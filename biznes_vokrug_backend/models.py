from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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