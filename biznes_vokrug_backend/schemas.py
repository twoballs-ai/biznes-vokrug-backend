from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    name: Optional[str]  # Имя может быть необязательным
    email: str  # Обязательное поле
    phone: Optional[str]  # Необязательное
    password: str  # Обязательное

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
class IndividualEntrepreneurCreate(BaseModel):
    inn: str = Field(..., min_length=10, max_length=12, description="ИНН должен содержать 10 или 12 цифр")
    name: Optional[str] = None
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
    email: Optional[str] = None
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
    email: Optional[str] = None
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
    email: Optional[str] = None
    is_verified: bool
    rating: Optional[float] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None

    class Config:
        orm_mode = True


class IndividualEntrepreneurUpdate(BaseModel):
    name: Optional[str] = None
    inn: Optional[str] = None
    ogrnip: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class IndividualEntrepreneurResponse(BaseModel):
    name: Optional[str] = None
    id: int
    inn: str
    ogrnip: str
    phone: Optional[str] = None
    owner_id: int

    class Config:
        orm_mode = True


class ServiceCreate(BaseModel):
    name: str = Field(..., title="Название услуги", max_length=255)
    description: Optional[str] = Field(None, title="Описание услуги", max_length=500)
    price: Optional[float] = Field(None, title="Цена услуги")
    organization_id: Optional[int] = Field(None, title="ID организации, к которой привязана услуга")
    individual_entrepreneur_id: Optional[int] = Field(None, title="ID ИП, к которому привязана услуга")


class ServiceResponse(ServiceCreate):
    id: int = Field(..., title="ID услуги")
    created_at: Optional[str] = Field(None, title="Дата создания")
    updated_at: Optional[str] = Field(None, title="Дата последнего обновления")

    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    name: str = Field(..., title="Название продукта", max_length=255)
    description: Optional[str] = Field(None, title="Описание продукта", max_length=500)
    price: Optional[float] = Field(None, title="Цена продукта")
    organization_id: Optional[int] = Field(None, title="ID организации, к которой привязан продукт")
    individual_entrepreneur_id: Optional[int] = Field(None, title="ID ИП, к которому привязан продукт")

class ProductResponse(ProductCreate):
    id: int = Field(..., title="ID продукта")
    created_at: Optional[str] = Field(None, title="Дата создания")
    updated_at: Optional[str] = Field(None, title="Дата последнего обновления")

    class Config:
        orm_mode = True
