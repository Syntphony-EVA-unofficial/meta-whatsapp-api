
from fastapi import APIRouter, Form, HTTPException
import logging

from pydantic import BaseModel
from models import Admin_FormData
from sessionHandler import session


router = APIRouter()

@router.post("/admin/form")
async def form_adminpost(
    organization_name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    facebook_access_token: str = Form(...), 
    facebook_app_id: str = Form(...), 
    facebook_app_secret: str = Form(...), 
    facebook_verify_token: str = Form(...), 
    facebook_phone_id: str = Form(...), 
    keycloak: str = Form(...), 
    organization_id: str = Form(...), 
    environment_id: str = Form(...), 
    api_key: str = Form(...),
    instance: str = Form(...), 
    bot_id: str = Form(...), 
    channel_id: str = Form(...)
):
    form_data = {
        "ORGANIZATION_NAME": organization_name,
        "EMAIL": email,
        "PASSWORD": password,
        "FACEBOOK_ACCESS_TOKEN": facebook_access_token,
        "FACEBOOK_APP_ID": facebook_app_id,
        "FACEBOOK_APP_SECRET": facebook_app_secret,
        "FACEBOOK_VERIFY_TOKEN": facebook_verify_token,
        "FACEBOOK_PHONE_ID": facebook_phone_id,
        "KEYCLOAK": keycloak,
        "ORGANIZATION_ID": organization_id,
        "ENVIRONMENT_ID": environment_id,
        "API_KEY": api_key,
        "INSTANCE": instance,
        "BOT_ID": bot_id,
        "CHANNEL_ID": channel_id
    }
    for field, value in form_data.items():
        if value == '':
            raise HTTPException(status_code=400, detail=f"{field} is required")

    token, error = await session.GeneratePasswordToken(form_data['EMAIL'], form_data['PASSWORD'], form_data['KEYCLOAK'], form_data['ORGANIZATION_NAME']) 
    logging.info(f"Token: {token}")
    if error:
        # handle the error
        raise HTTPException(status_code=400, detail=error)
    else:
        # use the token, credtentails are correct and can access that bot
        logging.info("token for insert config valid")
        # send this to database
        error = await insertConfig(form_data)
        if (error):    
            raise HTTPException(status_code=400, detail="Error inserting config data {error}")

    
    # If all fields are filled, return a success message
    return {"status_code": 200, "message": "Form submitted successfully"}

async def insertConfig(form_data: Admin_FormData):
    try:
        logging.info("IN Inserting config data")
        session.config_variables.update_one(
            {"FACEBOOK_PHONE_ID": form_data["FACEBOOK_PHONE_ID"]},
            {"$set": form_data},
            upsert=True
        )
        logging.info("OUT Inserting config data")
        return None
    except Exception as e:
        return str(e)
    