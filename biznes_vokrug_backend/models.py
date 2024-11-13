from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .database import Base

class Owner(Base):
    __tablename__ = "owners_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
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


class Organization(Base):
    __tablename__ = "organizations_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    inn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ogrn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    owner_id: Mapped[int] = mapped_column(ForeignKey("owners_models.id"))

    owner: Mapped["Owner"] = relationship(back_populates="organizations")

class IndividualEntrepreneur(Base):
    __tablename__ = "individual_entrepreneurs_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    ogrnip: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners_models.id"))

    owner: Mapped["Owner"] = relationship(back_populates="individual_entrepreneur")