from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select, update  # ← update добавлен
from sqlalchemy.orm import selectinload

from db.connection import async_session
from db.models import Company, Vacancy


class CompanyService:
    """Операции над компаниями + полезные выборки."""

    # ─────────────── CRUD ───────────────
    @staticmethod
    async def create_company(owner_id: int, title: str) -> Company:
        async with async_session() as s:
            comp = Company(owner_id=owner_id, title=title.strip())
            s.add(comp)
            await s.commit()
            await s.refresh(comp)
            return comp

    @staticmethod
    async def update_title(company_id: int, title: str) -> None:
        """Переименовать компанию."""
        async with async_session() as s:
            await s.execute(
                update(Company)
                .where(Company.id == company_id)
                .values(title=title.strip())
            )
            await s.commit()

    # ─────────────── выборки ───────────────
    @staticmethod
    async def companies_for_user(owner_id: int) -> List[Company]:
        async with async_session() as s:
            res = await s.execute(
                select(Company)
                .where(Company.owner_id == owner_id)
                .options(selectinload(Company.vacancies))
                .order_by(Company.id.asc())
            )
            return res.scalars().all()

    @staticmethod
    async def companies_with_vacancies(owner_id: int) -> Dict[str, List[Vacancy]]:
        """Название компании → список активных вакансий."""
        companies = await CompanyService.companies_for_user(owner_id)
        mapping: Dict[str, List[Vacancy]] = {}
        for c in companies:
            active = [v for v in c.vacancies if v.is_active]
            if active:
                mapping[c.title] = active
        return mapping
