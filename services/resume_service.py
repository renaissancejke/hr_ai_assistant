from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram.types import File, FSInputFile

from bot.handlers.resume import ALLOWED_EXT, analyse_resume, extract_text
from settings.config import setup
from .vacancy_service import VacancyService
from .errors import InvalidResumeError


class ResumeService:

    THANKS_IMG = Path("data/static/thanks.png")

    @staticmethod
    def _ts() -> str:
        return dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    @classmethod
    async def _save_document(cls, bot: Bot, tg_file: File, ext: str) -> Path:
        target = Path(setup.data_dir) / f"{cls._ts()}_{tg_file.file_unique_id}{ext}"
        await bot.download(tg_file, destination=target)
        return target

    @staticmethod
    def _humanize_missing(val: Any) -> str:
        if not val:
            return "ключевых навыках"
        if isinstance(val, str):
            return val.strip().rstrip(".;,")
        if isinstance(val, (list, tuple)):
            return ", ".join(map(str, val[:3])).rstrip(".;,")
        return str(val).rstrip(".;,")

    @staticmethod
    def _looks_like_resume(text: str) -> bool:
        """проверка, что прислан не пустой лист."""
        if len(text) < 150:
            return False
        words = text.split()
        if len(words) < 10:
            return False
        url_tokens = sum(bool(re.match(r"https?://", w)) for w in words)
        return url_tokens / len(words) <= 0.5

    @classmethod
    async def evaluate(
        cls,
        bot: Bot,
        tg_file: File,
        vacancy_name: str,
        ext: str,
        telegram_user_id: int,
    ) -> dict:
        if ext not in ALLOWED_EXT:
            raise ValueError("unsupported")

        file_path = await cls._save_document(bot, tg_file, ext)

        resume_text = extract_text(str(file_path))

        if not cls._looks_like_resume(resume_text):
            raise InvalidResumeError("Файл не похож на резюме")

        vacancy_text = VacancyService.get(vacancy_name)
        meta = await analyse_resume(resume_text, vacancy_text)
        meta["file_path"] = str(file_path)
        return meta

    @classmethod
    def build_hr_caption(cls, vacancy: str, meta: dict, username: str | None) -> str:
        q = meta["interview_questions"]
        return (
            f"#{vacancy.replace(' ', '_')}\n"
            f"Кандидат подходит на {meta['rating']:.0f}%\n\n"
            f"💪 Сильные стороны: {meta['strong']}\n"
            f"📉 Слабые стороны: {meta['weak']}\n"
            f"🔗 Релевантный опыт: {meta['matched_experience']}\n"
            f"🚫 Не хватает опыта: {cls._humanize_missing(meta.get('missing_experience'))}\n"
            f"💧 «Вода»: {meta['water']}\n"
            f"⚠️ Несоответствия / подозрения: "
            f"{meta['mismatches'] or meta['suspicious']}\n\n"
            f"❓ Вопросы для собеседования:\n"
            f"• {q[0]}\n• {q[1]}\n• {q[2]}\n\n"
            f"📱 Контакт: @{username or '—'}"
        )

    @classmethod
    def thanks_photo(cls) -> FSInputFile | None:
        return FSInputFile(cls.THANKS_IMG) if cls.THANKS_IMG.exists() else None
