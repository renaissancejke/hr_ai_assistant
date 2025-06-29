from __future__ import annotations

import logging
import pathlib
import uuid
from typing import Dict

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Document,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.utils.resume_tools import (
    analyse_resume,
    extract_text,
)
from services import VacancyService
from settings.config import setup

router = Router(name="resume_fsm")
log = logging.getLogger(__name__)

_tips_cache: Dict[str, str] = {}


class ResumeFSM(StatesGroup):
    waiting_for_file = State()


def _humanize_missing(text: str | None) -> str:
    return text.strip() if text and text.strip() else "—"


@router.message(ResumeFSM.waiting_for_file, F.document)
async def handle_resume(m: Message, state: FSMContext) -> None:
    vac_id = (await state.get_data()).get("vacancy_id")
    processing = await m.answer("⏳ Обрабатываем резюме…")

    doc: Document = m.document
    ext = pathlib.Path(doc.file_name or "").suffix.lower()
    if ext not in {".txt", ".pdf", ".doc", ".docx"}:
        await processing.edit_text("Поддерживаются только PDF, DOC/DOCX или TXT.")
        return

    dst = pathlib.Path(setup.data_dir) / f"{uuid.uuid4().hex}{ext}"
    try:
        tg_file = await m.bot.get_file(doc.file_id)
        await m.bot.download_file(tg_file.file_path, destination=str(dst))
    except Exception as exc:
        log.exception("download_file failed")
        await processing.edit_text(f"Не удалось скачать файл: {exc}")
        return

    try:
        cv_text = extract_text(dst)
    except Exception as exc:
        log.exception("extract_text failed")
        await processing.edit_text(f"Не удалось прочитать файл: {exc}")
        return

    vacancy = await VacancyService.by_id(vac_id)
    if not vacancy:
        await processing.edit_text("Вакансия не найдена.")
        await state.clear()
        return

    try:
        meta = await analyse_resume(cv_text, vacancy.description or vacancy.title)
    except Exception as exc:
        log.exception("analyse_resume failed")
        await processing.edit_text(f"Ошибка обработки: {exc}")
        await state.clear()
        return

    rating = float(meta.get("rating", 0))

    if rating >= 40:
        token = uuid.uuid4().hex
        _tips_cache[token] = meta.get("interview_tips", "—")

        caption = (
            "Спасибо! Мы свяжемся с вами после рассмотрения вашего резюме.\n\n"
            'Подпишитесь на наш канал <a href="https://t.me/rakestep/">ICE breaker</a>, '
            "чтобы не пропустить тренды и новости из мира ИИ, финтеха и блокчейна."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 Получить советы", callback_data=f"tips_{token}"
                    ),
                    InlineKeyboardButton(
                        text="Не нужно", callback_data=f"tips_no_{token}"
                    ),
                ]
            ]
        )
        await m.answer_photo(
            photo=FSInputFile("data/static/thanks_rake.png"),
            caption=caption,
            reply_markup=kb,
        )
        await processing.delete()
    else:
        await processing.edit_text(
            "К сожалению, ваш опыт пока недостаточен для этой вакансии."
        )

    await state.clear()

    if getattr(setup, "summary_chat_id", None):
        vac_tag = vacancy.title.replace(" ", "_")
        qs = meta.get("interview_questions", []) + ["—", "—", "—"]
        username = m.from_user.username or "—"

        summary = (
            f"#{vac_tag}\n"
            f"Кандидат подходит на {rating:.0f}%\n\n"
            f"💪 Сильные стороны: {meta.get('strong', '—')}\n"
            f"📉 Слабые стороны: {meta.get('weak', '—')}\n"
            f"🔗 Релевантный опыт: {meta.get('matched_experience', '—')}\n"
            f"🚫 Не хватает опыта: {_humanize_missing(meta.get('missing_experience'))}\n"
            f"💧 «Вода»: {meta.get('water', '—')}\n"
            f"⚠️ Несоответствия / подозрения: "
            f"{meta.get('mismatches') or meta.get('suspicious') or '—'}\n\n"
            f"❓ Вопросы:\n• {qs[0]}\n• {qs[1]}\n• {qs[2]}\n\n"
            f"📱 @{username}"
        )
        try:
            await m.bot.send_message(setup.summary_chat_id, summary)
        except Exception:
            pass


@router.callback_query(F.data.startswith("tips_no_"))
async def skip_tips(cb: CallbackQuery) -> None:
    try:
        await cb.message.edit_reply_markup(reply_markup=None)  # убираем кнопки
    except Exception:
        pass

    await cb.message.answer("Хорошо, всего доброго!")
    _tips_cache.pop(cb.data.split("_", 2)[2], None)
    await cb.answer()


@router.callback_query(F.data.startswith("tips_"))
async def send_tips(cb: CallbackQuery) -> None:
    try:
        await cb.message.edit_reply_markup(reply_markup=None)  # убираем кнопки
    except Exception:
        pass

    token = cb.data.split("_", 1)[1]
    tips = _tips_cache.pop(token, None)
    if tips:
        await cb.message.answer(f"💡 Советы от AI-ассистента:\n\n{tips}")
    else:
        await cb.message.answer("Советы уже выданы или токен не найден.")
    await cb.answer()


@router.message(ResumeFSM.waiting_for_file, F.text.casefold() == "/cancel")
async def cancel(m: Message, state: FSMContext) -> None:
    await m.answer("Отклик отменён.")
    await state.clear()
