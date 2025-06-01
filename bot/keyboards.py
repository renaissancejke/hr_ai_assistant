from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from vacancies import VACANCIES

__all__ = ["POST_UPLOAD_KB", "vacancy_inline_kb"]

POST_UPLOAD_KB: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👀 Посмотреть вакансии"),
            KeyboardButton(text="📄 Моё резюме"),
        ]
    ],
    resize_keyboard=True,
    is_persistent=True,
)


def vacancy_inline_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"vac|{name}")]
        for name in VACANCIES
    ] or [[InlineKeyboardButton(text="Нет вакансий", callback_data="none")]]

    return InlineKeyboardMarkup(inline_keyboard=rows)
