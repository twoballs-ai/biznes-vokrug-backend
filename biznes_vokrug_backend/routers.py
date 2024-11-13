from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from biznes_vokrug_backend.auth import create_access_token, create_refresh_token, verify_password, verify_token
from biznes_vokrug_backend.crud import get_user_by_email
from biznes_vokrug_backend.utils.redis_dadata import get_address_suggestions
from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import os
from fastapi import Header, Cookie
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import Owner, Organization
from .schemas import UserCreate, OrganizationCreate, OrganizationUpdate, OrganizationResponse
from passlib.context import CryptContext
import os
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    response: Response = None
):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="Lax",
        secure=True
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        samesite="Lax",
        secure=True
    )

    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out"}

@router.post("/refresh")
def refresh_token_endpoint(
    refresh_token: str = Cookie(None),
    response: Response = None
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is missing")

    payload = verify_token(refresh_token)
    user_id: str = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    new_access_token = create_access_token({"sub": user_id})
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="Lax",
        secure=True
    )

    return {"message": "Token refreshed"}

# Регистрация пользователя
@router.post("/register", response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = Owner(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "User registered successfully"}

@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(org_data: OrganizationCreate, db: Session = Depends(get_db)):
    new_org = Organization(**org_data.dict())
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

@router.get("/organizations/{id}", response_model=OrganizationResponse)
def get_organization(id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return org

@router.put("/organizations/{id}", response_model=OrganizationResponse)
def update_organization(id: int, org_data: OrganizationUpdate, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    for key, value in org_data.dict(exclude_unset=True).items():
        setattr(org, key, value)

    db.commit()
    db.refresh(org)
    return org

@router.delete("/organizations/{id}", response_model=OrganizationResponse)
def delete_organization(id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    
    db.delete(org)
    db.commit()
    return org

@router.get("/suggest/address")
async def suggest_address(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    suggestions = get_address_suggestions(query)
    if not suggestions:
        raise HTTPException(status_code=404, detail="No suggestions found")

    return {"suggestions": suggestions}