from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx import Document
from openai import AsyncOpenAI
from pdfminer.high_level import extract_text as pdf_text

from settings.config import setup

openai_client = AsyncOpenAI(api_key=setup.openai_api_key)
ALLOWED_EXT = {".txt", ".pdf", ".doc", ".docx"}


# извлечение текста из файла
def extract_text(path: str | Path) -> str:
    p = Path(path)
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


#  запрос к ChatGPT

PROMPT_TEMPLATE = """
Ты – опытный IT-HR. Проанализируй резюме и сравни его с вакансией
и верни JSON строго этого формата:
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

=== ВАКАНСИЯ ===
{vacancy}

=== РЕЗЮМЕ ===
{resume}
"""


async def analyse_resume(resume_text: str, vacancy_text: str) -> dict[str, Any]:
    prompt = PROMPT_TEMPLATE.format(
        resume=resume_text.strip(), vacancy=vacancy_text.strip()
    )
    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=700,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)
