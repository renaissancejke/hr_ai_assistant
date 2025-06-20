from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from bot.handlers.resume_fsm import ResumeFSM
from bot.keyboards import vacancy_inline_kb
from services import VacancyService

router = Router(name="candidate")


#  Карточка вакансии + кнопки


@router.callback_query(F.data.startswith("vac_"))
async def show_vacancy(cq: CallbackQuery) -> None:
    vac_id = int(cq.data.split("_", 1)[1])
    vacancy = await VacancyService.by_id(vac_id)
    if not vacancy:
        await cq.answer("Вакансия не найдена", show_alert=True)
        return

    text = (
        f"<b>{vacancy.title}</b>\n\n"
        f"{vacancy.description or 'Описание отсутствует.'}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📎 Откликнуться", callback_data=f"respond_{vacancy.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К списку вакансий", callback_data="back_vacancies"
                )
            ],
        ]
    )
    await cq.message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await cq.answer()


#  Кнопка «📎 Откликнуться»


@router.callback_query(F.data.startswith("respond_"))
async def start_respond(cb: CallbackQuery, state: FSMContext) -> None:
    vac_id = int(cb.data.split("_", 1)[1])

    vacancy = await VacancyService.by_id(vac_id)
    if not vacancy:
        await cb.answer("Вакансия не найдена", show_alert=True)
        return

    await state.update_data(vacancy_id=vac_id)
    await state.set_state(ResumeFSM.waiting_for_file)

    await cb.message.answer(
        "Пришлите файл-резюме (PDF, DOC/DOCX или TXT).\n" "Если передумали — /cancel",
    )
    await cb.answer()


#  Кнопка «🔙 К списку вакансий»


@router.callback_query(F.data == "back_vacancies")
async def back_to_vacancies(cb: CallbackQuery) -> None:
    kb = await vacancy_inline_kb()  # список всех активных вакансий
    if kb.inline_keyboard:
        await cb.message.answer("Выберите вакансию:", reply_markup=kb)
    else:
        await cb.message.answer("Пока нет открытых вакансий.")
    await cb.answer()
