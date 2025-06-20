from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from db.connection import Base


#  компании


class Company(Base):
    __tablename__ = "companies"

    id: int = Column(Integer, primary_key=True)
    owner_id: int = Column(BigInteger, index=True, nullable=False)
    title: str = Column(String(255), nullable=False)

    created_at: dt.datetime = Column(
        DateTime,
        default=dt.datetime.utcnow,
        nullable=False,
    )

    vacancies = relationship("Vacancy", back_populates="company", lazy="selectin")
    members = relationship("CompanyMember", back_populates="company", lazy="selectin")


#  вакансии


class Vacancy(Base):  # type: ignore[misc]
    __tablename__ = "vacancies"

    id: int = Column(Integer, primary_key=True)
    company_id: int = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title: str = Column(String(255), nullable=False)

    description: str = Column(String, default="")
    requirements: str = Column(String, default="")
    duties: str = Column(String, default="")
    conditions: str = Column(String, default="")
    is_active: bool = Column(Boolean, default=True)

    company = relationship("Company", back_populates="vacancies")


#  сотрудники компании (HR-ы, владельцы…)


class CompanyMember(Base):
    __tablename__ = "company_members"

    company_id: int = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: int = Column(BigInteger, primary_key=True)  # Telegram-ID сотрудника
    role: str = Column(String(50), default="hr")  # 'hr', 'owner', …

    company = relationship("Company", back_populates="members")
