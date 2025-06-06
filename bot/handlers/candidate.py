from __future__ import annotations

import datetime as dt
import pathlib
import typing as t
from uuid import uuid4

from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from pathlib import Path
from aiogram.exceptions import TelegramBadRequest

from bot.handlers.resume import ALLOWED_EXT, extract_text, process_resume
from bot.keyboards import (
    POST_UPLOAD_KB,
    vacancy_inline_kb,
    GET_TIPS_KB,
)
from settings.config import setup
from vacancies import VACANCIES

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


# ────── helpers ──────────────────────────────────────────────────────────────
def humanize_missing(value: t.Any) -> str:

    if not value:
        return "ключевых навыках"

    if isinstance(value, str):
        return value.strip().rstrip(".;,")  # убираем завершающую пунктуацию

    if isinstance(value, (list, tuple)):
        joined = ", ".join(map(str, value[:3]))
        return joined.rstrip(".;,")

    return str(value).rstrip(".;,")


def build_hr_caption(vacancy: str, meta: dict, username: str | None) -> str:
    vacancy_tag = f"#{vacancy.replace(' ', '_')}"
    missing = humanize_missing(meta.get("missing_experience"))
    questions = meta["interview_questions"]

    return (
        f"{vacancy_tag}\n"
        f"Кандидат подходит на {meta['rating']:.0f}%\n\n"
        f"💪 Сильные стороны: {meta['strong']}\n"
        f"📉 Слабые стороны: {meta['weak']}\n"
        f"🔗 Релевантный опыт: {meta['matched_experience']}\n"
        f"🚫 Не хватает опыта: {missing}\n"
        f"💧 «Вода»: {meta['water']}\n"
        f"⚠️ Несоответствия / подозрения: "
        f"{meta['mismatches'] or meta['suspicious']}\n\n"
        f"❓ Вопросы для собеседования:\n"
        f"• {questions[0]}\n"
        f"• {questions[1]}\n"
        f"• {questions[2]}\n\n"
        f"📱 Контакт: @{username or '—'}"
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
        "3️⃣ Получите обратную связь и рейтинг\n\n"
        "После загрузки появятся кнопки:\n"
        "• «👀 Посмотреть вакансии»\n"
        "• «📄 Моё резюме»"
    )


@router.message(F.text == "👀 Посмотреть вакансии")
async def show_vacancies(m: types.Message) -> None:
    await m.answer("Актуальные вакансии:", reply_markup=vacancy_inline_kb())


@router.message(F.text == "📄 Моё резюме")
async def send_my_resume(m: types.Message, state: FSMContext) -> None:
    file_id = (await state.get_data()).get("resume_file_id")
    if file_id:
        await m.answer_document(file_id)
    else:
        await m.answer("Вы ещё не отправляли резюме.")


@router.callback_query(F.data.startswith("vac|"))
async def choose_vacancy(cb: types.CallbackQuery, state: FSMContext) -> None:
    _, vacancy = cb.data.split("|", 1)
    await state.update_data(vacancy=vacancy)
    await cb.message.edit_text(
        f"Вы выбрали <b>{vacancy}</b>.\n"
        "Пришлите файл PDF, DOC/DOCX или TXT с резюме."
    )
    await cb.answer()


@router.message(F.document)
async def handle_document(m: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    vacancy = data.get("vacancy")
    if not vacancy:
        return await m.answer("Сначала выберите вакансию через /start.")

    ext = pathlib.Path(m.document.file_name or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        return await m.answer(MSG_FMT_UNSUPPORTED)

    processing_msg = await m.answer(MSG_PROCESSING)

    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    target = pathlib.Path(setup.data_dir) / f"{ts}_{uuid4().hex}{ext}"
    target.parent.mkdir(parents=True, exist_ok=True)
    file_info = await m.bot.get_file(m.document.file_id)
    await m.bot.download_file(file_info.file_path, destination=target)

    resume_txt = extract_text(str(target))
    meta = await process_resume(
        file_path=str(target),
        resume_text=resume_txt,
        vacancy_name=vacancy,
        vacancy_text=VACANCIES.get(vacancy, ""),
        user_id=m.from_user.id,
    )

    if meta["rating"] < 40:
        lack = humanize_missing(meta.get("missing_experience"))
        await processing_msg.edit_text(
            f"😔 К сожалению, по вашему резюме мы видим недостаточно опыта: {lack}."
        )
        return

    await processing_msg.edit_text(MSG_SUCCESS)
    await m.answer_photo(FSInputFile(Path("data/static/thanks.png")))

    await state.update_data(
        resume_file_id=m.document.file_id,
        interview_tips=meta.get("interview_tips", ""),
    )

    await m.answer(
        "Хотите получить рекомендации для прохождения собеседования "
        "от нашего ИИ-HR-агента?",
        reply_markup=GET_TIPS_KB,
    )

    caption = build_hr_caption(vacancy, meta, m.from_user.username)
    await m.bot.send_document(
        setup.summary_chat_id,
        m.document.file_id,
        caption=caption,
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
