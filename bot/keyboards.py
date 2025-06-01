from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from vacancies import VACANCIES


MAIN_REPLY_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="👀 Посмотреть вакансии")]],
    resize_keyboard=True,
    is_persistent=True,
)


def post_upload_kb() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
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

    if VACANCIES:
        rows = [
            [InlineKeyboardButton(text=v, callback_data=f"vac|{v}")] for v in VACANCIES
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="Нет актуальных вакансий", callback_data="none")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
