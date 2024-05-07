import logging
import json
import os
import time
import traceback
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from dotenv import load_dotenv
from starlette.responses import Response
from models import IL_ListMessage, ResponseModel, WebhookData, Answer, MM_MediaMessage, TM_TemplateMessage
from utils import signature_required, verify
from datetime import datetime, timedelta, timezone
import urllib
import httpx
import urllib.parse
from fastapi import HTTPException
import pytz
from pydantic import ValidationError
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.oauth2 import service_account
from admin.admin import router as admin_router

import aiohttp
import aiofiles
logging.basicConfig(level=logging.INFO)


from sessionHandler import session
 
load_dotenv('variables.env')



app = FastAPI()
app.include_router(admin_router)

app.mount("/admin", StaticFiles(directory="admin"), name="admin")
templates = Jinja2Templates(directory="admin")

    


#Verify the webhook from WhatsApp API configuration, this is only needed once
@app.get("/webhook")
async def verify_webhook(request: Request):
    try:
        logging.info("Verifying webhook")
        response = verify(request)
        return Response(content=response["content"], media_type=response["media_type"], status_code=response["status_code"])
    except HTTPException as e:
        logging.error(f"HTTP error occurred: {e.detail}")
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        logging.error(f"An error1 occurred: {e}")
        logging.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred"})


