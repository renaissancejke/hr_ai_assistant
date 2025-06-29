from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from docx import Document
from openai import AsyncOpenAI, OpenAIError
from pdfminer.high_level import extract_text as pdf_text

from settings.config import setup

openai_client = AsyncOpenAI(api_key=setup.openai_api_key, timeout=60)
ALLOWED_EXT = {".txt", ".pdf", ".doc", ".docx"}

PROMPT_TEMPLATE = """
Ты – опытный IT-HR. Проанализируй резюме и сравни его с вакансией и верни JSON строго этого формата:
{{
  "rating": 0-100,                       # целое число, рейтинг общего соответствия резюме и вакансии
  "strong": "ключевые сильные стороны кандидата",
  "weak": "главные слабые стороны кандидата",
  "matched_experience": "что из опыта соответствует роли",
  "missing_experience": "что из опыта не соответствует роли",
  "water": "есть ли лишняя 'вода' в резюме (коротко)",
  "mismatches": "несоответствия",
  "suspicious": "подозрительные моменты",
  "interview_questions": ["вопрос 1", "вопрос 2", "вопрос 3"],
  "interview_tips": "конкретные рекомендации к собеседованию (указать конкретные вопросы, которые стоит подготовить, вопросов дожно быть 6, минимум 35 слов )  (≤500 симв.)"
}}

Вакансия:
{vacancy}

Резюме:
{resume}
"""


def extract_text(file_path: str | Path) -> str:
    p = Path(file_path)
    if p.suffix.lower() not in ALLOWED_EXT:
        raise ValueError("Неподдерживаемый тип файла")

    match p.suffix.lower():
        case ".txt":
            return p.read_text(encoding="utf-8", errors="ignore")
        case ".pdf":
            return pdf_text(str(p))
        case ".doc" | ".docx":
            doc = Document(str(p))
            return "\n".join(par.text for par in doc.paragraphs)
        case _:
            return ""


async def analyse_resume(text: str, vacancy: str) -> dict[str, Any]:
    prompt = PROMPT_TEMPLATE.format(vacancy=vacancy, resume=text)

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI error: {exc}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Не удалось разобрать JSON из ответа OpenAI:\n{raw[:400]}...")
