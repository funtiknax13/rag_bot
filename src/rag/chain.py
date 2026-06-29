import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from rag.retriever import retrieve

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

_llm = None


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        _llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI
        _llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1",
        )

    else:  # ollama (default)
        from langchain_ollama import ChatOllama
        _llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "phi3:mini"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        )

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
    chain = _get_llm() | StrOutputParser()
    return chain.invoke(prompt)
