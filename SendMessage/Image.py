import json
import logging
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator
from typing import Literal, Optional



class ImageModel(BaseModel):

    type: Literal["image"]
    link: HttpUrl




class ImageMessage:
    jsondata: Optional[ImageModel] = None

    @staticmethod    
    def validate(answer):
        try:
            ImageMessage.jsondata = ImageModel.model_validate(answer.technicalText)
            return True
        except ValidationError as e:      
            logging.info(f"Validation error: {e}")
        return False

    @staticmethod            
    def create(answer, data):
        data["type"] = "image"
        data["image"] = {}
        data["image"]["link"] = str(ImageMessage.jsondata.link)
        if answer.content is not None and answer.content != " ":
            data["image"]["caption"] = answer.content

        return data





# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/image-messages
# {
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "to": "<WHATSAPP_USER_PHONE_NUMBER>",
#   "type": "image",
#   "image": {
#     "id" : "<MEDIA_ID>", /* Only if using uploaded media */
#     "link": "<MEDIA_URL>", /* Only if linking to your media */
#     "caption": "<IMAGE_CAPTION_TEXT>"
#   }
# }
