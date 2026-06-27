import asyncio
import logging

from aiogram import Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import Message

from db.history import add_message, get_history
from indexer.loader import index_docs
from rag.chain import ask

router = Router()
logger = logging.getLogger(__name__)


async def _keep_typing(message: Message):
    """Повторяет 'печатает...' каждые 4 секунды пока работает LLM."""
    while True:
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(4)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я RAG-бот.\n\n"
        "Положи файлы (PDF, DOCX, TXT, MD) в папку `docs/` и перезапусти бота или отправь /reindex.\n"
        "Затем просто задавай вопросы по содержимому документов.\n\n"
        "/help — помощь  |  /reindex — переиндексировать"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Как пользоваться:\n"
        "1. Положи файлы (PDF, DOCX, TXT, MD) в папку `docs/`\n"
        "2. Отправь /reindex или перезапусти бота\n"
        "3. Задавай вопросы — отвечу на основе документов\n\n"
        "Если ответа нет в документах — скажу об этом честно."
    )


@router.message(Command("reindex"))
async def cmd_reindex(message: Message):
    await message.answer("Начинаю переиндексацию документов...")
    try:
        await asyncio.to_thread(index_docs)
        await message.answer("Переиндексация завершена.")
    except Exception as e:
        logger.error(f"Ошибка переиндексации: {e}")
        await message.answer(f"Ошибка при индексации: {e}")


@router.message()
async def handle_message(message: Message):
    if not message.text:
        return

    user_id = message.from_user.id
    question = message.text

    history = await get_history(user_id)

    typing_task = asyncio.create_task(_keep_typing(message))
    try:
        answer = await asyncio.to_thread(ask, question, history)
    except Exception as e:
        logger.error(f"Ошибка RAG: {e}")
        answer = "Произошла ошибка при обработке запроса. Попробуй позже."
    finally:
        typing_task.cancel()

    await add_message(user_id, "user", question)
    await add_message(user_id, "assistant", answer)

    await message.answer(answer)