@app.get("/admin", response_class=HTMLResponse)
async def admin_form(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/test")
def test_endpoint():
    return {"message": "This is a test endpoint"}

@app.post("/webhook")
async def handle_incoming_user_message(request: Request, botid: str, phoneid: str):

    if not await session.load_config(botid, phoneid):
        logging.error("Failed to load config data")
        raise HTTPException(status_code=500, detail="Failed to load config data")

    try:   
        #This singature is to be sure that the request is coming from WhatsApp API
        await signature_required(request)
    except Exception as e:
        logging.error(f"An error2 occurred: {e}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:

        data = await request.json()
        updateRecord = False
        #print(json.dumps(data, indent=4))
        try:
            webhook_data = WebhookData(**data)
            for entry in webhook_data.entry:
                for change in entry.changes:
                    for message in change.value.messages:
                        userId = f'{message["from"]}&{phoneid}'
                        logging.info(f"composed User ID: {userId}")
                        session.UserID = userId
                        session.fromPhone = message["from"]
                        if message["type"] == "text":
                            await HandleTextMessage(message)
                            updateRecord = True
                        elif message["type"] == "image":
                            await HandleImageMessage(message)
                            updateRecord = True
                        elif message["type"] == "interactive":
                            await HandleInteractivePressed(message)
                            updateRecord = True
                        elif message["type"] == "audio":    
                            await HandleAudioMessage(message)
                            #updateRecord = True

                        else:
                            logging.warning(f"Message type not supported: {message['type']}")
            if updateRecord:
                await session.updateTime()
            return {"status": "ok"}
        except ValidationError:
            #message must be status read,sent,delivered
            try:
                status = data['entry'][0]['changes'][0]['value']['statuses'][0]['status']
                logging.info(f'message status: {status}')
            except:
                logging.warning(f"Received unexpected data: {data}")

    except Exception as e:
        logging.error(f"An error3 occurred: {e}")
        raise HTTPException(status_code=500, detail="An error3 occurred while processing the request.")


async def HandleAudioMessage(message):
    # Add your code to handle the text message here
    audioID = message["audio"]["id"] 
    audioURL = await getAudioURL(audioID)
    if (audioURL):
        downloadAudio = await getDownloadAudio(audioURL)
        if (downloadAudio):
            logging.info(f"Audio message downloaded successfully")
            if isinstance(downloadAudio, bytes):
                logging.info(f"The size of the binary data is {len(downloadAudio)} bytes")
                STT_Result = transcribe_file_v2("seu-whatsapp-api",downloadAudio)
                if STT_Result:
                    evaSessionCode, evaToken = await session.getSession()
                    await send_message_to_eva(STT_Result)
                    return    
            else:
                logging.info("The downloadAudio data is not in binary format")
                return



def transcribe_file_v2(  project_id: str, audio_data: bytes,) -> cloud_speech.RecognizeResponse:
    # Instantiates a client
    credentials = service_account.Credentials.from_service_account_file('key.json')
    client = SpeechClient(credentials=credentials)

    # Reads a file as bytes
    content = audio_data
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US", "es-ES", "fr-FR"],
        model="long",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/global/recognizers/_",
        config=config,
        content=content,
    )

    logging.info(f"Transcribing audio file")
    # Transcribes the audio into text
    try:
        response = client.recognize(request=request)
        logging.info(f"Transcriptionw all results: {response.results}")
        return response.results[0].alternatives[0].transcript
    
    except Exception as e:
        logging.error(f"An error4 occurred in Transcribe: {e}")
        return None

async def getDownloadAudio(audioURL):    
    
    # Define the headers
    headers = {
        'Authorization': f'Bearer {session.getenv("FACEBOOK_ACCESS_TOKEN")}'
    }
    
    try:
        # Download the audio file
        async with httpx.AsyncClient() as client:
            audio_response = await client.get(audioURL, headers=headers)

        # Store the audio data in a variable
        audio_data = audio_response.content
        return audio_data

    except httpx.HTTPStatusError as exc:
        print(f"An HTTP error occurred: {exc}")
        return None
    except httpx.NetworkError:
        print("A network error occurred.")
        return None
    except httpx.TimeoutException:
        print("The request timed out.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None
        

async def getAudioURL(audioID):
    logging.info(f"Data of AudioMessage: {audioID}")  # Corrected line
    #get audio message

    # Define the endpoint
    url = f"https://graph.facebook.com/v19.0/{audioID}"

    # Define the headers
    headers = {
        'Authorization': f'Bearer {session.getenv("FACEBOOK_ACCESS_TOKEN")}'
    }

    logging.info(f"Trying to get audio message from {url}")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    try:
        response_data = response.json()
        logging.info(f"data Response {response_data}")
        logging.info(json.dumps(response_data, indent=4))
        return response_data["url"] 

    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response")
        return None
    except KeyError:
        logging.error("The key 'url' was not found in the response data")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None


async def HandleInteractivePressed(message):
    # Add your code to handle the interactive message here  
    #logging.info(f"Data of interactive: {json.dumps(data, indent=4)}")  # Add this line
    
    
    logging.info("Handling interactive message")
    interactive_message = json.dumps(message, indent=4)
    logging.info(f"Data of interactive: {interactive_message}")  # Corrected line
    
    evaSessionCode, evaToken = await session.getSession()
    
    
    if (message["interactive"]["type"] == "button_reply"):
        valueToEva = message["interactive"]["button_reply"]["id"]
    elif (message["interactive"]["type"] == "list_reply"):
        valueToEva = message["interactive"]["list_reply"]["id"]

    
    await send_message_to_eva(valueToEva)     

    return   


async def HandleImageMessage(message):
    # Add your code to handle the text message here
    pass

async def HandleTextMessage(message):

    logging.info("Handling text message")
    evaSessionCode, evaToken = await session.getSession()

    
    await send_message_to_eva(message["text"]["body"])     

    return   


async def send_message_to_eva( user_message):
    logging.info(f"Sending message to evaBroker (TIME) {datetime.now(timezone.utc)}")
    instance = session.getenv('INSTANCE')  
    orgUUID = session.getenv('ORGANIZATION_ID')
    envUUID = session.getenv('ENVIRONMENT_ID')
    botUUID = session.getenv('BOT_ID')
    channelUUID = session.getenv('CHANNEL_ID')
    api_key = session.getenv('API_KEY')  # replace with your API key

    url = f"https://{instance}/eva-broker/org/{orgUUID}/env/{envUUID}/bot/{botUUID}/channel/{channelUUID}/v1/conversations/{ session.evaSessionCode }"

    headers = {
        'Content-Type': 'application/json',
        'API-KEY': api_key,
        'OS': 'Windows',
        'USER-REF': session.UserID,
        'LOCALE': 'en-US',
        'Authorization': f'Bearer {session.evaToken}'
    }
    data = json.dumps({
        "text": user_message
    })
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data)
    
        if response.status_code == 401:
            newToken = await session.RenewToken()
            headers['Authorization'] = f'Bearer {newToken}'
            response = await client.post(url, headers=headers, data=data)

    
    try:
        response_data = response.json()
        #if 'error' in response_data:
        instanceEvaResponse = ResponseModel.model_validate(response_data)

    except ValidationError as e:
        logging.error(f"EvaMessage do not fit the model ResponseModel: {e}") 
        print(json.dumps(response_data, indent=4))
        return

    answers = instanceEvaResponse.answers

    for answer in answers:
        headers, data = prepare_message(answer, session.fromPhone)
        response = send_message_whatsapp(headers, data)
        # Check the response status
        if response.status_code != 200:
            logging.error(f"Failed to send message: {response.text}")
            break
        # Wait for 1 second before sending the next message
        time.sleep(1)

def prepare_message(answer: Answer, user_id):
    logging.info(f"Preparing message for WhatsApp API")
    headers = {
        'Authorization': f"Bearer {session.getenv('FACEBOOK_ACCESS_TOKEN')}",
        'Content-Type': 'application/json',
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": user_id
    }

    #logging.info("data: " + json.dumps(data, indent=4))
    #logging.info("headers: " + json.dumps(headers, indent=4))    
    #logging.info("userid: " + user_id)

    # Determine the message type
    if answer.technicalText is None:
        if answer.buttons:
            logging.info("Buttons found -- mapping to interactive format")
            data["type"] = "interactive"
            data["interactive"] = {
                "type": "button",
                "body": {
                    "text": answer.content
                },
               "action": {
                    "buttons": generate_buttons(answer.buttons)
                }
            }
        else:
            logging.info("Technical text is None and no buttons -- defaulting to text")
            data["type"]="text"
            data["text"] = {
                "preview_url": True,
                "body": answer.content
            }

    if answer.technicalText is not None:
        model_found = False

        if not model_found:
            try:
                instanceListMessage = IL_ListMessage.model_validate(answer.technicalText)
                model_found = True
                logging.info(f"Interactive list message detected")
                data["type"] = "interactive"
                data["interactive"] = instanceListMessage.interactive.model_dump()
            except ValidationError as e:      
                logging.error(f"Message is not IL_ListMessage: {e}")
                logging.error(f"Technical text: {json.dumps(answer.technicalText)}")
        if not model_found:
            try:
                instanceMediaMessage = MM_MediaMessage.model_validate(answer.technicalText)
                model_found = True
                logging.info(f"Media message detected")
                data["type"] = instanceMediaMessage.type.value
                data[instanceMediaMessage.type.value] = {
                    "link": instanceMediaMessage.link.__str__()
                }
                if answer.content is not None:
                    data[instanceMediaMessage.type.value]["caption"] = answer.content
            except ValidationError as e:
                logging.error(f"Message is not MM_MediaMessage: {e}")
        if not model_found:
            try:
                instanceTemplateMessage = TM_TemplateMessage.model_validate(answer.technicalText)
                model_found = True
                logging.info(f"Template message detected")
                data["type"] = "template"
                data["template"] = instanceTemplateMessage.template.model_dump()
                #if "namespace" not in data["template"] or data["template"]["namespace"] is None:
                #    data["template"]["namespace"] = session.getenv("FACEBOOK_TEMPLATE_NAMESPACE")
                
            except ValidationError as e:
                logging.error(f"Message is not TM_TemplateMessage: {e}")
                logging.info(f"Technical text: {json.dumps(answer.technicalText, indent=4)}")    


        if not model_found:
            logging.warning(f"Technical text model not supported (defaulted to text)")
            data["type"]="text"
            data["text"] = {
                "preview_url": True,
                "body": answer.content
             }

    return headers, data

def generate_buttons(buttons):
    button_list = []
    for i, button in enumerate(buttons):
        if i >= 3:  # Limit to 3 buttons
            break
        button_list.append({
            "type": "reply",
            "reply": {
                "id": button['value'],
                "title": button['name']
            }
        })
    return button_list

def send_message_whatsapp(headers, data):
    logging.info(f"Sending message to WhatsApp API")
    logging.info(f"Data: {json.dumps(data, indent=4)}")  # Add this line
    
    with httpx.Client() as client:        
        response = client.post(f"https://graph.facebook.com/v18.0/{session.getenv('FACEBOOK_PHONE_ID')}/messages", headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            logging.error(f"Response status: {response.status_code}")
            logging.error(f"Response headers: {response.headers}")
            logging.error(f"Response body: {response.text}")
        response.raise_for_status()
        return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True, log_level="debug")


 


