import datetime
import json
import logging
import os
import pathlib
import uuid
from typing import Any, Dict

import openai
from docx import Document
from openai import AsyncOpenAI
from pdfminer.high_level import extract_text as pdf_text

from db import save_record
from settings.config import Settings

settings = Settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)
logger = logging.getLogger(__name__)


def tag_by_score(score: float) -> str:
    if score >= 85:
        return "#top1"
    if score >= 70:
        return "#senior"
    if score >= 50:
        return "#middle"
    return "#junior"


async def analyse_resume(resume_text: str, vacancy_text: str) -> dict:
    prompt = f"""
Привет, ты HR it-компании. Тебе нужно проанализировать резюме кандидата. Ты должен определить общий рейтинг кандидата,
в зависимости от соответствия резюме требованиям вакансии, написать саммари по его опыту и дать советы для интрвьюера
по данному кандидату.
Вакансия:
{vacancy_text}

----
Резюме:
{resume_text}

Сравни опыт кандидата с требованиями. Верни JSON:
{{
  "rating": <0-100>,
  "summary": "...",
  "interview_tips": "..."
}}
"""
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)


async def process_resume(
    file_path: str, resume_text: str, vacancy_name: str, vacancy_text: str, user_id: int
) -> Dict[str, Any]:
    result = await analyse_resume(resume_text, vacancy_text)
    score = float(result["rating"])
    tag = tag_by_score(score)
    meta = {
        "uuid": uuid.uuid4().hex,
        "telegram_user_id": user_id,
        "vacancy": vacancy_name,
        "rating": score,
        "tag": tag,
        "summary": result["summary"],
        "interview_tips": result["interview_tips"],
        "file_path": file_path,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    save_record(meta, settings.data_dir)
    return meta


def extract_text(file_path: str) -> str:
    ext = pathlib.Path(file_path).suffix.lower()
    if ext == ".txt":
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".pdf":
        return pdf_text(file_path)
    if ext in {".doc", ".docx"}:
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Unsupported file type")
