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