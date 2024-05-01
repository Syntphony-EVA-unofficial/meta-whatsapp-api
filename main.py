import json
import logging
import os
import time
from fastapi import FastAPI, Request, requests, HTTPException
import uvicorn
from dotenv import load_dotenv
from starlette.responses import Response
from models import IL_ListMessage, ResponseModel, WebhookData, Answer, MM_MediaMessage, TM_TemplateMessage
from utils import signature_required, verify
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import urllib
import httpx
import urllib.parse
from fastapi import HTTPException
import pytz
from pydantic import ValidationError


load_dotenv('variables.env')

logging.basicConfig(level=logging.DEBUG)
logging.info("Starting the application")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")

app = FastAPI()


#Verify the webhook from WhatsApp API configuration, this is only needed once
@app.get("/webhook")
async def verify_webhook(request: Request):
    response = verify(request)
    return Response(content=response["content"], media_type=response["media_type"], status_code=response["status_code"])

#This singature is to be sure that the request is coming from WhatsApp API
@app.middleware("http")
async def middleware(request: Request, call_next):
    return await signature_required(request, call_next)


@app.post("/webhook")
async def handle_incoming_user_message(request: Request):
    try:
        data = await request.json()
        #print(json.dumps(data, indent=4))
        try:
            webhook_data = WebhookData(**data)
            for entry in webhook_data.entry:
                for change in entry.changes:
                    for message in change.value.messages:
                        if message["type"] == "text":
                            await HandleTextMessage(message)
                        elif message["type"] == "image":
                            await HandleImageMessage(message)
                        elif message["type"] == "interactive":
                            await HandleInteractivePressed(message)
                        else:
                            logging.warning(f"Message type not supported: {message['type']}")
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




async def HandleInteractivePressed(message):
    # Add your code to handle the interactive message here  
    #logging.info(f"Data of interactive: {json.dumps(data, indent=4)}")  # Add this line
    
    
    logging.info("Handling interactive message")
    interactive_message = json.dumps(message, indent=4)
    logging.info(f"Data of interactive: {interactive_message}")  # Corrected line
    
    evaSesionCode, evaToken = await find_session(message["from"])
    
    if (message["interactive"]["type"] == "button_reply"):
        valueToEva = message["interactive"]["button_reply"]["id"]
    elif (message["interactive"]["type"] == "list_reply"):
        valueToEva = message["interactive"]["list_reply"]["id"]

    if evaToken is None:
        evaToken= await GenerateToken()
        logging.info(f"Token has been generated")
    
    await send_message_to_eva(evaSesionCode, evaToken,  valueToEva, message["from"])     

    return   



async def HandleImageMessage(message):
    # Add your code to handle the text message here
    pass

async def HandleTextMessage(message):

    logging.info("Handling text message")
    evaSesionCode, evaToken = await find_session(message["from"])
    
    if evaToken is None:
        evaToken= await GenerateToken()
        logging.info(f"Token has been generated")
    
    await send_message_to_eva(evaSesionCode, evaToken,  message["text"]["body"], message["from"])     

    return   


async def send_message_to_eva(session_code, access_token, user_message, user_id):
    logging.info(f"Sending message to evaBroker (TIME) {datetime.now(timezone.utc)}")
    instance = os.getenv('EVA_INSTANCE')  
    orgUUID = os.getenv('EVA_ORG_UUID')
    envUUID = os.getenv('EVA_ENV_UUID')
    botUUID = os.getenv('EVA_BOT_UUID')
    channelUUID = os.getenv('EVA_CHANNEL_UUID')
    api_key = os.getenv('EVA_APIKEY')  # replace with your API key

    url = f"https://{instance}/eva-broker/org/{orgUUID}/env/{envUUID}/bot/{botUUID}/channel/{channelUUID}/v1/conversations"
    if session_code is not None:
        url += f"/{session_code}"
    headers = {
        'Content-Type': 'application/json',
        'API-KEY': api_key,
        'OS': 'Windows',
        'USER-REF': user_id,
        'LOCALE': 'en-US',
        'Authorization': f'Bearer {access_token}'
    }
    data = json.dumps({
        "text": user_message
    })
    logging.info(f"Message to eva config from {session_code}: {user_message} at {datetime.now(timezone.utc)}")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data)

    try:
        response_data = response.json()
        instanceEvaResponse = ResponseModel.model_validate(response_data)
        logging.info(f"Match to eva response")

    except ValidationError as e:
        logging.error(f"EvaMessage do not fit the model ResponseModel: {e}") 
        print(json.dumps(response_data, indent=4))
        return



    logging.info(f"Respuesta evaBroker (TIME) {datetime.now(timezone.utc)}")
    answers = instanceEvaResponse.answers
    eva_session = instanceEvaResponse.sessionCode

    logging.info("Print all answers:")

    for answer in answers:
        headers, data = prepare_message(answer, user_id)
        response = send_message_whatsapp(headers, data)
    
        # Check the response status
        if response.status_code != 200:
            logging.error(f"Failed to send message: {response.text}")
            break
        # Wait for 1 second before sending the next message
        time.sleep(1)

    # Update the records with the new session code and access token
    whatsapp_users.update_one(
        {"userUniqueID": user_id},
        {"$set": {"evaSessionCode": eva_session, "evaToken": access_token, "timestamp": datetime.now(timezone.utc)}},
        upsert=True
        )

