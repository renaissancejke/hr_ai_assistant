from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload, selectinload

from db.connection import async_session
from db.models import Vacancy


class VacancyService:
    """CRUD + вспомогательные методы по вакансиям."""

    # получить вакансию по ID (с привязанной company)
    @staticmethod
    async def by_id(vacancy_id: int) -> Optional[Vacancy]:
        async with async_session() as s:
            res = await s.execute(
                select(Vacancy)
                .options(selectinload(Vacancy.company))
                .where(Vacancy.id == vacancy_id)
            )
            return res.scalar_one_or_none()

    # все активные вакансии (для кандидата)
    @staticmethod
    async def all_active() -> List[Vacancy]:
        async with async_session() as s:
            stmt = (
                select(Vacancy)
                .options(joinedload(Vacancy.company))
                .where(Vacancy.is_active.is_(True))
                .order_by(Vacancy.id.desc())
            )
            res = await s.execute(stmt)
            return res.scalars().all()

    # создать вакансию
    @staticmethod
    async def create(company_id: int, title: str, description: str = "") -> Vacancy:
        async with async_session() as s:
            vac = Vacancy(
                company_id=company_id,
                title=title.strip(),
                description=description.strip(),
            )
            s.add(vac)
            await s.commit()
            await s.refresh(vac)
            return vac

    # обновить название
    @staticmethod
    async def update_title(vacancy_id: int, title: str) -> None:
        async with async_session() as s:
            await s.execute(
                update(Vacancy)
                .where(Vacancy.id == vacancy_id)
                .values(title=title.strip())
            )
            await s.commit()

    # обновить описание
    @staticmethod
    async def update_description(vacancy_id: int, description: str) -> None:
        async with async_session() as s:
            await s.execute(
                update(Vacancy)
                .where(Vacancy.id == vacancy_id)
                .values(description=description.strip())
            )
            await s.commit()

    # пометить вакансию неактивной (мягкое удаление)
    @staticmethod
    async def deactivate(vacancy_id: int) -> None:
        async with async_session() as s:
            await s.execute(
                update(Vacancy).where(Vacancy.id == vacancy_id).values(is_active=False)
            )
            await s.commit()

    # жёсткое удаление записи из БД (использовать осторожно)
    @staticmethod
    async def delete(vacancy_id: int) -> None:
        async with async_session() as s:
            await s.execute(delete(Vacancy).where(Vacancy.id == vacancy_id))
            await s.commit()
