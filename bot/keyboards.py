from __future__ import annotations

from collections import defaultdict
from typing import List

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from services import CompanyService, VacancyService
from db.models import Vacancy


def role_choice_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Я HR"), KeyboardButton(text="Я соискатель")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def hr_main_kb(owner_id: int) -> ReplyKeyboardMarkup:
    companies = await CompanyService.companies_for_user(owner_id)
    have_companies = bool(companies)
    have_vacancies = any(any(v.is_active for v in c.vacancies) for c in companies)

    rows: list[list[KeyboardButton]] = []

    if have_companies:
        rows.append([KeyboardButton(text="➕ Создать вакансию")])
        rows.append([KeyboardButton(text="✏️ Редактировать компании")])
        if have_vacancies:
            rows.append([KeyboardButton(text="✏️ Редактировать вакансии")])
    else:
        rows.append([KeyboardButton(text="🏢 Создать компанию")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


async def company_inline_kb(owner_id: int) -> InlineKeyboardMarkup:
    companies = await CompanyService.companies_for_user(owner_id)
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"🏢 {c.title}", callback_data=f"companyedit_{c.id}"
            )
        ]
        for c in companies
    ]

    if not rows:
        rows = [[InlineKeyboardButton(text="Компаний нет", callback_data="noop")]]

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def vacancy_inline_kb(
    *,
    owner_id: int | None = None,
    mode: str = "view",
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if owner_id is not None:
        # HR-режим
        mapping = await CompanyService.companies_with_vacancies(owner_id)
        for company_name, vacancies in mapping.items():
            rows.append(
                [InlineKeyboardButton(text=f"🏢 {company_name}", callback_data="noop")]
            )
            for v in vacancies:
                prefix = "edit_" if mode == "edit" else "vac_"
                rows.append(
                    [
                        InlineKeyboardButton(
                            text=f"— {v.title}", callback_data=f"{prefix}{v.id}"
                        )
                    ]
                )
    else:
        vacancies: List[Vacancy] = await VacancyService.all_active()
        grouped: dict[str, list[Vacancy]] = defaultdict(list)
        for v in vacancies:
            grouped[v.company.title].append(v)

        for company_name in sorted(grouped.keys()):
            rows.append(
                [InlineKeyboardButton(text=f"🏢 {company_name}", callback_data="noop")]
            )
            for v in grouped[company_name]:
                rows.append(
                    [
                        InlineKeyboardButton(
                            text=f"— {v.title}", callback_data=f"vac_{v.id}"
                        )
                    ]
                )

    if not rows:
        rows.append(
            [InlineKeyboardButton(text="Нет открытых вакансий", callback_data="noop")]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)
