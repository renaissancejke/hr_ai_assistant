from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router(name="noop")


@router.callback_query(F.data == "noop")
async def ignore_company_header(cb: CallbackQuery) -> None:

    await cb.answer()
