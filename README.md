# RAG-бот для Telegram

Telegram-бот с RAG (Retrieval-Augmented Generation): кидай файлы в папку `docs/` → они индексируются → общайся с их содержимым через Telegram. Работает полностью локально через Ollama.

## Требования

- Docker + Docker Compose
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

## Быстрый старт

**1. Настройка окружения**
```bash
cp .env.example .env
# Открой .env и вставь TELEGRAM_TOKEN
```

**2. Запуск**
```bash
docker compose up --build -d
```

**3. Скачать модели (один раз)**
```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull phi3:mini
```

**4. Перезапустить бота**
```bash
docker compose up -d bot
```

## Использование

Положи файлы (PDF, DOCX, TXT, MD) в папку `docs/` и отправь боту `/reindex`.  
После этого просто задавай вопросы по содержимому документов.

**Команды бота:**
- `/start` — начало работы
- `/help` — справка
- `/reindex` — переиндексировать папку `docs/`

## Настройки (.env)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `TELEGRAM_TOKEN` | Токен бота от BotFather | — |
| `OLLAMA_MODEL` | Модель LLM | `phi3:mini` |
| `OLLAMA_EMBED_MODEL` | Модель эмбеддингов | `nomic-embed-text` |
| `TOP_K` | Кол-во чанков для контекста | `5` |
| `HISTORY_LENGTH` | Кол-во сообщений в истории | `10` |
| `CHUNK_SIZE` | Размер чанка при индексации | `300` |
| `CHUNK_OVERLAP` | Перекрытие чанков | `50` |

## Стек

- **Бот:** aiogram 3.x
- **RAG:** LangChain + ChromaDB
- **LLM:** Ollama (CPU-режим, без GPU)
- **История:** SQLite
