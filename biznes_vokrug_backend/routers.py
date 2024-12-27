from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Response, Body
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload

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
from .models import IndividualEntrepreneur, Product, Service, User, Organization
from .schemas import (
    IndividualEntrepreneurCreate,
    IndividualEntrepreneurResponse,
    IndividualEntrepreneurUpdate,
    ProductCreate,
    ServiceCreate,
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

from fastapi import HTTPException, status

@router.post("/organizations/")
def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли организация с таким же ОГРН
    existing_org = db.query(Organization).filter(Organization.ogrn == org_data.ogrn).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Организация с таким ОГРН уже существует."
        )
    
    # Создаём новую организацию
    new_org = Organization(**org_data.model_dump(), owner_id=current_user.id)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return JSONResponse(
        content={"status": True, "data": new_org.to_dict(), "message": "Успешно добавлена"},
        status_code=status.HTTP_201_CREATED,
    )

@router.get("/organizations", response_model=list[dict])  # Указываем, что возвращаем список словарей
def get_all_organizations(limit: int | None = None, db: Session = Depends(get_db)):
    """
    Получить список организаций с возможным ограничением по количеству.
    
    Args:
        limit (int | None): Максимальное количество возвращаемых организаций. По умолчанию None (все организации).
        db (Session): Сессия базы данных.
    """
    # Если `limit` задан, применяем ограничение
    query = db.query(Organization)
    if limit:
        query = query.limit(limit)
    
    organizations = query.all()

    # Если организаций нет, возвращаем пустой список
    if not organizations:
        return JSONResponse(
            content={"status": True, "data": [], "message": "Организации не найдены"},
            status_code=200,
        )

    # Преобразуем объекты в словари (предполагается, что у модели есть метод `to_dict()`)
    orgs_list = [org.to_dict() for org in organizations]

    return JSONResponse(
        content={"status": True, "data": orgs_list, "message": "Успешно"},
        status_code=200,
    )


@router.get("/organizations/by_ogrn/{ogrn}")
def get_organization_by_ogrn(
    ogrn: str,
    db: Session = Depends(get_db),
):
    
    org = db.query(Organization).filter(Organization.ogrn == ogrn).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return JSONResponse(
        content={"status": True, "data": org.to_dict(), "message": "Успешно"},
        status_code=200,
    )



@router.get("/organization/{id}")
def get_organization_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    print("dd")
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return JSONResponse(
        content={"status": True, "data": org.to_dict(), "message": "Успешно"},
        status_code=200,
    )


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
    return JSONResponse(
        content={"status": True, "message": "Успешно удалено"},
        status_code=200,
    )

@router.get("/organizations/me")
def get_organizations_for_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    organizations = db.query(Organization).filter(Organization.owner_id == current_user.id).all()
    if not organizations:
        return JSONResponse(
            content={
                "status": False,
                "data": [],  # Возвращаем пустой массив
                "message": "Организации не найдены"
            },
            status_code=200,
        )

    return JSONResponse(
        content={
            "status": True,
            "data": [org.to_dict() for org in organizations],
            "message": "Успешно"
        },
        status_code=200,
    )


@router.get("/individual-entrepreneurs", response_model=list[dict])  # Указываем, что возвращаем список словарей
def get_all_individual_entrepreneurs(limit: int | None = None, db: Session = Depends(get_db)):
    """
    Получить список индивидуальных предпринимателей с возможным ограничением по количеству.
    
    Args:
        limit (int | None): Максимальное количество возвращаемых предпринимателей. По умолчанию None (все).
        db (Session): Сессия базы данных.
    """
    # Создаем запрос с возможным ограничением
    query = db.query(IndividualEntrepreneur)
    if limit:
        query = query.limit(limit)
    
    entrepreneurs = query.all()

    # Если предпринимателей нет, возвращаем пустой список
    if not entrepreneurs:
        return JSONResponse(
            content={"status": True, "data": [], "message": "Предприниматели не найдены"},
            status_code=200,
        )

    # Преобразуем объекты в словари
    entrepreneurs_list = [entrepreneur.to_dict() for entrepreneur in entrepreneurs]

    return JSONResponse(
        content={"status": True, "data": entrepreneurs_list, "message": "Успешно"},
        status_code=200,
    )

