
class InteractiveReplyButtonMessage:
    @staticmethod
    def validate(answer):
        if answer.buttons:
            return True

    @staticmethod
    def create(data, answer):
        data["type"] = "interactive"
        data["interactive"] = {
                "type": "button",
                "body": {
                    "text": answer.content
                },
                "action": {
                    "buttons": InteractiveReplyButtonMessage.generate_buttons(answer.buttons)
                }
            }
        return data

    @staticmethod
    def generate_buttons(buttons):
        button_list = []
        for i, button in enumerate(buttons):
            if i >= 3:  # Limit to 3 buttons
                break
            button_list.append({
                "type": "reply",
                "reply": {
                    "id": button['value'],
                    "title": button['name']
                }
            })
        return button_list
        

# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-reply-buttons-messages
# {
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "to": "<WHATSAPP_USER_PHONE_NUMBER>",
#   "type": "interactive",
#   "interactive": {
#     "type": "button",
#     "header": {<MESSAGE_HEADER>},
#     "body": {
#       "text": "<BODY_TEXT>"
#     },
#     "footer": {
#       "text": "<FOOTER_TEXT>"
#     },
#     "action": {
#       "buttons": [
#         {
#           "type": "reply",
#           "reply": {
#             "id": "<BUTTON_ID>",
#             "title": "<BUTTON_LABEL_TEXT>"
#           }
#         }
#       ]
#     }
#   }
# }