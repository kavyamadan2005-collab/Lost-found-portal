from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# Auth
class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# Items
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    date_reported: Optional[date] = None


class ItemCreate(ItemBase):
    type: str


class ItemOut(ItemBase):
    id: int
    type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ItemImageOut(BaseModel):
    id: int
    image_url: str

    class Config:
        orm_mode = True


class ItemDetail(ItemOut):
    images: List[ItemImageOut] = []


class MatchResult(BaseModel):
    item_id: int
    score: float
