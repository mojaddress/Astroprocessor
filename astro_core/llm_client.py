"""
Опциональный LLM-клиент (итерация 23, гибридный вариант C).

Конфигурация ТОЛЬКО через окружение / .env (Роль §12):
ASTRO_LLM_URL, ASTRO_LLM_MODEL, ASTRO_LLM_API_KEY.
Без конфигурации продукт работает полностью на локальной базе.
Секреты не логируются и не попадают в сообщения об ошибках.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

_ENV_LOADED = False
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = (
    "Ты — опытный консультативный астролог классической традиции. "
    "Отвечай по-русски, структурно, без гарантий и выдуманных фактов; "
    "неуверенные выводы помечай как предположения.")


def _load_dotenv():
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    path = PROJECT_ROOT / ".env"
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


def llm_config():
    """Возвращает словарь конфигурации LLM или None, если LLM не настроена."""
    _load_dotenv()
    url = os.environ.get("ASTRO_LLM_URL", "").strip()
    model = os.environ.get("ASTRO_LLM_MODEL", "").strip()
    key = os.environ.get("ASTRO_LLM_API_KEY", "").strip()
    if not url or not model:
        return None
    local = url.startswith(("http://localhost", "http://127.0.0.1"))
    if not key and not local:
        return None
    return {"url": url, "model": model, "key": key or "local"}


def is_llm_available() -> bool:
    return llm_config() is not None


def ask_llm(user_prompt, system_prompt=SYSTEM_PROMPT, timeout=90):
    """Возвращает (ok, текст). Без конфигурации сетевых вызовов нет."""
    cfg = llm_config()
    if not cfg:
        return False, ("LLM не настроена: не заданы ASTRO_LLM_URL/ASTRO_LLM_MODEL "
                       "(и ASTRO_LLM_API_KEY для удалённого провайдера).")
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }
    headers = {"Content-Type": "application/json"}
    if cfg["key"] != "local":
        headers["Authorization"] = f"Bearer {cfg['key']}"
    req = urllib.request.Request(
        cfg["url"], data=json.dumps(payload).encode("utf-8"),
        headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return True, text
    except urllib.error.HTTPError as e:
        return False, f"Провайдер вернул HTTP {e.code}. Проверьте ключ и имя модели в .env."
    except urllib.error.URLError:
        return False, "Провайдер недоступен (сеть). Проверьте интернет и ASTRO_LLM_URL."
    except (KeyError, IndexError, ValueError):
        return False, "Провайдер вернул ответ неожиданного формата."
    except Exception as e:
        return False, f"Ошибка запроса LLM: {type(e).__name__}."
