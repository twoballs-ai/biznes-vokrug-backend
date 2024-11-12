from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from biznes_vokrug_backend.utils.redis_dadata import get_address_suggestions
from . import crud, schemas
from .database import SessionLocal, get_db
from .minio import delete_object, download_file, upload_image
import urllib.parse
from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import Owner, Organization
from .schemas import UserCreate, OrganizationCreate, OrganizationUpdate, OrganizationResponse
from passlib.context import CryptContext
router = APIRouter()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Регистрация пользователя
@router.post("/register", response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = Owner(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "User registered successfully"}

# Создание новой организации
@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(org: OrganizationCreate, user_id: int, db: Session = Depends(get_db)):
    db_org = Organization(**org.dict(), owner_id=user_id)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

# Получение списка организаций
@router.get("/organizations", response_model=List[OrganizationResponse])
async def get_organizations(db: Session = Depends(get_db)):
    return db.query(Organization).all()

# Получение информации об организации
@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: int, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

# Обновление информации об организации
@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(org_id: int, org: OrganizationUpdate, db: Session = Depends(get_db)):
    db_org = db.query(Organization).filter(Organization.id == org_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")

    for key, value in org.dict(exclude_unset=True).items():
        setattr(db_org, key, value)

    db.commit()
    db.refresh(db_org)
    return db_org

# Удаление организации
@router.delete("/organizations/{org_id}")
async def delete_organization(org_id: int, db: Session = Depends(get_db)):
    db_org = db.query(Organization).filter(Organization.id == org_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")

    db.delete(db_org)
    db.commit()
    return {"msg": "Organization deleted successfully"}

@router.get("/suggest/address")
async def suggest_address(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    suggestions = get_address_suggestions(query)
    if not suggestions:
        raise HTTPException(status_code=404, detail="No suggestions found")

    return {"suggestions": suggestions}