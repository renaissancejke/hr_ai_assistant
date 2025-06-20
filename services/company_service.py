from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.connection import async_session
from db.models import Company, Vacancy


class CompanyService:

    # создать компанию

    @staticmethod
    async def create_company(owner_id: int, title: str) -> Company:
        async with async_session() as s:
            comp = Company(owner_id=owner_id, title=title.strip())
            s.add(comp)
            await s.commit()
            await s.refresh(comp)
            return comp

    # все компании конкретного HR-а

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

    # компании HR-а + список вакансий

    @staticmethod
    async def companies_with_vacancies(owner_id: int) -> Dict[str, List[Vacancy]]:
        companies = await CompanyService.companies_for_user(owner_id)
        mapping: Dict[str, List[Vacancy]] = {}
        for c in companies:
            if c.vacancies:
                mapping[c.title] = list(c.vacancies)
        return mapping

    # создать вакансию

    @staticmethod
    async def create_vacancy(company_id: int, title: str) -> Vacancy:
        async with async_session() as s:
            vac = Vacancy(company_id=company_id, title=title.strip())
            s.add(vac)
            await s.commit()
            await s.refresh(vac)
            return vac
