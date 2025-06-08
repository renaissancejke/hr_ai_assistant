from __future__ import annotations

import pathlib
from typing import Any

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards import GET_TIPS_KB, POST_UPLOAD_KB, vacancy_inline_kb
from services import ResumeService
from services.errors import InvalidResumeError
from settings.config import setup

router = Router()

MSG_WELCOME = (
    "Привет! 👋\n"
    "Я помогу сопоставить ваше резюме с открытыми вакансиями RakeStep.\n\n"
    "👇 Выберите интересующую вакансию:"
)
MSG_MENU_HELP = (
    "ℹ️ Команды:\n" "• /start — выбрать вакансию\n" "• /info  — как пользоваться ботом"
)
MSG_FMT_UNSUPPORTED = (
    "❌ Этот формат не поддерживается. Пришлите PDF, DOC/DOCX или TXT-файл."
)
MSG_PROCESSING = "⚙️ Обрабатываем ваше резюме…"
MSG_SUCCESS = (
    "Спасибо! Мы свяжемся с вами после рассмотрения.\n"
    "Подпишитесь на @rakestep, чтобы не пропустить новости."
)


@router.message(CommandStart())
async def cmd_start(m: types.Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer(MSG_WELCOME, reply_markup=vacancy_inline_kb())


@router.message(Command("info"))
async def cmd_info(m: types.Message) -> None:
    await m.answer(
        "ℹ️ Как пользоваться ботом:\n"
        "1️⃣ /start — выбрать вакансию\n"
        "2️⃣ Отправьте резюме (PDF/DOCX/TXT)\n"
        "3️⃣ Получите обратную связь и рейтинг"
    )


@router.message(F.text == "👀 Посмотреть вакансии")
async def show_vacancies(m: types.Message) -> None:
    await m.answer("Актуальные вакансии:", reply_markup=vacancy_inline_kb())


@router.message(F.text == "📄 Моё резюме")
async def send_my_resume(m: types.Message, state: FSMContext) -> None:
    file_id = (await state.get_data()).get("resume_file_id")
    (
        await m.answer_document(file_id)
        if file_id
        else await m.answer("Вы ещё не отправляли резюме.")
    )


@router.callback_query(F.data.startswith("vac|"))
async def choose_vacancy(cb: types.CallbackQuery, state: FSMContext) -> None:
    _, vacancy = cb.data.split("|", 1)
    await state.update_data(vacancy=vacancy)
    await cb.message.edit_text(f"Вы выбрали <b>{vacancy}</b>.", parse_mode="HTML")
    await cb.message.answer(
        "Пришлите файл PDF, DOC/DOCX или TXT с резюме.",
        reply_markup=POST_UPLOAD_KB,
    )
    await cb.answer()


@router.message(F.document)
async def handle_document(m: types.Message, state: FSMContext) -> None:
    vacancy = (await state.get_data()).get("vacancy")
    if not vacancy:
        return await m.answer("Сначала выберите вакансию через /start.")

    ext = pathlib.Path(m.document.file_name or "").suffix.lower()
    processing = await m.answer(MSG_PROCESSING)

    try:
        meta: dict[str, Any] = await ResumeService.evaluate(
            bot=m.bot,
            tg_file=await m.bot.get_file(m.document.file_id),
            vacancy_name=vacancy,
            ext=ext,
            telegram_user_id=m.from_user.id,
        )
    except InvalidResumeError:
        await processing.edit_text(
            "Файл не похож на резюме 🤔\n"
            "Пожалуйста, отправьте корректный PDF, DOCX или TXT с вашим опытом."
        )
        return
    except ValueError:
        return await m.answer(MSG_FMT_UNSUPPORTED)

    if meta["rating"] < 40:
        lack = ResumeService._humanize_missing(meta.get("missing_experience"))
        await processing.edit_text(f"😔 Недостаточно опыта: {lack}.")
        return

    await processing.edit_text(MSG_SUCCESS)
    if p := ResumeService.thanks_photo():
        await m.answer_photo(p)

    await state.update_data(
        resume_file_id=m.document.file_id,
        interview_tips=meta.get("interview_tips", ""),
    )

    await m.answer(
        "Хотите получить рекомендации для прохождения собеседования "
        "от нашего ИИ-HR-агента?",
        reply_markup=GET_TIPS_KB,
    )

    caption = ResumeService.build_hr_caption(vacancy, meta, m.from_user.username)
    await m.bot.send_document(
        setup.summary_chat_id, m.document.file_id, caption=caption
    )


@router.callback_query(F.data.startswith("tips|"))
async def tips_handler(cb: types.CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    if cb.data.endswith("yes"):
        tips = (await state.get_data()).get("interview_tips") or "Советов нет 🤷‍♂️"
        await cb.message.answer(f"🤖 Советы ИИ-HR-агента:\n{tips}")
    else:
        await cb.message.answer("Хорошо, будем на связи. Удачи!")


@router.message()
async def catch_all(m: types.Message) -> None:
    await m.answer(MSG_MENU_HELP)
