from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Response, Body
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from biznes_vokrug_backend.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_password,
    verify_token
)
from biznes_vokrug_backend.crud import get_user_by_email
from biznes_vokrug_backend.utils.redis_dadata import get_address_suggestions
from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pydantic import BaseModel
from .database import get_db
from .models import IndividualEntrepreneur, User, Organization
from .schemas import (
    IndividualEntrepreneurCreate,
    UserCreate,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверные учетные данные")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@router.post("/logout")
def logout():
    # Если вы не храните токены на сервере, просто возвращайте сообщение
    return {"message": "Вы вышли из системы"}

@router.post("/refresh")
def refresh_token_endpoint(
    refresh_token: str = Body(...),
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Токен обновления отсутствует")

    try:
        payload = verify_token(refresh_token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Неверный токен")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        new_access_token = create_access_token({"sub": user_id})
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Неверный токен")

@router.post("/register/")
async def register_user(
    user: UserCreate = Body(...),  # Данные пользователя
    add_organization: bool = Body(False),  # Флаг добавления организации
    add_individual_entrepreneur: bool = Body(False),  # Флаг добавления ИП
    org_data: Optional[OrganizationCreate] = None,
    ie_data: Optional[IndividualEntrepreneurCreate] = None,
    db: Session = Depends(get_db)
):
    print("add_organization:", add_organization)
    print("add_individual_entrepreneur:", add_individual_entrepreneur)

    # Проверяем, существует ли пользователь с таким email
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        return JSONResponse(
            content={"status": False, "message": "Пользователь уже существует"},
            status_code=200,
        )

    # Хэшируем пароль пользователя
    hashed_password = pwd_context.hash(user.password)
    
    # Создание пользователя
    new_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(add_organization)
    # Если пользователь выбрал организацию
    if add_organization:
        if not org_data:
            raise HTTPException(status_code=400, detail="Необходимо указать данные организации.")
        new_organization = Organization(
            name=org_data.name,
            description=org_data.description,
            address=org_data.address,
            inn=org_data.inn,
            ogrn=org_data.ogrn,
            phone=org_data.phone,
            website=org_data.website,
            email=org_data.email,
            category=org_data.category,
            is_verified=org_data.is_verified,
            rating=org_data.rating,
            logo_url=org_data.logo_url,
            city=org_data.city,
            owner_id=new_user.id,
            updated_at=datetime.utcnow() 
        )
        db.add(new_organization)
        db.commit()
        db.refresh(new_organization)

    # Если пользователь выбрал ИП
    if add_individual_entrepreneur:
        if not ie_data:
            raise HTTPException(status_code=400, detail="Необходимо указать данные ИП.")
        new_entrepreneur = IndividualEntrepreneur(
            inn=ie_data.inn,
            ogrnip=ie_data.ogrnip,
            phone=ie_data.phone,
            owner_id=new_user.id
        )
        db.add(new_entrepreneur)
        db.commit()
        db.refresh(new_entrepreneur)
    
    return JSONResponse(
        content={"status": True,"message": "Пользователь успешно создан"},
        status_code=200,
    )

# Следующие эндпоинты теперь используют get_current_user для проверки аутентификации
@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_org = Organization(**org_data.dict(), owner_id=current_user.id)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

@router.get("/organizations/{id}", response_model=OrganizationResponse)
def get_organization(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return org

@router.put("/organizations/{id}", response_model=OrganizationResponse)
def update_organization(
    id: int,
    org_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    # Проверяем, является ли текущий пользователь владельцем
    if org.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не авторизованы для обновления этой организации")

    for key, value in org_data.dict(exclude_unset=True).items():
        setattr(org, key, value)

    db.commit()
    db.refresh(org)
    return org

@router.delete("/organizations/{id}", response_model=OrganizationResponse)
def delete_organization(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    # Проверяем, является ли текущий пользователь владельцем
    if org.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не авторизованы для удаления этой организации")
    
    db.delete(org)
    db.commit()
    return org

@router.get("/suggest/address")
async def suggest_address(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not query:
        raise HTTPException(status_code=400, detail="Требуется параметр запроса")

    suggestions = get_address_suggestions(query)
    if not suggestions:
        raise HTTPException(status_code=404, detail="Предложения не найдены")

    return {"suggestions": suggestions}
