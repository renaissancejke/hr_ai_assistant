from __future__ import annotations

import datetime as dt
import json
import logging
import pathlib
import uuid
from typing import Any

from docx import Document
from openai import AsyncOpenAI
from pdfminer.high_level import extract_text as pdf_text

from db import save_record
from settings.config import setup

logger = logging.getLogger(__name__)
openai_client = AsyncOpenAI(api_key=setup.openai_api_key)

ALLOWED_EXT = {".txt", ".pdf", ".doc", ".docx"}
TAG_RULES = [
    (85, "#top1"),
    (70, "#senior"),
    (50, "#middle"),
]


def extract_text(file_path: str) -> str:
    suffix = pathlib.Path(file_path).suffix.lower()

    match suffix:
        case ".txt":
            return pathlib.Path(file_path).read_text(encoding="utf-8", errors="ignore")
        case ".pdf":
            return pdf_text(file_path)
        case ".doc" | ".docx":
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        case _:
            raise ValueError("Unsupported file type")


async def analyse_resume(resume: str, vacancy: str) -> dict[str, Any]:
    prompt = f"""
Ты – опытный IT-HR. Проанализируй резюме и срравни его с вакансией и верни JSON строго этого формата:
{{
  "rating": 0-100,                       # целое
  "strong": "ключевые сильные стороны кандидата",
  "weak": "главные слабые стороны кандидата",
  "matched_experience": "что из опыта соответствует роли",
  "missing_experience": "что из опыта не соответствует роли",
  "water": "есть ли лишняя 'вода' в резюме (коротко)",
  "mismatches": "несоответствия",
  "suspicious": "подозрительные моменты",
  "interview_questions": ["вопрос 1", "вопрос 2", "вопрос 3"],
  "interview_tips": "конкретные рекомендации к собеседованию (указать конкретные вопросы, которые стоит подготовить) (≤300 симв.)"
}}

Вакансия:
{vacancy}

Резюме:
{resume}
"""
    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def tag_by_score(score: float) -> str:
    for threshold, tag in TAG_RULES:
        if score >= threshold:
            return tag
    return "#junior"


async def process_resume(
    *,
    file_path: str,
    resume_text: str,
    vacancy_name: str,
    vacancy_text: str,
    user_id: int,
) -> dict[str, Any]:
    analysis = await analyse_resume(resume_text, vacancy_text)
    score = float(analysis["rating"])

    record = {
        "uuid": uuid.uuid4().hex,
        "telegram_user_id": user_id,
        "vacancy": vacancy_name,
        "rating": score,
        "tag": tag_by_score(score),
        **analysis,
        "file_path": file_path,
        "created_at": dt.datetime.utcnow().isoformat(),
    }

    save_record(record, setup.data_dir)
    return record