@router.post("/individual-entrepreneurs/")
def create_individual_entrepreneur(
    ie_data: IndividualEntrepreneurCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли ИП у текущего пользователя
    existing_ie_for_user = db.query(IndividualEntrepreneur).filter(IndividualEntrepreneur.owner_id == current_user.id).first()
    if existing_ie_for_user:
        return JSONResponse(
            content={
                "status": False,
                "message": "Вы уже зарегистрировали индивидуального предпринимателя."
            },
            status_code=400,
        )

    # Проверяем, существует ли предприниматель с таким же ОГРНИП
    existing_ie_by_ogrnip = db.query(IndividualEntrepreneur).filter(IndividualEntrepreneur.ogrnip == ie_data.ogrnip).first()
    if existing_ie_by_ogrnip:
        return JSONResponse(
            content={
                "status": False,
                "message": "Индивидуальный предприниматель с таким ОГРНИП уже существует."
            },
            status_code=400,
        )

    # Создаём нового индивидуального предпринимателя
    new_ie = IndividualEntrepreneur(**ie_data.model_dump(), owner_id=current_user.id)
    db.add(new_ie)
    db.commit()
    db.refresh(new_ie)

    return JSONResponse(
        content={
            "status": True,
            "data": new_ie.to_dict(),
            "message": "Индивидуальный предприниматель успешно добавлен."
        },
        status_code=201,
    )


@router.get("/individual-entrepreneurs/{id}")
def get_individual_entrepreneur_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    ie = db.query(IndividualEntrepreneur).filter(IndividualEntrepreneur.id == id).first()
    if not ie:
        raise HTTPException(status_code=404, detail="Индивидуальный предприниматель не найден")
    return JSONResponse(
        content={"status": True, "data": ie.to_dict(), "message": "Успешно"},
        status_code=200,
    )
@router.get("/individual-entrepreneur/me")
def get_individual_entrepreneurs_for_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ie = db.query(IndividualEntrepreneur).filter(IndividualEntrepreneur.owner_id == current_user.id).all()
    if not ie:
        return JSONResponse(
            content={
                "status": False,
                "data": [],  # Возвращаем пустой массив
                "message": "ип не найдены"
            },
            status_code=200,
        )
    return JSONResponse(
        content={
            "status": True,
            "data": [entrepreneur.to_dict() for entrepreneur in ie],
            "message": "Успешно"
        },
        status_code=200,
    )


@router.put("/individual-entrepreneurs/{id}", response_model=IndividualEntrepreneurResponse)
def update_individual_entrepreneur(
    id: int,
    ie_data: IndividualEntrepreneurUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ie = db.query(IndividualEntrepreneur).filter(IndividualEntrepreneur.id == id).first()
    if not ie:
        raise HTTPException(status_code=404, detail="Индивидуальный предприниматель не найден")
    # Проверяем, является ли текущий пользователь владельцем
    if ie.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не авторизованы для обновления этого предпринимателя")

    for key, value in ie_data.dict(exclude_unset=True).items():
        setattr(ie, key, value)

    db.commit()
    db.refresh(ie)
    return ie


@router.delete("/individual-entrepreneurs/{id}", response_model=IndividualEntrepreneurResponse)
def delete_individual_entrepreneur(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ie = db.query(IndividualEntrepreneur).filter(IndividualEntrepreneur.id == id).first()
    if not ie:
        raise HTTPException(status_code=404, detail="Индивидуальный предприниматель не найден")
    # Проверяем, является ли текущий пользователь владельцем
    if ie.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы не авторизованы для удаления этого предпринимателя")
    
    db.delete(ie)
    db.commit()
    return ie

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




@router.get("/user/details")
def get_user_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Загружаем связанные данные пользователя
    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .options(
            joinedload(User.organizations).joinedload(Organization.services),
            joinedload(User.organizations).joinedload(Organization.products),
            joinedload(User.individual_entrepreneur).joinedload(IndividualEntrepreneur.services),
            joinedload(User.individual_entrepreneur).joinedload(IndividualEntrepreneur.products),
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Формируем результат
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "organizations": [
            {
                "id": org.id,
                "name": org.name,
                "description": org.description,
                "services": [
                    {"id": svc.id, "name": svc.name, "price": svc.price} for svc in org.services
                ],
                "products": [
                    {"id": prod.id, "name": prod.name, "price": prod.price} for prod in org.products
                ],
            }
            for org in user.organizations
        ],
        "individual_entrepreneur": {
            "id": user.individual_entrepreneur.id,
            "inn": user.individual_entrepreneur.inn,
            "ogrnip": user.individual_entrepreneur.ogrnip,
            "services": [
                {"id": svc.id, "name": svc.name, "price": svc.price} for svc in user.individual_entrepreneur.services
            ],
            "products": [
                {"id": prod.id, "name": prod.name, "price": prod.price} for prod in user.individual_entrepreneur.products
            ],
        } if user.individual_entrepreneur else None,
    }
@router.post("/services/")
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем, принадлежит ли организация пользователю
    if service_data.organization_id:
        organization = db.query(Organization).filter(
            Organization.id == service_data.organization_id,
            Organization.owner_id == current_user.id,
        ).first()
        if not organization:
            return JSONResponse(
                content={"status": False, "message": "Организация не найдена или не принадлежит текущему пользователю"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # Проверяем, принадлежит ли индивидуальный предприниматель пользователю
    if service_data.individual_entrepreneur_id:
        entrepreneur = db.query(IndividualEntrepreneur).filter(
            IndividualEntrepreneur.id == service_data.individual_entrepreneur_id,
            IndividualEntrepreneur.owner_id == current_user.id,
        ).first()
        if not entrepreneur:
            return JSONResponse(
                content={"status": False, "message": "ИП не найден или не принадлежит текущему пользователю"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # Создаем услугу
    new_service = Service(**service_data.dict())
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return JSONResponse(
        content={"status": True, "data": new_service.to_dict(), "message": "Услуга успешно создана"},
        status_code=status.HTTP_201_CREATED,
    )

@router.delete("/services/{id}")
def delete_service(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = db.query(Service).filter(Service.id == id).first()
    if not service:
        return JSONResponse(
            content={"status": False, "message": "Услуга не найдена"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Проверяем, имеет ли пользователь право удалить услугу
    if service.organization_id:
        organization = db.query(Organization).filter(
            Organization.id == service.organization_id,
            Organization.owner_id == current_user.id,
        ).first()
        if not organization:
            return JSONResponse(
                content={"status": False, "message": "Услуга не принадлежит вашей организации"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    if service.individual_entrepreneur_id:
        entrepreneur = db.query(IndividualEntrepreneur).filter(
            IndividualEntrepreneur.id == service.individual_entrepreneur_id,
            IndividualEntrepreneur.owner_id == current_user.id,
        ).first()
        if not entrepreneur:
            return JSONResponse(
                content={"status": False, "message": "Услуга не принадлежит вашему ИП"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    db.delete(service)
    db.commit()

    return JSONResponse(
        content={"status": True, "message": "Услуга успешно удалена"},
        status_code=status.HTTP_200_OK,
    )

# --- Product CRUD Operations ---
@router.post("/products/")
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем, принадлежит ли организация пользователю
    if product_data.organization_id:
        organization = db.query(Organization).filter(
            Organization.id == product_data.organization_id,
            Organization.owner_id == current_user.id,
        ).first()
        if not organization:
            return JSONResponse(
                content={"status": False, "message": "Организация не найдена или не принадлежит текущему пользователю"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # Проверяем, принадлежит ли индивидуальный предприниматель пользователю
    if product_data.individual_entrepreneur_id:
        entrepreneur = db.query(IndividualEntrepreneur).filter(
            IndividualEntrepreneur.id == product_data.individual_entrepreneur_id,
            IndividualEntrepreneur.owner_id == current_user.id,
        ).first()
        if not entrepreneur:
            return JSONResponse(
                content={"status": False, "message": "ИП не найден или не принадлежит текущему пользователю"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # Создаем продукт
    new_product = Product(**product_data.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return JSONResponse(
        content={"status": True, "data": new_product.to_dict(), "message": "Продукт успешно создан"},
        status_code=status.HTTP_201_CREATED,
    )

@router.delete("/products/{id}")
def delete_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        return JSONResponse(
            content={"status": False, "message": "Продукт не найден"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Проверяем, имеет ли пользователь право удалить продукт
    if product.organization_id:
        organization = db.query(Organization).filter(
            Organization.id == product.organization_id,
            Organization.owner_id == current_user.id,
        ).first()
        if not organization:
            return JSONResponse(
                content={"status": False, "message": "Продукт не принадлежит вашей организации"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    if product.individual_entrepreneur_id:
        entrepreneur = db.query(IndividualEntrepreneur).filter(
            IndividualEntrepreneur.id == product.individual_entrepreneur_id,
            IndividualEntrepreneur.owner_id == current_user.id,
        ).first()
        if not entrepreneur:
            return JSONResponse(
                content={"status": False, "message": "Продукт не принадлежит вашему ИП"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    db.delete(product)
    db.commit()

    return JSONResponse(
        content={"status": True, "message": "Продукт успешно удален"},
        status_code=status.HTTP_200_OK,
    )