import logging
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from typing import Literal, Optional


class LocationModel(BaseModel):
    latitude: float
    longitude: float
    name: str
    address: str

class LocationMessageModel(BaseModel):
    type: Literal["location"]
    location: LocationModel

jsondata = None
class LocationMessage:
    @staticmethod    
    def validate(answer):
        try:
            LocationMessage.jsondata = LocationMessageModel.model_validate(answer.technicalText)
            return True
        except ValidationError as e:      
            logging.info(f"Checking, message is not LocationMessage")
        return False

    @staticmethod            
    def create(answer, data):
        data["type"] = "location"
        data["location"] = {
            "latitude": LocationMessage.jsondata.location.latitude,
            "longitude": LocationMessage.jsondata.location.longitude,
            "name": LocationMessage.jsondata.location.name,
            "address": LocationMessage.jsondata.location.address
            }   
        return data


# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/location-messages
# {
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "to": "<WHATSAPP_USER_PHONE_NUMBER>",
#   "type": "location",
#   "location": {
#     "latitude": "<LOCATION_LATITUDE>",
#     "longitude": "<LOCATION_LONGITUDE>",
#     "name": "<LOCATION_NAME>",
#     "address": "<LOCATION_ADDRESS>"
#   }
# }