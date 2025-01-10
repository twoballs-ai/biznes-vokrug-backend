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
from ..database import get_db
from ..models import IndividualEntrepreneur, Product, ProductCategory, Service, ServiceCategory, User, Organization
from ..schemas import (
    IndividualEntrepreneurCreate,
    IndividualEntrepreneurResponse,
    IndividualEntrepreneurUpdate,
    ProductCreate,
    ServiceCreate,
    UserCreate,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    UserUpdate
)
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

category_product = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

service_categories_data = [
    {"name": "Образование", "description": "Услуги в области образования, курсов и тренингов."},
    {"name": "Здравоохранение", "description": "Услуги, связанные с медициной и здоровьем."},
    {"name": "Юридические услуги", "description": "Услуги юридических консультаций и представительства в суде."},
    {"name": "Бухгалтерия", "description": "Услуги бухгалтерского учёта и финансовой отчётности."},
    {"name": "Ремонт и строительство", "description": "Услуги ремонта, строительства и отделки помещений."},
    {"name": "Логистика", "description": "Услуги транспортировки, доставки и складирования."},
    {"name": "ИТ и технологии", "description": "Услуги разработки программного обеспечения и системного администрирования."},
    {"name": "Дизайн", "description": "Графический, интерьерный и промышленный дизайн."},
    {"name": "Реклама и маркетинг", "description": "Услуги продвижения, SMM и рекламных кампаний."},
    {"name": "Финансовые услуги", "description": "Кредитование, инвестирование и финансовые консультации."},
    {"name": "Клининг", "description": "Услуги профессиональной уборки и клининга помещений."},
    {"name": "Красота и здоровье", "description": "Косметологические, парикмахерские и массажные услуги."},
    {"name": "Туризм", "description": "Услуги туристических агентств и гидов."},
    {"name": "Спорт", "description": "Услуги спортивных секций, тренеров и фитнес-центров."},
    {"name": "Общественное питание", "description": "Услуги кафе, ресторанов и кейтеринга."},
    {"name": "Фото и видео", "description": "Услуги фотографов и видеографов."},
    {"name": "Автосервис", "description": "Ремонт, техобслуживание и диагностика автомобилей."},
    {"name": "Няни и сиделки", "description": "Услуги ухода за детьми и престарелыми людьми."},
    {"name": "Энергетика", "description": "Услуги проектирования и обслуживания энергетических систем."},
    {"name": "Экологические услуги", "description": "Услуги по переработке отходов и экологии."},
]
product_categories_data = [
    {"name": "Электроника", "description": "Товары, связанные с электроникой."},
    {"name": "Продукты питания", "description": "Все категории еды и напитков."},
    {"name": "Одежда", "description": "Мужская, женская и детская одежда."},
    {"name": "Обувь", "description": "Обувь для всех сезонов и поводов."},
    {"name": "Мебель", "description": "Мебель для дома, офиса и дачи."},
    {"name": "Канцелярия", "description": "Товары для офиса, школы и творчества."},
    {"name": "Игрушки", "description": "Детские игрушки для разных возрастов."},
    {"name": "Косметика", "description": "Декоративная и уходовая косметика."},
    {"name": "Бытовая техника", "description": "Техника для дома, кухни и уборки."},
    {"name": "Автозапчасти", "description": "Запчасти и аксессуары для автомобилей."},
    {"name": "Книги", "description": "Художественная и образовательная литература."},
    {"name": "Спорттовары", "description": "Товары для спорта и активного отдыха."},
    {"name": "Зоотовары", "description": "Корма, игрушки и аксессуары для животных."},
    {"name": "Инструменты", "description": "Электро- и ручной инструмент."},
    {"name": "Декор", "description": "Предметы интерьера и украшения."},
    {"name": "Ювелирные изделия", "description": "Золото, серебро и драгоценные камни."},
    {"name": "Часы", "description": "Наручные и настенные часы."},
    {"name": "Медицинские товары", "description": "Аптечные и медицинские устройства."},
    {"name": "Кухонные принадлежности", "description": "Посуда и аксессуары для кухни."},
    {"name": "Компьютеры и аксессуары", "description": "ПК, ноутбуки и комплектующие."},
]

# @category_product.post("/service-categories")
# def add_service_categories(db: Session = Depends(get_db)):
#     try:
#         for category in service_categories_data:
#             existing_category = db.query(ServiceCategory).filter(ServiceCategory.name == category["name"]).first()
#             if not existing_category:
#                 db.add(ServiceCategory(**category))
#         db.commit()
#         return {"message": "Категории услуг успешно добавлены."}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Ошибка добавления категорий услуг: {e}")


