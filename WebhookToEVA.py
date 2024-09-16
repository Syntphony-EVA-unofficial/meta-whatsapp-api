
import json
import logging
from collections import namedtuple

from AudioSTT import AudioSTT
EVARequestTuple = namedtuple('EVARequestTuple', ['content', 'context'])

class WebhookToEVA:
    
    
    
    @staticmethod
    async def handle_text(message):
        logging.info("Handling text message")
        EVA_content = message["text"]["body"]
        EVA_context = None
        return EVARequestTuple(EVA_content, EVA_context)     

    # @staticmethod
    # def handle_image():
    #     print("Handling image message")
        # Add your handling code here
    
    @staticmethod
    async def handle_interactive(message):
        subtype = message["interactive"]["type"]
        if subtype == "button_reply":
            logging.info("Handling interactive button message")
            EVA_content = message["interactive"]["button_reply"]["id"]
            EVA_context = None
            return EVARequestTuple(EVA_content, EVA_context)
        elif subtype == "list_reply":
            logging.info("Handling interactive list message")
            EVA_content = message["interactive"]["list_reply"]["id"]
            EVA_context = None
            return EVARequestTuple(EVA_content, EVA_context)
        else:
            logging.warning(f"Interactive message subtype not supported: {subtype}")
            return None

    @staticmethod
    async def handle_audio(message):
        logging.info("Handling audio message")
        audioID = message["audio"]["id"] 
        audioURL = await AudioSTT.getAudioURL(audioID)
        if (audioURL):
            downloadAudio = await AudioSTT.getDownloadAudio(audioURL)
            if (downloadAudio):
                logging.info(f"Audio message downloaded successfully")
                if isinstance(downloadAudio, bytes):
                    logging.info(f"The size of the binary data is {len(downloadAudio)} bytes")
                    STT_Result =  await AudioSTT.transcribe_file_v2("seu-whatsapp-api",downloadAudio)
                    if STT_Result:
                        EVA_content = STT_Result
                        EVA_context = None
                        return EVARequestTuple(EVA_content, EVA_context)
        logging.warning("Audio message could not be processed")
        return None
            
    @staticmethod
    def handle_location(message):
        print("Handling location message")
        EVA_content = " "
        EVA_context = {
            
            "location": {
                "latitude": message["location"]["latitude"],
                "longitude": message["location"]["longitude"]
            }
        }   
        return EVARequestTuple(EVA_content, EVA_context)     


    type_handlers = {
        "text": handle_text,
        #"image": handle_image,
        "interactive": handle_interactive,
        "audio": handle_audio,
        "location": handle_location,
    }

    @staticmethod
    async def convert(webhookData) -> EVARequestTuple:
        type = webhookData.entry[0].changes[0].value.messages[0]['type']
        # Call the appropriate handler function based on the type
        handler = WebhookToEVA.type_handlers.get(type)
        if handler:
            message = webhookData.entry[0].changes[0].value.messages[0]
            return await handler(message)
        else:
            logging.warning(f"Message type not supported: {type}")
            logging.info(f"Message data: {json.dumps(message, indent=4)}")
            return None


#Payload reference
#https://developers.facebook.com/docs/whatsapp/webhooks/

# region Sample payload Text
# {
#     "object": "whatsapp_business_account",
#     "entry": [
#         {
#             "id": "396803506838931",
#             "changes": [
#                 {
#                     "value": {
#                         "messaging_product": "whatsapp",
#                         "metadata": {
#                             "display_phone_number": "443300270175",
#                             "phone_number_id": "377135318814227"
#                         },
#                         "contacts": [
#                             {
#                                 "profile": {
#                                     "name": "Jorge Alviarez"
#                                 },
#                                 "wa_id": "819046050746"
#                             }
#                         ],
#                         "messages": [
#                             {
#                                 "from": "819046050746",
#                                 "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAEhgWM0VCMDEwOEIyMjcxRTU2OEMzMEZDMgA=",
#                                 "timestamp": "1726505663",
#                                 "text": {
#                                     "body": "text"
#                                 },
#                                 "type": "text"
#                             }
#                         ]
#                     },
#                     "field": "messages"
#                 }
#             ]
#         }
#     ]
# }
# endregion

# region Sample payload Image
# {
#     "object": "whatsapp_business_account",
#     "entry": [
#         {
#             "id": "396803506838931",
#             "changes": [
#                 {
#                     "value": {
#                         "messaging_product": "whatsapp",
#                         "metadata": {
#                             "display_phone_number": "443300270175",
#                             "phone_number_id": "377135318814227"
#                         },
#                         "contacts": [
#                             {
#                                 "profile": {
#                                     "name": "Jorge Alviarez"
#                                 },
#                                 "wa_id": "819046050746"
#                             }
#                         ],
#                         "messages": [
#                             {
#                                 "from": "819046050746",
#                                 "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAEhggOTE4RjQwRDVBREY0OTY1MUM5REU4MUZFMEYwNEJERUMA",
#                                 "timestamp": "1726505863",
#                                 "type": "image",
#                                 "image": {
#                                     "mime_type": "image/jpeg",
#                                     "sha256": "XI5zVScjPljtTOamVAfjuFJDXI4CIJjQjpiZAjjsXlI=",
#                                     "id": "1519915665311104"
#                                 }
#                             }
#                         ]
#                     },
#                     "field": "messages"
#                 }
#             ]
#         }
#     ]
# }
# endregion 

