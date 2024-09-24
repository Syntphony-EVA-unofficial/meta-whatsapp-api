import logging
from pydantic import BaseModel, ValidationError
from typing import Any, Dict, Literal, List, Optional


### Models for the Whatsapp API. TM for Template Message

class TM_Component(BaseModel):
    type: str
    parameters: List[Dict[str, Any]]
    sub_type: Optional[str] = None
    index: Optional[str] = None
    class Config:
        exclude_none = True

class TM_Language(BaseModel):
    policy: Optional[str] = None
    code: str
    class Config:
        exclude_none = True

class TM_Template(BaseModel):
    namespace: Optional[str]  = None
    name: str
    language: TM_Language
    components: List[TM_Component]

class TM_TemplateMessage(BaseModel):
    type: Literal["template"]
    template: TM_Template

jsondata = None
class TemplateMessage:
    @staticmethod
    def validate(answer):
        try:
            TemplateMessage.jsondata = TM_TemplateMessage.model_validate(answer.technicalText)
            return True
        except ValidationError as e:      
            logging.info(f"Checking, message is not TemplateMessage")
        return False

    @staticmethod
    def create(answer, data):
        data["type"] = "template"
        data["template"] = TemplateMessage.jsondata.template.model_dump()
        return data




# https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates
# curl -X  POST \
#  'https://graph.facebook.com/v20.0/FROM_PHONE_NUMBER_ID/messages' \
#  -H 'Authorization: Bearer ACCESS_TOKEN' \
#  -H 'Content-Type: application/json' \
#  -d '{
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "to": "PHONE_NUMBER",
#   "type": "template",
#   "template": {
#     "name": "TEMPLATE_NAME",
#     "language": {
#       "code": "LANGUAGE_AND_LOCALE_CODE"
#     },
#     "components": [
#       {
#         "type": "body",
#         "parameters": [
#           {
#             "type": "text",
#             "text": "text-string"
#           },
#           {
#             "type": "currency",
#             "currency": {
#               "fallback_value": "VALUE",
#               "code": "USD",
#               "amount_1000": NUMBER
#             }
#           },
#           {
#             "type": "date_time",
#             "date_time": {
#               "fallback_value": "DATE"
#             }
#           }
#         ]
#       }
#     ]
#   }
# }'
