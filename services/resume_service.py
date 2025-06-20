from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict

from aiogram.types import Document, Message

from bot.handlers.resume import extract_text, process_resume
from settings.config import setup
from services import VacancyService


class ResumeService:
    """
    Загрузка файла из Telegram, парсинг текста и запуск ChatGPT-анализа.
    """

    uploads_dir = Path(setup.data_dir) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def process_telegram_file(message: Message, *, vacancy_id: int) -> Dict:
        doc: Document = message.document
        ext = Path(doc.file_name or "").suffix.lower()
        file_path = ResumeService.uploads_dir / f"{uuid.uuid4().hex}{ext}"

        # скачиваем файл
        await doc.download(destination=file_path)

        # читаем текст
        resume_text = extract_text(str(file_path))

        vacancy = await VacancyService.by_id(vacancy_id)
        vacancy_name = vacancy.title if vacancy else "Vacancy"
        vacancy_text = (
            (vacancy.description or vacancy.title) if vacancy else vacancy_name
        )

        # анализ ChatGPT
        analysis = await process_resume(
            file_path=str(file_path),
            resume_text=resume_text,
            vacancy_name=vacancy_name,
            vacancy_text=vacancy_text,
            user_id=message.from_user.id,
        )
        return analysis
