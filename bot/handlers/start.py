from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from bot.keyboards import hr_main_kb, role_choice_kb, vacancy_inline_kb
from services import VacancyService

router = Router(name="start")


#  /start


@router.message(Command("start"))
async def cmd_start(m: Message) -> None:
    await m.answer(
        "Привет! Выберите, кто вы:",
        reply_markup=role_choice_kb(),
    )


#  /info


@router.message(Command("info"))
async def cmd_info(m: Message) -> None:
    text = (
        "<b>Как пользоваться ботом</b>\n\n"
        "👤 <b>Соискатель</b>\n"
        "• Нажмите «Я соискатель» и выберите вакансию.\n"
        "• Откликнитесь, отправив файл-резюме.\n"
        "• После успешного отклика получите AI-советы.\n\n"
        "💼 <b>HR</b>\n"
        "• «Я HR» → создайте компанию и вакансии.\n"
        "• Редактируйте вакансии и получайте отклики.\n\n"
        "Для отмены действия используйте /cancel."
    )
    await m.answer(text, disable_web_page_preview=True)


#  HR-режим


@router.message(F.text == "Я HR")
async def role_hr(m: Message) -> None:
    kb = await hr_main_kb(m.from_user.id)
    await m.answer("Вы перешли в режим HR. Используйте меню ниже.", reply_markup=kb)


#  Режим соискателя


@router.message(F.text == "Я соискатель")
async def role_candidate(m: Message) -> None:
    # показываем либо список вакансий, либо сообщение «нет вакансий»
    vacancies = await VacancyService.all_active()
    kb = await vacancy_inline_kb() if vacancies else None
    text = "Выберите вакансию:" if vacancies else "Пока нет открытых вакансий."
    await m.answer(text, reply_markup=kb)


#  случайные сообщения


@router.message(StateFilter(None))
async def fallback_message(m: Message) -> None:
    await m.answer(
        "Я не понял сообщение 🤔\n"
        "Пожалуйста, воспользуйтесь кнопками меню или командой /info."
    )
