from __future__ import annotations
from pathlib import Path
import json

_VAC_FILE = Path("vacancies/vacancies.json")


class VacancyService:

    _cache: dict[str, str] | None = None

    @classmethod
    def _load(cls) -> dict[str, str]:
        cls._cache = json.loads(_VAC_FILE.read_text(encoding="utf-8"))
        return cls._cache

    @classmethod
    def all(cls) -> dict[str, str]:
        return cls._cache or cls._load()

    @classmethod
    def get(cls, name: str) -> str:
        return cls.all().get(name, "")
