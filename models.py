# models.py
from enum import Enum
import json
from typing import List, Dict, Any, Optional, Union
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
    description: str
    type: str
    interactionId: str
    evaluable: bool

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

### Models for the Whatsapp API. IL for interactive List 
class IL_TextandType(BaseModel):
    type: Optional[str]
    text: str

class IL_TextSingle(BaseModel):
    text: str

class IL_Row(BaseModel):
    id: str
    title: str
    description: str

class IL_Section(BaseModel):
    title: str
    rows: List[IL_Row]

class IL_Action(BaseModel):
    button: str
    sections: List[IL_Section]

class IL_Interactive(BaseModel):
    type: str
    header: IL_TextandType
    body: IL_TextSingle
    footer: IL_TextSingle
    action: IL_Action

class IL_ListMessage(BaseModel):
    interactive: IL_Interactive

### Models for the Whatsapp API. MM for Media Message
class MM_Type(Enum):
    AUDIO = "audio"
    DOCUMENT = "document"
    IMAGE = "image"
    STICKER = "sticker"
    VIDEO = "video"
    
class MM_MediaMessage(BaseModel):
    type: MM_Type
    link: HttpUrl

### Models for the Whatsapp API. TM for Template Message


class TM_Component(BaseModel):
    type: str
    parameters: List[Dict[str, Any]]
    sub_type: Optional[str] = None
    index: Optional[str] = None
    class Config:
        exclude_none = True

class TM_Language(BaseModel):
    policy: Optional[str] = None
    code: str
    class Config:
        exclude_none = True

class TM_Template(BaseModel):
    namespace: Optional[str]  = None
    name: str
    language: TM_Language
    components: List[TM_Component]

class TM_TemplateMessage(BaseModel):
    type: str
    template: TM_Template
