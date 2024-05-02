

import logging
from datetime import datetime, timedelta, timezone
from models import IL_ListMessage, ResponseModel, WebhookData, Answer, MM_MediaMessage, TM_TemplateMessage
from pymongo import MongoClient
import os
import httpx
import urllib
import json
import pytz
from pydantic import ValidationError
from dotenv import load_dotenv

# MongoDB
load_dotenv('variables.env')


uri = f"{os.getenv('MONGO_URI')}?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client[os.getenv("MONGO_DB")]
whatsapp_users = db['whatsapp_users']

class Session:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state
        self.evaSessionCode = None
        self.evaToken = None
        self.UserID = None

    async def getSession(self, userID: str):
        logging.info("Enter to function Get Session TIME: %s", datetime.now(timezone.utc))
        if self.evaSessionCode is not None and self.evaToken is not None:
            logging.info("Session already exists")
            return self.evaSessionCode, self.evaToken
        else:
            logging.info("Session does not exist, go finding user...")
            self.evaSessionCode, self.evaToken = await self.findSession(userID)


        self.UserID = userID
        updateRecord = False
        if self.evaToken is None:
            self.evaToken= await self.GenerateToken()
            logging.info(f"Token has been generated {str(self.evaToken)[:10]}")
            updateRecord = True
        if self.evaSessionCode is None:
            self.evaSessionCode = await self.GenerateSessionCode()
            logging.info(f"Session Code has been generated {str(self.evaSessionCode)[:10]}")
            updateRecord = True
        if updateRecord:
            await self.saveSession(self.evaSessionCode, self.evaToken)
        return self.evaSessionCode, self.evaToken

    async def RenewToken(self):
        self.evaToken= await self.GenerateToken()
        logging.info(f"RenewToken has been generated {str(self.evaToken)[:10]}")
        await self.saveSession(self.evaSessionCode, self.evaToken)
        return self.evaToken

    async def updateTime(self):
        timestamp = await self.saveSession(self.evaSessionCode, self.evaToken)
        logging.info(f"Update Time of session values: {timestamp}")

    async def findSession(self, userID: str):
        logging.info("Enter finding user %s TIME: %s",userID, datetime.now(timezone.utc))
        try:
           
            query = {
                "userUniqueID": userID,
            }
            found_user = whatsapp_users.find_one(query)
            
            if found_user is not None:
                logging.info("Found User Result: %s", found_user["userUniqueID"])
                timestamp = found_user["timestamp"]
                timestamp = timestamp.replace(tzinfo=pytz.UTC)

                if datetime.now(timezone.utc) - timestamp <= timedelta(seconds=1800):  # session code expiry time
                    self.evaSessionCode = found_user["evaSessionCode"]
                if datetime.now(timezone.utc) - timestamp <= timedelta(seconds=900):  # token expiry time
                    self.evaToken = found_user["evaToken"]
                if self.evaSessionCode is None or self.evaToken is None:
                    delete_query = {"userUniqueID": self.UserID}
                    whatsapp_users.delete_many(delete_query)
                logging.info("Found UserInformation evaSessionCode: %s, evaToken: %s", str(self.evaSessionCode)[:10] if self.evaSessionCode else None, str(self.evaToken)[:10] if self.evaToken else None)        
                return self.evaSessionCode, self.evaToken
        except Exception as error:
            logging.error("Error finding user: %s", error)
        #this line Return a default value when found_user is None or an exception is raised
        return None, None  

    async def GenerateToken(self):
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

    async def GenerateSessionCode(self):
        logging.info("Enter to function Session Code Gen TIME: %s", datetime.now(timezone.utc))
        logging.info(f"Sending Welcome message to evaBroker")
        instance = os.getenv('EVA_INSTANCE')  
        orgUUID = os.getenv('EVA_ORG_UUID')
        envUUID = os.getenv('EVA_ENV_UUID')
        botUUID = os.getenv('EVA_BOT_UUID')
        channelUUID = os.getenv('EVA_CHANNEL_UUID')
        api_key = os.getenv('EVA_APIKEY')  # replace with your API key

        url = f"https://{instance}/eva-broker/org/{orgUUID}/env/{envUUID}/bot/{botUUID}/channel/{channelUUID}/v1/conversations"

        headers = {
            'Content-Type': 'application/json',
            'API-KEY': api_key,
            'OS': 'Windows',
            'USER-REF': self.UserID,
            'LOCALE': 'en-US',
            'Authorization': f'Bearer {self.evaToken}'
        }
        data = json.dumps({
            "code": "%EVA_WELCOME_MSG"
            })      
        
        logging.info(f"Welcome Message to eva config from {self.UserID} at {datetime.now(timezone.utc)}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)

        try:
            response_data = response.json()
            instanceEvaResponse = ResponseModel.model_validate(response_data)
            logging.info(f"Match to eva response")
            return instanceEvaResponse.sessionCode

        except ValidationError as e:
            logging.error(f"EvaMessage do not fit the model ResponseModel: {e}") 
            print(json.dumps(response_data, indent=4))
            return

    async def saveSession(self, evaSessionCode: str, evaToken: str):
        timestamp = datetime.now(timezone.utc)
        logging.info("Enter to function Save Session TIME: %s", timestamp)
        #logging.info(f"Eva Session Code: {self.evaSessionCode}, Eva Token: {self.evaToken}, User ID: {self.UserID}")        
        whatsapp_users.update_one(
            {"userUniqueID": self.UserID},
            {"$set": {"evaSessionCode": evaSessionCode, "evaToken": evaToken, "timestamp": timestamp}},
            upsert=True
            )
        return timestamp