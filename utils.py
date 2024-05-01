import os
import hmac
import hashlib
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
import logging

def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == os.getenv("FACEBOOK_VERIFY_TOKEN"):
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return {"content": str(challenge), "media_type": "text/plain", "status_code": status.HTTP_200_OK}

        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        raise HTTPException(status_code=400, detail="Missing parameters")

def validate_signature(payload: str, signature: str) -> bool:
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(os.getenv("FACEBOOK_APP_SECRET"), "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)

async def signature_required(request: Request, call_next):
    signature = request.headers.get("X-Hub-Signature-256", "")[7:]  # Removing 'sha256='
    body = await request.body()
    if not validate_signature(body.decode("utf-8"), signature):
        logging.info("Signature verification failed!")
        raise HTTPException(status_code=403, detail="Invalid signature")
    else: 
        logging.info("Signature verification passed!")
    return await call_next(request)

