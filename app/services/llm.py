import requests

from app.core.config import settings

CHAT_MODEL = "openrouter/free"
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_answer(question: str, context_chunks: list[str]) -> str:
    context_text = "\n\n---\n\n".join(context_chunks)

    system_prompt = (
        "You are an assistant answering questions about London urban planning "
        "and geography, based on the London Plan 2021. Use ONLY the provided "
        "context to answer. If the context doesn't contain the answer, say so "
        "clearly instead of guessing."
    )

    user_prompt = f"Context:\n{context_text}\n\nQuestion: {question}"

    response = requests.post(
        CHAT_URL,
        headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
