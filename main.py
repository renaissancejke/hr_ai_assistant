# main.py
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from settings.config import setup
from bot.handlers import (
    candidate,
    company_admin,
    resume_fsm,
    start,
    noop,  # ← новый роутер-«заглушка»
)

bot = Bot(
    token=setup.telegram_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()

# порядок не критичен, но оставим группами
dp.include_router(company_admin.router)
dp.include_router(candidate.router)
dp.include_router(resume_fsm.router)
dp.include_router(start.router)
dp.include_router(noop.router)  # ← добавили

if __name__ == "__main__":
    dp.run_polling(bot)
