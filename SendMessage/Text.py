
class TextMessage:
    @staticmethod
    def validate(answer):
        True

    @staticmethod
    def create(data, answer):
        data["type"]="text"
        data["text"] = {
            "preview_url": True,
            "body": answer.content
        }
        return data


# https://developers.facebook.com/docs/whatsapp/cloud-api/messages/text-messages
# {
#   "messaging_product": "whatsapp",
#   "recipient_type": "individual",
#   "to": "<WHATSAPP_USER_PHONE_NUMBER>",
#   "type": "text",
#   "text": {
#     "preview_url": <ENABLE_LINK_PREVIEW>,
#     "body": "<BODY_TEXT>"
#   }
# }