# # POST-запрос для добавления категорий продуктов
# @category_product.post("/product-categories")
# def add_product_categories(db: Session = Depends(get_db)):
#     try:
#         for category in product_categories_data:
#             existing_category = db.query(ProductCategory).filter(ProductCategory.name == category["name"]).first()
#             if not existing_category:
#                 db.add(ProductCategory(**category))
#         db.commit()
#         return {"message": "Категории продуктов успешно добавлены."}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Ошибка добавления категорий продуктов: {e}")
    
# GET-запрос для получения продуктов пользователя, разделенных по ИП и организации
# GET-запрос для получения продуктов пользователя, разделенных по ИП и организации
@category_product.get("/organization/products")
def get_organization_products(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Проверяем, принадлежит ли организация текущему пользователю
        organization = db.query(Organization).filter(
            Organization.id == organization_id,
            Organization.owner_id == current_user.id
        ).first()

        if not organization:
            raise HTTPException(status_code=403, detail="Организация не найдена или не принадлежит пользователю.")

        # Получение продуктов
        org_products = (
            db.query(Product)
            .filter(Product.organization_id == organization_id)
            .options(joinedload(Product.category))
            .all()
        )

        return [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "category": product.category.name if product.category else None,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
            }
            for product in org_products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения продуктов: {e}")
    
@category_product.get("/entrepreneur/products")
def get_individual_entrepreneur_products(
    entrepreneur_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Проверяем, принадлежит ли ИП текущему пользователю
        entrepreneur = db.query(IndividualEntrepreneur).filter(
            IndividualEntrepreneur.id == entrepreneur_id,
            IndividualEntrepreneur.owner_id == current_user.id
        ).first()

        if not entrepreneur:
            raise HTTPException(status_code=403, detail="ИП не найден или не принадлежит пользователю.")

        # Получение продуктов
        ie_products = (
            db.query(Product)
            .filter(Product.individual_entrepreneur_id == entrepreneur_id)
            .options(joinedload(Product.category))
            .all()
        )

        return [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "category": product.category.name if product.category else None,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
            }
            for product in ie_products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения продуктов: {e}")
@category_product.get("/organization/services")
def get_organization_services(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Проверяем, принадлежит ли организация текущему пользователю
        organization = db.query(Organization).filter(
            Organization.id == organization_id,
            Organization.owner_id == current_user.id
        ).first()

        if not organization:
            raise HTTPException(status_code=403, detail="Организация не найдена или не принадлежит пользователю.")

        # Получение услуг
        org_services = (
            db.query(Service)
            .filter(Service.organization_id == organization_id)
            .options(joinedload(Service.category))
            .all()
        )

        return [
            {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "price": service.price,
                "category": service.category.name if service.category else None,
                "created_at": service.created_at,
                "updated_at": service.updated_at,
            }
            for service in org_services
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения услуг: {e}")

@category_product.get("/entrepreneur/services")
def get_individual_entrepreneur_services(
    entrepreneur_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Проверяем, принадлежит ли ИП текущему пользователю
        entrepreneur = db.query(IndividualEntrepreneur).filter(
            IndividualEntrepreneur.id == entrepreneur_id,
            IndividualEntrepreneur.owner_id == current_user.id
        ).first()

        if not entrepreneur:
            raise HTTPException(status_code=403, detail="ИП не найден или не принадлежит пользователю.")

        # Получение услуг
        ie_services = (
            db.query(Service)
            .filter(Service.individual_entrepreneur_id == entrepreneur_id)
            .options(joinedload(Service.category))
            .all()
        )

        return [
            {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "price": service.price,
                "category": service.category.name if service.category else None,
                "created_at": service.created_at,
                "updated_at": service.updated_at,
            }
            for service in ie_services
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения услуг: {e}")

@category_product.get("/service-categories-dropdown", response_model=list[dict])
def get_service_categories_dropdown(db: Session = Depends(get_db)):
    try:
        categories = db.query(ServiceCategory).all()
        return [category.to_key_value() for category in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения категорий сервисов: {e}")


# GET-запрос для получения категорий продуктов
@category_product.get("/product-categories-dropdown", response_model=list[dict])
def get_product_categories_dropdown(db: Session = Depends(get_db)):
    try:
        categories = db.query(ProductCategory).all()
        return [category.to_key_value() for category in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения категорий продуктов: {e}")