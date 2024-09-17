# models.py
from enum import Enum
import json
from typing import Literal, List, Dict, Any, Optional, Union
from pydantic import BaseModel, HttpUrl, field_validator
from typing import List


### Models for the Whatsapp webhook 
class Profile(BaseModel):
    name: str

class Contact(BaseModel):
    profile: Profile
    wa_id: str


class Metadata(BaseModel):
    display_phone_number: str
    phone_number_id: str

class Value(BaseModel):
    messaging_product: str
    metadata: Metadata
    contacts: List[Contact]
    messages: List[Dict[str, Any]]

class Change(BaseModel):
    value: Value
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class WebhookData(BaseModel):
    object: str
    entry: List[Entry]

### EVA response models
class NlpResponse(BaseModel):
    type: str
    name: str
    score: float
    entities: List[dict]

class Answer(BaseModel):
    content: str
    technicalText: Optional[Union[Dict, str]]
    buttons: List[dict]
    quickReply: List[dict]
    description: Optional[str]  # Allow null values
    type: str
    interactionId: str
    evaluable: bool
    masked: Optional[bool]  # Add the masked field


    @field_validator('technicalText')
    def parse_technical_text(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

class ResponseModel(BaseModel):
    text: Optional[str]
    sessionCode: str
    userInteractionUUID: str
    userInput: Optional[dict]
    nlpResponse: NlpResponse
    answers: List[Answer]
    context: dict
    contextReadOnly: dict



