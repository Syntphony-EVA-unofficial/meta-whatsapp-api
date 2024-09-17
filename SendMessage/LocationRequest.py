import logging
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from typing import Literal, Optional


class LocationRequestModel(BaseModel):
    type: Literal["location_request_message"]
    text: str

jsondata = None
class LocationRequestMessage:
    @staticmethod    
    def validate(answer):
        try:
            LocationRequestMessage.jsondata = LocationRequestModel.model_validate(answer.technicalText)
            return True
        except ValidationError as e:      
            logging.info(f"Checking, message is not LocationRequestMessage")
        return False

    @staticmethod            
    def create(answer, data):
        data["type"] = "interactive"
        data["interactive"] ={
            "type": "location_request_message",
            "body": {
                "text": LocationRequestMessage.jsondata.text
                    },
                "action": {
                    "name": "send_location"
                }
            }
        return data

# https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages/location-request-messages
# {
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "type": "interactive",
#   "to": "<WHATSAPP_USER_PHONE_NUMBER>",
#   "interactive": {
#     "type": "location_request_message",
#     "body": {
#       "text": "<BODY_TEXT>"
#     },
#     "action": {
#       "name": "send_location"
#     }
#   }
# }