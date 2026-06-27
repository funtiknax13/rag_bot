import os

from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

from rag.retriever import retrieve

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

_PROMPT = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=(
        "Ты — помощник, который отвечает ТОЛЬКО на основе текста из раздела «Контекст».\n"
        "Правила:\n"
        "- Не добавляй ничего от себя и не делай выводов, которых нет в контексте.\n"
        "- Если в контексте написано «нельзя» — отвечай «нельзя». Если «можно» — «можно». Передавай смысл точно.\n"
        "- Если ответа нет в контексте — скажи: «В документах нет информации по этому вопросу».\n"
        "- Отвечай на том же языке, на котором задан вопрос.\n"
        "\n"
        "{history}"
        "Контекст:\n{context}\n"
        "\n"
        "Вопрос: {question}\n"
        "Ответ:"
    ),
)

_llm: OllamaLLM | None = None


def _get_llm() -> OllamaLLM:
    global _llm
    if _llm is None:
        _llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    return _llm


def ask(question: str, history: list[dict]) -> str:
    chunks = retrieve(question)
    context = "\n\n".join(chunks) if chunks else "Документы не найдены."

    history_text = ""
    if history:
        lines = [
            f"{'Пользователь' if m['role'] == 'user' else 'Ассистент'}: {m['content']}"
            for m in history
        ]
        history_text = "История диалога:\n" + "\n".join(lines) + "\n\n"

    prompt = _PROMPT.format(history=history_text, context=context, question=question)
    return _get_llm().invoke(prompt)
