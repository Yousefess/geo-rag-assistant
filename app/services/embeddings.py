import time
import requests

from app.core.config import settings

EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"


def get_embedding(text: str, max_retries: int = 6) -> list[float]:
    for attempt in range(max_retries):
        response = requests.post(
            EMBEDDING_URL,
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            json={"model": EMBEDDING_MODEL, "input": text},
        )
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]

        if response.status_code == 429:
            wait = min(2**attempt, 60)  # cap at 60s
            print(
                f"Rate limited, waiting {wait}s... (attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(wait)
            continue

        response.raise_for_status()

    raise RuntimeError(f"Failed to get embedding after {max_retries} retries")
