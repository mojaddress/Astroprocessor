"""Тесты интерпретаций и LLM-конфига (итерация 23). Без сети."""

from astro_core import llm_client
from astro_core.interpretations import (
    format_natal_profile, natal_profile, summarize_natal,
)

FAKE = {
    "birth": {"name": "Тест"},
    "planets": [
        {"name": "Sun", "sign": "Leo", "house": 5, "longitude": 120.0},
        {"name": "Moon", "sign": "Cancer", "house": 4, "longitude": 100.0},
        {"name": "Mercury", "sign": "Virgo", "house": 6, "longitude": 150.0},
    ],
    "additional_points": [{"name": "ASC", "sign": "Sagittarius", "longitude": 240.0}],
    "aspects": [],
}


def test_natal_profile_traits_and_professions():
    prof = natal_profile(FAKE)
    assert prof["traits"]
    assert prof["professions"]


def test_format_natal_profile_text():
    text = format_natal_profile(FAKE)
    assert "Подходящие сферы деятельности" in text
    assert "Черты характера" in text


def test_summarize_natal_sections():
    text = summarize_natal(FAKE)
    assert "Портрет" in text
    assert "Солнце" in text


def test_llm_config_none_without_env(monkeypatch):
    for k in ("ASTRO_LLM_URL", "ASTRO_LLM_MODEL", "ASTRO_LLM_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    assert llm_client.llm_config() is None
    ok, msg = llm_client.ask_llm("проверка")
    assert not ok
    assert "LLM" in msg


def test_llm_config_local_without_key(monkeypatch):
    monkeypatch.setenv("ASTRO_LLM_URL", "http://localhost:11434/v1/chat/completions")
    monkeypatch.setenv("ASTRO_LLM_MODEL", "llama3.1")
    monkeypatch.delenv("ASTRO_LLM_API_KEY", raising=False)
    cfg = llm_client.llm_config()
    assert cfg is not None
    assert cfg["key"] == "local"


def test_llm_config_remote_requires_key(monkeypatch):
    monkeypatch.setenv("ASTRO_LLM_URL", "https://example.com/v1/chat/completions")
    monkeypatch.setenv("ASTRO_LLM_MODEL", "m")
    monkeypatch.delenv("ASTRO_LLM_API_KEY", raising=False)
    assert llm_client.llm_config() is None
