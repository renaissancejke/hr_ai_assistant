import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from settings.config import setup

from bot.handlers.candidate import router as candidate_router

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s"
)


async def main():
    bot = Bot(
        setup.telegram_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(candidate_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bye!")
