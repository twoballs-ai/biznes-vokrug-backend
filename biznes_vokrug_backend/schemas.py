from typing import Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl

class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str]
    hashed_password: str


class IndividualEntrepreneurCreate(BaseModel):
    inn: str
    ogrnip: str
    phone: Optional[str]


class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str]
    address: Optional[str]
    inn: Optional[str]
    ogrn: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    email: Optional[str]
    category: Optional[str]
    is_verified: bool
    rating: Optional[float]
    logo_url: Optional[str]
    city: Optional[str]

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    category: Optional[str] = None
    is_verified: Optional[bool] = None
    rating: Optional[float] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    category: Optional[str] = None
    is_verified: bool
    rating: Optional[float] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None

    class Config:
        orm_mode = True
