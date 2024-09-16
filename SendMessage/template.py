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