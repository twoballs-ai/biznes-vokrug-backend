from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .database import Base

# User model remains the same
class User(Base):
    __tablename__ = "user_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    organizations: Mapped[List["Organization"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    individual_entrepreneur: Mapped[Optional["IndividualEntrepreneur"]] = relationship(
        back_populates="owner", uselist=False, cascade="all, delete-orphan"
    )
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            # Include related models if needed
            "organizations": self.organizations if self.organizations else None,
            "individual_entrepreneur": self.individual_entrepreneur if self.individual_entrepreneur else None,
        }

class Organization(Base):
    __tablename__ = "organizations_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    inn: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True,)
    ogrn: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True,)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )

    owner_id: Mapped[int] = mapped_column(ForeignKey("user_models.id"))

    owner: Mapped["User"] = relationship(back_populates="organizations")

    services: Mapped[List["Service"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "address": self.address,
            "inn": self.inn,
            "ogrn": self.ogrn,
            "phone": self.phone,
            "website": self.website,
            "email": self.email,
            "category": self.category,
            "is_verified": self.is_verified,
            "rating": self.rating,
            "logo_url": self.logo_url,
            "city": self.city,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "owner_id": self.owner_id,
            "services": [service.to_dict() for service in self.services] if self.services else [],
            "products": [product.to_dict() for product in self.products] if self.products else [],
        }


class IndividualEntrepreneur(Base):
    __tablename__ = "individual_entrepreneurs_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    ogrnip: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user_models.id"))

    owner: Mapped["User"] = relationship(back_populates="individual_entrepreneur")

    services: Mapped[List["Service"]] = relationship(
        back_populates="individual_entrepreneur", cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        back_populates="individual_entrepreneur", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "inn": self.inn,
            "ogrnip": self.ogrnip,
            "phone": self.phone,
            "owner_id": self.owner_id,
            "services": [service.to_dict() for service in self.services] if self.services else [],
            "products": [product.to_dict() for product in self.products] if self.products else [],
        }

# Service model for Organization and IndividualEntrepreneur
class Service(Base):
    __tablename__ = "services_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations_models.id"))
    individual_entrepreneur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("individual_entrepreneurs_models.id"))

    organization: Mapped[Optional["Organization"]] = relationship(back_populates="services")
    individual_entrepreneur: Mapped[Optional["IndividualEntrepreneur"]] = relationship(back_populates="services")

# Product model for Organization and IndividualEntrepreneur
class Product(Base):
    __tablename__ = "products_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    price: Mapped[Optional[Float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations_models.id"))
    individual_entrepreneur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("individual_entrepreneurs_models.id"))

    organization: Mapped[Optional["Organization"]] = relationship(back_populates="products")
    individual_entrepreneur: Mapped[Optional["IndividualEntrepreneur"]] = relationship(back_populates="products")

