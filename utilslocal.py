import os
import logging
import hmac
import json
import traceback

import hashlib
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from dotenv import load_dotenv
from sessionHandlerlocal import session

load_dotenv('variables.env')

def verify(request: Request):
    verifyToken = None

    logging.info("Verifying webhook")
    request_dict = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "client": str(request.client)
    }
    logging.info(json.dumps(request_dict, indent=4))
    params = request.query_params
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")
    botid= params.get("botid")
    phoneid = params.get("phoneid")

    
    #check if bot and numberid are present in database
    if session.validate_webhook(botid, phoneid) :
        verifyToken = session.getenv("FACEBOOK_VERIFY_TOKEN")
    else:    
        raise HTTPException(status_code=403, detail="Bot and numberid are not present in database")
    if (verifyToken is None):
        raise HTTPException(status_code=403, detail="Bot and numberid are not present in database")     

    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == verifyToken:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return {"content": str(challenge), "media_type": "text/plain", "status_code": status.HTTP_200_OK}

        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("FACEBOOK_VERIFY_TOKEN MISSING_PARAMETER")
        raise HTTPException(status_code=400, detail="Missing parameters")

def validate_signature(payload: str, signature: str) -> bool:
    """
    Validate the incoming payload's signature against our expected signature
    """ 
    # Use the App Secret to hash the payload 
    expected_signature = hmac.new(
        bytes(session.getenv("FACEBOOK_APP_SECRET"), "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)

async def signature_required(request: Request):
    signature = request.headers.get("X-Hub-Signature-256", "")[7:]  # Removing 'sha256='
    body = await request.body()
    if not validate_signature(body.decode("utf-8"), signature):
        logging.info("Signature verification failed!")
        raise HTTPException(status_code=403, detail="Invalid signature")
    else: 
        logging.info("Signature verification passed!")