# region Sample payload Audio
# {
#     "object": "whatsapp_business_account",
#     "entry": [
#         {
#             "id": "396803506838931",
#             "changes": [
#                 {
#                     "value": {
#                         "messaging_product": "whatsapp",
#                         "metadata": {
#                             "display_phone_number": "443300270175",
#                             "phone_number_id": "377135318814227"
#                         },
#                         "contacts": [
#                             {
#                                 "profile": {
#                                     "name": "Jorge Alviarez"
#                                 },
#                                 "wa_id": "819046050746"
#                             }
#                         ],
#                         "messages": [
#                             {
#                                 "from": "819046050746",
#                                 "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAEhggQ0VERjBFNDk2M0RGNEZCQkRFNzEzRTc2RkU5MjFFNjIA",
#                                 "timestamp": "1726506047",
#                                 "type": "audio",
#                                 "audio": {
#                                     "mime_type": "audio/ogg; codecs=opus",
#                                     "sha256": "UVX8nD2Obr8xOSBWzvjaaELN5zcfJiDFl/1/mTAvvl4=",
#                                     "id": "888403122625223",
#                                     "voice": true
#                                 }
#                             }
#                         ]
#                     },
#                     "field": "messages"
#                 }
#             ]
#         }
#     ]
# }
# endregion

# region Sample payload Document
# {
#     "object": "whatsapp_business_account",
#     "entry": [
#         {
#             "id": "396803506838931",
#             "changes": [
#                 {
#                     "value": {
#                         "messaging_product": "whatsapp",
#                         "metadata": {
#                             "display_phone_number": "443300270175",
#                             "phone_number_id": "377135318814227"
#                         },
#                         "contacts": [
#                             {
#                                 "profile": {
#                                     "name": "Jorge Alviarez"
#                                 },
#                                 "wa_id": "819046050746"
#                             }
#                         ],
#                         "messages": [
#                             {
#                                 "from": "819046050746",
#                                 "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAEhggNzFFQUI5QkMxNjEzQTNCRkEzMjk3QTQ1RjMzRjhGNDcA",
#                                 "timestamp": "1726506116",
#                                 "type": "document",
#                                 "document": {
#                                     "filename": "1. PRESENTACION SUE\u00d1A MARIN..pdf",
#                                     "mime_type": "application/pdf",
#                                     "sha256": "pp8c2xMjXu3x0pMvljAzP11z96p9/+OdftnP1EfkTj0=",
#                                     "id": "8095888260519062"
#                                 }
#                             }
#                         ]
#                     },
#                     "field": "messages"
#                 }
#             ]
#         }
#     ]
# }
# endregion

# region Sample payload Location
# {
#     "object": "whatsapp_business_account",
#     "entry": [
#         {
#             "id": "396803506838931",
#             "changes": [
#                 {
#                     "value": {
#                         "messaging_product": "whatsapp",
#                         "metadata": {
#                             "display_phone_number": "443300270175",
#                             "phone_number_id": "377135318814227"
#                         },
#                         "contacts": [
#                             {
#                                 "profile": {
#                                     "name": "Jorge Alviarez"
#                                 },
#                                 "wa_id": "819046050746"
#                             }
#                         ],
#                         "messages": [
#                             {
#                                 "from": "819046050746",
#                                 "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAEhggQjIzQTEyMEFGODIxNDdFNDFDMDUwOTBGMEJGOUJCN0UA",
#                                 "timestamp": "1726506199",
#                                 "location": {
#                                     "latitude": 35.6589903,
#                                     "longitude": 139.7959751
#                                 },
#                                 "type": "location"
#                             }
#                         ]
#                     },
#                     "field": "messages"
#                 }
#             ]
#         }
#     ]
# }
# endregion

# region Sample payload Interactive List Reply
# {
#     "object": "whatsapp_business_account",
#     "entry": [
#         {
#             "id": "396803506838931",
#             "changes": [
#                 {
#                     "value": {
#                         "messaging_product": "whatsapp",
#                         "metadata": {
#                             "display_phone_number": "443300270175",
#                             "phone_number_id": "377135318814227"
#                         },
#                         "contacts": [
#                             {
#                                 "profile": {
#                                     "name": "Jorge Alviarez"
#                                 },
#                                 "wa_id": "819046050746"
#                             }
#                         ],
#                         "messages": [
#                             {
#                                 "context": {
#                                     "from": "443300270175",
#                                     "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAERgSMkVEMDI2OEI2QzQ5RDM2NUIxAA=="
#                                 },
#                                 "from": "819046050746",
#                                 "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAEhggNzc3OENBOTMyRTdGMzI3MzI4OThDQkQyQzgzRTI0OTkA",
#                                 "timestamp": "1726506263",
#                                 "type": "interactive",
#                                 "interactive": {
#                                     "type": "list_reply",
#                                     "list_reply": {
#                                         "id": "SECTION_1_ROW_2_ID",
#                                         "title": "SECTION_1_ROW_2_TITLE",
#                                         "description": "SECTION_1_ROW_2_DESCRIPTION"
#                                     }
#                                 }
#                             }
#                         ]
#                     },
#                     "field": "messages"
#                 }
#             ]
#         }
#     ]
# }
# endregion

#region Sample payload Interactive Button Reply
# {
#     "context": {
#         "from": "443300270175",
#         "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAERgSMjFEMEY2MTE0RDMxMURBNEZDAA=="
#     },
#     "from": "819046050746",
#     "id": "wamid.HBgMODE5MDQ2MDUwNzQ2FQIAEhggMDk0REUzNzkxN0NFNDRBMzMwODM2RUUyOTgwMUVCMjUA",
#     "timestamp": "1726506605",
#     "type": "interactive",
#     "interactive": {
#         "type": "button_reply",
#         "button_reply": {
#             "id": "value2",
#             "title": "ButtonName2"
#         }
#     }
# }
#endregion




