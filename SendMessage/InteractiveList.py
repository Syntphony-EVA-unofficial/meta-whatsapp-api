

import logging
from pydantic import BaseModel, ValidationError
from typing import Literal, List, Optional


### Models for the Whatsapp API. IL for interactive List 
class IL_TextandType(BaseModel):
    type: Optional[str]
    text: str

class IL_TextSingle(BaseModel):
    text: str

class IL_Row(BaseModel):
    id: str
    title: str
    description: str

class IL_Section(BaseModel):
    title: str
    rows: List[IL_Row]

class IL_Action(BaseModel):
    button: str
    sections: List[IL_Section]

class IL_Interactive(BaseModel):
    type: Literal["list"]
    header: IL_TextandType
    body: IL_TextSingle
    footer: IL_TextSingle
    action: IL_Action

class IL_ListMessage(BaseModel):
    interactive: IL_Interactive

jsondata = None
class InteractiveListMessage:
    @staticmethod
    def validate(answer):
        try:
            InteractiveListMessage.jsondata = IL_ListMessage.model_validate(answer.technicalText)
            return True
        except ValidationError as e:      
            logging.info(f"Checking, message is not InteractiveListMessage")
        return False

    @staticmethod
    def create(answer, data):
        data["type"] = "interactive"
        data["interactive"] = InteractiveListMessage.jsondata.interactive.model_dump()
        return data




# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-list-messages
# {
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "to": "<WHATSAPP_USER_PHONE_NUMBER>",
#   "type": "interactive",
#   "interactive": {
#     "type": "list",
#     "header": {
#       "type": "text",
#       "text": "<MESSAGE_HEADER_TEXT"
#     },
#     "body": {
#       "text": "<MESSAGE_BODY_TEXT>"
#     },
#     "footer": {
#       "text": "<MESSAGE_FOOTER_TEXT>"
#     },
#     "action": {
#       "sections": [
#         {
#           "title": "<SECTION_TITLE_TEXT>",
#           "rows": [
#             {
#               "id": "<ROW_ID>",
#               "title": "<ROW_TITLE_TEXT>",
#               "description": "<ROW_DESCRIPTION_TEXT>"
#             }
#             /* Additional rows would go here*/
#           ]
#         }
#         /* Additional sections would go here */
#       ],
#       "button": "<BUTTON_TEXT>",
#     }
#   }
# }