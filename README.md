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

## Провайдеры LLM

Бот поддерживает три режима работы — переключение через `LLM_PROVIDER` в `.env`:

| `LLM_PROVIDER` | Описание | Что нужно |
|---|---|---|
| `ollama` | Локальная модель через Ollama | Docker + скачать модель |
| `openai` | OpenAI API (GPT-4o, GPT-4o-mini и др.) | `OPENAI_API_KEY` |
| `deepseek` | DeepSeek API (дешевле OpenAI, сравнимое качество) | `DEEPSEEK_API_KEY` |

> Эмбеддинги (`nomic-embed-text`) всегда работают локально через Ollama — сервис `ollama` в Docker нужен при любом провайдере.

**Пример для OpenAI:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Пример для DeepSeek:**
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat
```

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

## Поддерживаемые локальные модели

Все модели запускаются через Ollama. Смена модели — одна строка в `.env`:
```bash
docker compose exec ollama ollama pull <модель>
# OLLAMA_MODEL=<модель> в .env
docker compose up -d bot
```

---

### CPU-only (без видеокарты)

Минимум: **4 ГБ RAM** (свободной, под модель + ОС + эмбеддинги)

| Модель | Параметры | Мин. RAM | Качество | Примечание |
|---|---|---|---|---|
| `qwen2.5:1.5b` | 1.5B | 4 ГБ | ⭐⭐ | Самый быстрый, базовое качество |
| `gemma2:2b` | 2B | 4 ГБ | ⭐⭐⭐ | Лучше рассуждает, чем qwen 1.5b |
| `llama3.2:3b` | 3B | 6 ГБ | ⭐⭐⭐ | Хорош для многоязычных документов |
| `phi3:mini` ✅ | 3.8B | 6 ГБ | ⭐⭐⭐⭐ | Лучшее следование инструкциям в своём классе |
| `phi4-mini` | 3.8B | 6 ГБ | ⭐⭐⭐⭐ | Новее phi3:mini, чуть точнее |
| `mistral:7b` | 7B | 10 ГБ | ⭐⭐⭐⭐ | Высокое качество, медленно на CPU |

---

### Бюджетная видеокарта (6–8 ГБ VRAM)

GTX 1060 6GB / RTX 2060 / RTX 3060 / RX 6600 XT и аналоги

| Модель | Параметры | Мин. VRAM | Качество | Примечание |
|---|---|---|---|---|
| `mistral:7b` | 7B | 6 ГБ | ⭐⭐⭐⭐ | Быстро на GPU, хорошее качество |
| `qwen2.5:7b` | 7B | 6 ГБ | ⭐⭐⭐⭐ | Сильный для структурированных текстов |
| `llama3.1:8b` | 8B | 8 ГБ | ⭐⭐⭐⭐ | Один из лучших в классе 8B |
| `gemma2:9b` | 9B | 8 ГБ | ⭐⭐⭐⭐ | Отличное качество рассуждений |

---

### Средняя видеокарта (10–16 ГБ VRAM)

RTX 3080 / RTX 4070 / RTX 3080 Ti / RX 7900 XT и аналоги

| Модель | Параметры | Мин. VRAM | Качество | Примечание |
|---|---|---|---|---|
| `phi4` | 14B | 10 ГБ | ⭐⭐⭐⭐⭐ | Очень точное следование инструкциям |
| `qwen2.5:14b` | 14B | 10 ГБ | ⭐⭐⭐⭐⭐ | Отличный для многоязычного RAG |
| `deepseek-r1:14b` | 14B | 10 ГБ | ⭐⭐⭐⭐⭐ | Модель с цепочкой рассуждений |
| `mistral-nemo:12b` | 12B | 10 ГБ | ⭐⭐⭐⭐ | Быстрый и точный |
| `llama3.3:70b` (Q2) | 70B | 16 ГБ | ⭐⭐⭐⭐⭐ | Топовое качество при сильной квантизации |

---

### Топовая видеокарта (24+ ГБ VRAM)

RTX 3090 / RTX 4090 / RTX 4080 Super / A100 и аналоги

| Модель | Параметры | Мин. VRAM | Качество | Примечание |
|---|---|---|---|---|
| `gemma2:27b` | 27B | 18 ГБ | ⭐⭐⭐⭐⭐ | Высочайшее качество от Google |
| `qwen2.5:32b` | 32B | 22 ГБ | ⭐⭐⭐⭐⭐ | Один из лучших открытых в своём классе |
| `deepseek-r1:32b` | 32B | 22 ГБ | ⭐⭐⭐⭐⭐ | Рассуждения уровня GPT-4 |
| `llama3.3:70b` | 70B | 48 ГБ | ⭐⭐⭐⭐⭐ | Максимальное качество из открытых |

---

> **Для GPU:** в `docker-compose.yml` нужно добавить секцию `deploy.resources.reservations.devices` для сервиса `ollama`. Ollama автоматически определяет видеокарту и использует CUDA/ROCm.

## Стек

- **Бот:** aiogram 3.x
- **RAG:** LangChain + ChromaDB
- **LLM:** Ollama (CPU-режим, без GPU)
- **История:** SQLite
