from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path

from openai import AsyncOpenAI
from settings.config import setup

openai_client = AsyncOpenAI(api_key=setup.openai_api_key)


#  вспомогательные функции


def extract_text(file_path: str) -> str:
    p = Path(file_path)
    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    return ""


def _prompt(cv_text: str, vacancy_text: str) -> str:
    return (
        "Ты — HR-бот. Нужно оценить, насколько резюме подходит под вакансию.\n\n"
        "=== ВАКАНСИЯ ===\n"
        f"{vacancy_text}\n\n"
        "=== РЕЗЮМЕ КАНДИДАТА ===\n"
        f"{cv_text}\n\n"
        "Сначала оцени соответствие в процентах (0-100), затем одним словом тег "
        "из списка: Junior, Middle, Senior, Lead. Верни JSON: "
        '{"rating": 85, "tag": "Middle"}.'
    )


async def analyse_resume(cv_text: str, vacancy_text: str) -> dict:
    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": _prompt(cv_text, vacancy_text)}],
        temperature=0.2,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


async def process_resume(
    *,
    file_path: str,
    resume_text: str,
    vacancy_name: str,
    vacancy_text: str,
    user_id: int,
) -> dict:
    result = await analyse_resume(resume_text, vacancy_text)

    out_path = Path(file_path).with_suffix(".json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    log_line = {
        "id": uuid.uuid4().hex,
        "user_id": user_id,
        "vacancy": vacancy_name,
        "created_at": dt.datetime.utcnow().isoformat(),
        **result,
    }
    (out_path.parent / "resume_audit.log").open("a", encoding="utf-8").write(
        json.dumps(log_line, ensure_ascii=False) + "\n"
    )

    return result
