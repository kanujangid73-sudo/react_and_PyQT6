from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class InquiryCreate(BaseModel):
    name: str
    email: EmailStr
    number: str
    company: str
    subject: str
    msg: str
    purpose: str

class InquiryResponse(InquiryCreate):
    id: int
    status: str
    created_at: datetime
    data: str
    time: str

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str