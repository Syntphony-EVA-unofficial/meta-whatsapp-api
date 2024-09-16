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