def prepare_message(answer: Answer, user_id):
    logging.info(f"Preparing message for WhatsApp API")
    headers = {
        'Authorization': f"Bearer {os.getenv('FACEBOOK_ACCESS_TOKEN')}",
        'Content-Type': 'application/json',
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": user_id
    }

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
                data["template"]["namespace"] = os.getenv("FACEBOOK_TEMPLATE_NAMESPACE")
                
            except ValidationError as e:
                logging.error(f"Message is not TM_TemplateMessage: {e}")    


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
        response = client.post(f"https://graph.facebook.com/v18.0/{os.getenv('FACEBOOK_PHONE_ID')}/messages", headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            logging.error(f"Response status: {response.status_code}")
            logging.error(f"Response headers: {response.headers}")
            logging.error(f"Response body: {response.text}")
        response.raise_for_status()
        return response

async def GenerateToken():
    logging.info("Enter to function Token Gen TIME: %s", datetime.now(timezone.utc))
    data = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv('EVA_CLIENT_ID'),
        'client_secret': os.getenv('EVA_SECRET'),
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    url = f"{os.getenv('EVA_KEYCLOAK')}/auth/realms/{os.getenv('EVA_ORGANIZATION')}/protocol/openid-connect/token"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, data=urllib.parse.urlencode(data))
            response.raise_for_status()
            token = response.json().get('access_token')
            logging.info(f"token expiration: {response.json().get('expires_in')}")
            return token
        except httpx.HTTPError as error:
            logging.error("HTTPError  generating Access Token: %s", str(error))
        except Exception as error:
            logging.error("Error generating Access Token: %s", str(error))

 
# MongoDB

logging.info(f"MongoDB URI: {os.getenv('MONGO_URI')}, Database: {os.getenv('MONGO_DB')}")

uri = f"{os.getenv('MONGO_URI')}?retryWrites=true&w=majority"
logging.info(f"Connecting to MongoDB: {uri}")

client = MongoClient(uri)
db = client[os.getenv("MONGO_DB")]
whatsapp_users = db['whatsapp_users']

async def find_session(userID: str):
    logging.info("Enter finding user TIME: %s", datetime.now(timezone.utc))
    try:
        evasession_code = None
        eva_token = None

        query = {
            "userUniqueID": userID,
        }
        found_user = whatsapp_users.find_one(query)
        
        if found_user is not None:
            logging.info("Found User Result: %s", found_user["userUniqueID"])
            timestamp = found_user["timestamp"]
            timestamp = timestamp.replace(tzinfo=pytz.UTC)

            if datetime.now(timezone.utc) - timestamp <= timedelta(seconds=1800):  # session code expiry time
                evasession_code = found_user["evaSessionCode"]
            if datetime.now(timezone.utc) - timestamp <= timedelta(seconds=900):  # token expiry time
                eva_token = found_user["evaToken"]
            if evasession_code is None and eva_token is None:
                delete_query = {"userUniqueID": userID}
                whatsapp_users.delete_many(delete_query)
            logging.info("evaSessionCode: %s, evaToken: %s", str(evasession_code)[:10] if evasession_code else None, str(eva_token)[:10] if eva_token else None)        
            return evasession_code, eva_token
    except Exception as error:
        logging.error("Error finding user: %s", error)
    #this line Return a default value when found_user is None or an exception is raised
    return None, None  