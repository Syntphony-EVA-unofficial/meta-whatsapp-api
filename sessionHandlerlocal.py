

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
load_dotenv('localvariables.env')


class Session:
    session_cache = {}


    def __init__(self):
        self.evaSessionCode = None
        self.evaToken = None
        self.UserID = None
        self.fromPhone = None
        
        


    async def getSession(self):
        logging.info("Enter to function Get Session TIME: %s", datetime.now(timezone.utc))
        if (session.userID in self.session_cache) and ("evaTokenTimestamp" in self.session_cache[self.UserID]) and ("evaToken" in self.session_cache[self.UserID]):
            timestamp = self.session_cache[session.userID]["evaTokenTimestamp"]
            timestamp = timestamp.replace(tzinfo=pytz.UTC)
    
        if self.evaToken is None or datetime.now(timezone.utc) - timestamp > timedelta(seconds=900):  # token expiry time
            self.evaToken, error = await self.GenerateToken()
            if error:
                logging.error(f"Error generating token: {error}")
                return None, None
            
            logging.info(f"Token has been generated {str(self.evaToken)[:10]}")
            await self.updateTokenTimestamp()
        
       
        return self.evaSessionCode, self.evaToken


    async def updateTokenTimestamp(self):
        try:
            if self.UserID in self.session_cache:
                self.session_cache[self.UserID]['evaTokenTimestamp'] = datetime.now(timezone.utc)
                self.session_cache[self.UserID]['evaToken'] = self.evaToken
                logging.info("Updated token timestamp for UserID: %s", self.UserID)
            else:
                logging.warning("UserID: %s not found in cache", self.UserID)
        except Exception as error:
            logging.error("Error updating token timestamp: %s", error)


    async def GenerateToken(self):
        logging.info("Enter to function Password Token Gen TIME: %s", datetime.now(timezone.utc))
        data = {
            'grant_type': 'client_credentials',
            'client_id': session.getenv('EVA_CLIENT_ID'),
            'client_secret': session.getenv('EVA_SECRET')
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        url = f"{session.getenv("EVA_KEYCLOAK")}/auth/realms/{session.getenv("EVA_ORG_UUID")}/protocol/openid-connect/token"
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
        token, error = await self.GenerateToken(
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
    
   
    
    async def validate_webhook(self, botid: str, phoneid: str):
        try:
            env_botid = os.getenv('EVA_BOT_UUID')
            env_phoneid = os.getenv('FACEBOOK_PHONE_ID')
            
            if botid == env_botid and phoneid == env_phoneid:
                logging.info("webhook validated")
                return True
            else:
                logging.error("BOT_ID or FACEBOOK_PHONE_ID does not match environment variables")
                return False
        except Exception as e:
            logging.error(f"Error getting config data: {e}")
            return False

    def getenv(self, key: str):
        if key in os.environ:
            return os.getenv(key)
        raise ValueError(f"Environment variable {key} not found")
                
#defining the sessioncode and sessiontoken as none
session = Session()
