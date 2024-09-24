import logging
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from typing import Literal, Optional

class VideoModel(BaseModel):
    type: Literal["video"]
    link: HttpUrl


jsondata = None
class VideoMessage:
    @staticmethod    
    def validate(answer):
        try:
            VideoMessage.jsondata = VideoModel.model_validate(answer.technicalText)
            return True
        except ValidationError as e:      
            logging.info(f"Checking, message is not VideoMessage")
        return False

    @staticmethod            
    def create(answer, data):
        data["type"] = "video"
        data["video"] = {}
        data["video"]["link"] =str(VideoMessage.jsondata.link)
        if answer.content is not None and answer.content != " ":
            data["video"]["caption"] = answer.content
        return data


# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/video-messages
# {
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "to": "{{wa-user-phone-number}}",
#   "type": "video",
#   "video": {
#     "id" : "<MEDIA_ID>", /* Only if using uploaded media */
#     "link": "<MEDIA_URL>", /* Only if linking to your media */
#     "caption": "<VIDEO_CAPTION_TEXT>"
#   }
# }
