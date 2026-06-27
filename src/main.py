import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers import router
from db.history import init_db
from indexer.loader import index_docs

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def wait_for_ollama():
    url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    logger.info("Ожидание Ollama...")
    async with httpx.AsyncClient() as client:
        for attempt in range(30):
            try:
                r = await client.get(f"{url}/api/tags", timeout=5)
                if r.status_code == 200:
                    logger.info("Ollama готова")
                    return
            except Exception:
                pass
            logger.info(f"Ollama недоступна, попытка {attempt + 1}/30...")
            await asyncio.sleep(3)
    raise RuntimeError("Ollama недоступна после 90 секунд ожидания")


async def main():
    await wait_for_ollama()
    await init_db()

    logger.info("Индексация документов...")
    await asyncio.to_thread(index_docs)
    logger.info("Индексация завершена")

    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
