# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/address-messages
# curl -X  POST \
# 'https://graph.facebook.com/v15.0/FROM_PHONE_NUMBER_ID/messages' \
# -H 'Authorization: Bearer ACCESS_TOKEN' \
# -H 'Content-Type: application/json' \
# -d '{
#           "messaging_product": "whatsapp",
#           "recipient_type": "individual",
#           "to": "PHONE_NUMBER",
#           "type": "interactive",
#           "interactive": {
#               "type": "address_message",
#               "body": {
#                    "text": "Thanks for your order! Tell us what address you’d like this order delivered to."
#               },
#               "action": {
#                    "name": "address_message",
#                    "parameters": {
#                       "country" :"COUNTRY_ISO_CODE"
#                    }
#               }
#           }
#     }' 

