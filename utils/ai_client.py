from __future__ import annotations

import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import AI_MODEL, AI_SERVER_URL, AI_SYSTEM_PROMPT, AI_TIMEOUT_SECONDS


def _post_chat_completion(user_text: str) -> str:
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    request = Request(
        AI_SERVER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=AI_TIMEOUT_SECONDS) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        return (
            "Не удалось получить ответ от AI.\n"
            f"HTTP {exc.code}.\n"
            f"Подробности: {error_body or exc.reason}"
        )
    except URLError as exc:
        return (
            "Не удалось подключиться к локальному AI-серверу.\n"
            f"Проверьте, что сервер запущен по адресу {AI_SERVER_URL}.\n"
            f"Техническая причина: {exc.reason}"
        )
    except Exception as exc:
        return f"Ошибка при обращении к AI: {exc}"

    try:
        data = json.loads(raw_body)
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return (
            "Сервер ответил в неожиданном формате.\n"
            f"Ответ сервера: {raw_body[:1000]}"
        )


async def ask_local_ai(user_text: str) -> str:
    return await asyncio.to_thread(_post_chat_completion, user_text)
