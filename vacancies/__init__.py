import json
import os

from settings.config import setup

VACANCIES_FILE = setup.vacancies_file


def _load():
    if os.path.exists(VACANCIES_FILE):
        with open(VACANCIES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


VACANCIES = _load()
