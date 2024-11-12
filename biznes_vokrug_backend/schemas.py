from typing import Optional
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str]
    address: Optional[str]

class OrganizationUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    address: Optional[str]

class OrganizationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: Optional[str]

    class Config:
        orm_mode = True