import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.handlers.candidate import router as candidate_router
from settings.config import setup

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s",
)


async def main() -> None:
    bot = Bot(
        setup.telegram_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(candidate_router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="начать работу"),
            BotCommand(command="info", description="как пользоваться ботом"),
        ]
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bye!")
