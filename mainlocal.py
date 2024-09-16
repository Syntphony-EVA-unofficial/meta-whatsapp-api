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
from models import IL_ListMessage, ResponseModel, WebhookData, Answer, MM_MediaMessage, TM_TemplateMessage, LM_LocationRequestMessage, LM_LocationMessageFromEva
from utilslocal import signature_required, verify
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

import aiohttp
import aiofiles
logging.basicConfig(level=logging.INFO)
from sessionHandlerlocal import session
from WebhookToEVA import WebhookToEVA, EVARequestTuple

load_dotenv('variables.env')
app = FastAPI()


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

@app.get("/test")
def test_endpoint():
    return {"message": "This is a test endpoint"}

@app.post("/webhook")
async def handle_incoming_user_message(request: Request):

    if not await session.validate_webhook():
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
            EVA_Request = await WebhookToEVA.convert(webhook_data)
            
            logging.info(f"Webhook incoming data: {json.dumps(data, indent=4)}")
            
            
            if EVA_Request:
                session.UserID = webhook_data.entry[0].changes[0].value.messages[0]["from"]
                session.fromPhone = webhook_data.entry[0].changes[0].value.messages[0]["from"]
                #use to load values from cache and generate a new token if needed
                await session.get_session()
                
                
                await send_message_to_eva(EVA_Request)
                await session.saveSession()
                return {"status": "ok"}
            else:
                logging.warning(f"Data to send to EVA is empty")
                return {"status": "ok"}
            
        
        except ValidationError:
            #message must be status read,sent,delivered
            try:
                status = data['entry'][0]['changes'][0]['value']['statuses'][0]['status']
                logging.info(f'message status: {status}')
            except:
                logging.warning(f"Received unexpected data: {data}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")
   

async def send_message_to_eva(EVA_Request: EVARequestTuple):

    logging.info(f"Sending message to evaBroker (TIME) {datetime.now(timezone.utc)}")
    instance = session.getenv('EVA_INSTANCE')  
    orgUUID = session.getenv('EVA_ORG_UUID')
    envUUID = session.getenv('EVA_ENV_UUID')
    botUUID = session.getenv('EVA_BOT_UUID')
    channelUUID = session.getenv('EVA_CHANNEL_UUID')
    api_key = session.getenv('EVA_APIKEY')  # replace with your API key

    url = f"https://{instance}/eva-broker/org/{orgUUID}/env/{envUUID}/bot/{botUUID}/channel/{channelUUID}/v1/conversations"
    if session.evaSessionCode:
        url += f"/{session.evaSessionCode}"

    headers = {
        'Content-Type': 'application/json',
        'API-KEY': api_key,
        'OS': 'Windows',
        'USER-REF': session.UserID,
        'LOCALE': 'en-US',
        'Authorization': f'Bearer {session.evaToken}'
    }


    # Check if context is present and construct the JSON accordingly
    if EVA_Request.context is not None:
        data = json.dumps({
            "text": EVA_Request.content,
            "context": EVA_Request.context
        })
    else:
        data = json.dumps({
            "text": EVA_Request.content
        })

    logging.info(f"Sending message to EVA: {json.dumps(json.loads(data), indent=4)}")
    
    async with httpx.AsyncClient() as client:
        max_retries = 2
        for attempt in range(max_retries):
            headers['Authorization'] = f'Bearer {session.evaToken}'
            response = await client.post(url, headers=headers, data=data)
    
            if response.status_code != 401:
                session.evaSessionCode = response.json().get('sessionCode')
                break

            session.evaToken, error = await session.GenerateToken()
            if error:
                logging.error(f"Failed to generate token: {error}")
                return
    
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
            try:
                instanceLocationMessage = LM_LocationRequestMessage.model_validate(answer.technicalText)
                model_found = True
                logging.info(f"LocationRequest message detected")
                data["type"] = "INTERACTIVE"
                data["interactive"] ={
                    "type": "location_request_message",
                    "body": {
                        "text": instanceLocationMessage.text
                        },
                    "action": {
                        "name": "send_location"
                        }
                }
                
            except ValidationError as e:
                logging.error(f"Message is not LM_LocationRequestMessage: {e}")
                logging.info(f"Technical text: {json.dumps(answer.technicalText, indent=4)}")    
        
        if not model_found:
            try:
                instanceLocation = LM_LocationMessageFromEva.model_validate(answer.technicalText)
                model_found = True
                logging.info(f"Location message detected")
                data["type"] = "location"
                data["location"] = {
                        "latitude": instanceLocation.location.latitude,
                        "longitude": instanceLocation.location.longitude,
                        "name": instanceLocation.location.name,
                        "address": instanceLocation.location.address
                }   
            except ValidationError as e:
                logging.error(f"Message is not LM_LocationMessageFromEva: {e}")
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
    uvicorn.run("mainlocal:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True, log_level="debug")


 


