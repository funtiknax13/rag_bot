# CLAUDE.md

Этот файл содержит инструкции для Claude Code (claude.ai/code) при работе с данным репозиторием.

## О проекте

Telegram RAG-бот: пользователь кладёт файлы в папку `docs/` → они индексируются в векторную БД → пользователи общаются с содержимым через Telegram. Работает полностью локально через Ollama (инференс только на CPU, без GPU).

## Ограничения железа

**Intel N150, 12 ГБ RAM, Intel UHD Graphics (без дискретной GPU).**

- Инференс только на CPU — Ollama запускается без GPU-флагов.
- Практически доступны только модели до ~3B параметров. Рекомендуемые: `gemma2:2b`, `qwen2.5:1.5b`, `phi3:mini`.
- Модель для эмбеддингов: `nomic-embed-text` через Ollama.
- Держать потребление памяти минимальным — не загружать несколько больших моделей одновременно.

## Технологический стек

| Слой | Выбор |
|---|---|
| Фреймворк бота | `aiogram` 3.x (async) |
| RAG-фреймворк | `LangChain` |
| Запуск LLM | Ollama (в Docker, CPU-режим) |
| Эмбеддинги | `nomic-embed-text` через Ollama |
| Векторная БД | ChromaDB (встроенная, персистентная на диске) |
| История диалогов | SQLite (последние 10 сообщений на пользователя) |
| Типы файлов | PDF, DOCX, TXT, MD |
| Конфигурация | `.env` (все секреты и настройки) |
| Инфраструктура | Docker Compose |

## Архитектура

```
docker-compose.yml
├── ollama          # образ ollama/ollama, CPU-режим, порт 11434
└── bot             # Python-приложение (aiogram + LangChain + ChromaDB + SQLite)

src/
├── main.py         # точка входа: индексация при старте, затем запуск polling
├── bot/
│   ├── handlers.py   # /start, /help, /reindex + обработчик сообщений
│   └── middlewares.py
├── rag/
│   ├── retriever.py  # настройка ChromaDB, поиск по схожести
│   └── chain.py      # RAG-цепочка LangChain (retriever + Ollama LLM)
├── indexer/
│   └── loader.py   # поиск файлов, чанкинг, эмбеддинги, запись в Chroma
└── db/
    └── history.py  # SQLite: сохранение/загрузка последних 10 сообщений по user_id

docs/               # <-- сюда пользователи кладут файлы
data/
├── chroma/         # персистентное хранилище ChromaDB (volume-mounted)
└── history.db      # файл SQLite (volume-mounted)
```

## Ключевые поведения

**Индексация при старте:** При запуске `main.py` модуль `indexer/loader.py` сканирует `docs/`, сравнивает хэши файлов с уже проиндексированными документами в метаданных ChromaDB и индексирует только новые или изменённые файлы. Если изменений нет — ChromaDB используется как есть.

**RAG-цепочка:** Каждое сообщение пользователя → поиск top-K релевантных чанков в ChromaDB → добавление последних 10 сообщений из SQLite → отправка в Ollama LLM → возврат ответа.

**Язык ответов:** Бот отвечает на том же языке, на котором написал пользователь — это реализуется через шаблон промпта, без дополнительных усилий модели.

**Команды бота:**
- `/start` — приветствие
- `/help` — инструкция по использованию
- `/reindex` — вручную запустить переиндексацию папки `docs/`

## Структура Docker Compose

```yaml
services:
  ollama:
    image: ollama/ollama
    # без 'deploy.resources.reservations.devices' — только CPU
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  bot:
    build: .
    depends_on:
      - ollama
    env_file: .env
    volumes:
      - ./docs:/app/docs
      - ./data:/app/data
```

Модели Ollama нужно скачать вручную после первого `docker compose up`:
```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull gemma2:2b
```

## Переменные окружения (.env)

```
TELEGRAM_TOKEN=
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:1.5b
OLLAMA_EMBED_MODEL=nomic-embed-text
DOCS_PATH=/app/docs
CHROMA_PATH=/app/data/chroma
SQLITE_PATH=/app/data/history.db
TOP_K=5
HISTORY_LENGTH=10
```

## Команды разработки

```bash
# Запустить все сервисы
docker compose up --build

# Скачать модели Ollama (только первый раз)
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull gemma2:2b

# Смотреть логи бота
docker compose logs -f bot

# Принудительная переиндексация (перезапуск бота запускает индексацию при старте)
docker compose restart bot

# Запустить бота локально без Docker (требуется Ollama на хосте)
pip install -r requirements.txt
OLLAMA_BASE_URL=http://localhost:11434 python src/main.py
```

## Заметки по LangChain

- Использовать `OllamaEmbeddings` и `OllamaLLM` из `langchain_ollama` (не устаревшие обёртки из `langchain_community`).
- ChromaDB через `langchain_chroma.Chroma` с `persist_directory`, указывающим на `CHROMA_PATH`.
- История диалога: вручную добавлять отформатированную историю в промпт — не использовать классы памяти LangChain (слишком тяжёлые для этой конфигурации).
- Использовать `RecursiveCharacterTextSplitter` для чанкинга: `chunk_size=500`, `chunk_overlap=50` (подобрано под маленькие модели с ограниченным контекстным окном).

## Загрузчики файлов

Использовать загрузчики документов LangChain:
- PDF → `PyPDFLoader`
- DOCX → `Docx2txtLoader`
- TXT/MD → `TextLoader`

Отслеживать проиндексированные файлы, сохраняя `{filepath: hash}` в метаданных коллекции ChromaDB — чтобы пропускать неизменившиеся файлы при перезапуске.
