# API RERFERENCE
# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/contacts-messages
# {
#   "messaging_product": "whatsapp",
#   "to": "<WHATSAPP_USER_PHONE_NUMBER>",
#   "type": "contacts",
#   "contacts": [
#     {
#       "addresses": [
#         {
#           "street": "<STREET_NUMBER_AND_NAME>",
#           "city": "<CITY>",
#           "state": "<STATE_CODE>",
#           "zip": "<ZIP_CODE>",
#           "country": "<COUNTRY_NAME>",
#           "country_code": "<COUNTRY_CODE>",
#           "type": "<ADDRESS_TYPE>"
#         }
#         /* Additional addresses objects go here, if using */
#       ],
#       "birthday": "<BIRTHDAY>",
#       "emails": [
#         {
#           "email": "<EMAIL_ADDRESS>",
#           "type": "<EMAIL_TYPE>"
#         }
#         */ Additional emails objects go here, if using */
#       ],
#       "name": {
#         "formatted_name": "<FULL_NAME>",
#         "first_name": "<FIRST_NAME>",
#         "last_name": "<LAST_NAME>",
#         "middle_name": "<MIDDLE_NAME>",
#         "suffix": "<SUFFIX>",
#         "prefix": "<PREFIX>"
#       },
#       "org": {
#         "company": "<COMPANY_OR_ORG_NAME>",
#         "department": "<DEPARTMENT_NAME>",
#         "title": "<JOB_TITLE>"
#       },
#       "phones": [
#         {
#           "phone": "<PHONE_NUMBER>",
#           "type": "<PHONE_NUMBER_TYPE>",
#           "wa_id": "<WHATSAPP_USER_ID>"
#         }
#         /* Additional phones objects go here, if using */
#       ],
#       "urls": [
#         {
#           "url": "<WEBSITE_URL>",
#           "type": "<WEBSITE_TYPE>"
#         },
#         /* Additional URLs go here, if using */
#       ]
#     }
#   ]
# }