

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
dbClient = client[os.getenv("MONGO_DB")]
whatsapp_users = dbClient['whatsapp_users']



class Session:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state
        self.evaSessionCode = None
        self.evaToken = None
        self.UserID = None
        self.fromPhone = None
        self.config_variables = dbClient['config_variables']
        self.loaded_variables = None
        


    async def getSession(self):
        logging.info("Enter to function Get Session TIME: %s", datetime.now(timezone.utc))
        if self.evaSessionCode is not None and self.evaToken is not None:
            logging.info("Session already exists")
            return self.evaSessionCode, self.evaToken
        else:
            logging.info("Session None, go finding user...")
            self.evaSessionCode, self.evaToken = await self.findSession(session.UserID)


        
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
        try:
           
            query = {
                "userUniqueID": userID,
            }
            found_user = whatsapp_users.find_one(query)
            
            if found_user is not None:
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

    async def GeneratePasswordToken(self, email , password, keycloak, organization):
        logging.info("Enter to function Password Token Gen TIME: %s", datetime.now(timezone.utc))
        data = {
            'grant_type': 'password',
            'client_id': 'eva-cockpit',
            'username': email,
            'password': password
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        url = f"{keycloak}/auth/realms/{organization}/protocol/openid-connect/token"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, data=urllib.parse.urlencode(data))
                response.raise_for_status()
                token = response.json().get('access_token')
                return token, None
            except httpx.HTTPError as error:
                logging.error("HTTPError Error Generating Access Token: %s", str(error))
                return None, str(error)

            except Exception as error:
                logging.error("Error Generating Access Token: %s", str(error))
                return None, str(error)

    

    async def GenerateToken(self):
        
        logging.info("Enter to function Token Gen TIME: %s", datetime.now(timezone.utc))
        token, error = await self.GeneratePasswordToken(
            self.getenv('EMAIL'),
            self.getenv('PASSWORD'),
            self.getenv('KEYCLOAK'),
            self.getenv('ORGANIZATION_NAME')
        )
        if not error:
            return token
        else:
            logging.error(f"Error generating token: {error}")
            return None
        
      
    async def GenerateSessionCode(self):
        logging.info("Enter to function Session Code Gen TIME: %s", datetime.now(timezone.utc))
        instance = self.getenv('INSTANCE')  
        orgUUID = self.getenv('ORGANIZATION_ID')
        envUUID = self.getenv('ENVIRONMENT_ID')
        botUUID = self.getenv('BOT_ID')
        channelUUID = self.getenv('CHANNEL_ID')
        api_key = self.getenv('API_KEY')  # replace with your API key

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
        
        #logging.info("url to generate session code: %s", url)
        #logging.info("headers to generate session code: %s", headers)
        #logging.info("data to generate session code: %s", data) 
        #logging.info("token to generate session code: %s", self.evaToken)




        logging.info(f"Welcome Message to eva config from {self.UserID} at {datetime.now(timezone.utc)}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)

        try:
            logging.info(f"Response from Eva: {response.json()}")
            response_data = response.json()
            instanceEvaResponse = ResponseModel.model_validate(response_data)
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
    
    def check_record(self, botid, phoneid):
        logging.info("Enter to function Check Record TIME: %s", datetime.now(timezone.utc))
        query = {
            "BOT_ID": botid,
            "FACEBOOK_PHONE_ID": phoneid
        }
        found_user = self.config_variables.find_one(query)
        if found_user is not None:
            return found_user["FACEBOOK_VERIFY_TOKEN"]
        else:
            return None
    
    async def load_config(self, botid: str, phoneid: str):
        if self.loaded_variables is None:
            try:
                logging.info("Getting config data from database")
                self.loaded_variables = self.config_variables.find_one({"BOT_ID": botid, "FACEBOOK_PHONE_ID": phoneid})
                return True                
            except Exception as e:
                logging.error(f"Error getting config data: {e}")
                return False
        return True
    
    def getenv(self, key: str):
        if self.loaded_variables is not None:
            return self.loaded_variables.get(key)
        else:
            return None
                
#defining the sessioncode and sessiontoken as none
session = Session()
