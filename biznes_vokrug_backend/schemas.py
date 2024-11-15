from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    hashed_password: str = Field(..., alias="password")


class IndividualEntrepreneurCreate(BaseModel):
    inn: str = Field(..., min_length=10, max_length=12, description="ИНН должен содержать 10 или 12 цифр")
    ogrnip: str = Field(..., min_length=15, max_length=15, description="ОГРНИП должен содержать 15 цифр")
    phone: Optional[str] = None


class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    inn: str = Field(..., min_length=10, max_length=10, description="ИНН организации должен содержать 10 цифр")
    ogrn: str = Field(..., min_length=13, max_length=13, description="ОГРН должен содержать 13 цифр")
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    category: Optional[str] = None
    is_verified: bool = False
    rating: Optional[float] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None

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
