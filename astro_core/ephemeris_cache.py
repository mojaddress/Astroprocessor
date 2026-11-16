"""Кэш обращений к Swiss Ephemeris: LRU с ограничением памяти и инвалидацией.

Зачем: расчёты транзитов/прогрессий/дирекций многократно спрашивают одни и те же
положения планет на одни и те же юлианские дни. Кэш убирает повторные вызовы C-библиотеки
и делает возможной плавную анимацию ползунка времени без фризов интерфейса.

Гарантии точности:
  * ключ строится по ТОЧНОМУ значению jd (без округления) - результат не меняется;
  * в ключ входят тело, флаги расчёта и контекст (путь эфемерид, сидерический режим);
  * ошибочные результаты (retflag < 0) и исключения не кэшируются.

Потокобезопасность: все операции под RLock (пригодено для расчётов в QThread).
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any

# FLG_SWIEPH (2) | FLG_SPEED (256) - значения из Swiss Ephemeris.
DEFAULT_FLAGS = 258
DEFAULT_MAXSIZE = 8192
ERR_FLAG = -1


class EphemerisCache:
    """LRU-кэш поверх бэкенда эфемерид (swisseph или тестовая подмена)."""

    def __init__(self, backend: Any = None, maxsize: int = DEFAULT_MAXSIZE,
                 context: dict | None = None) -> None:
        if int(maxsize) < 1:
            raise ValueError("maxsize должен быть >= 1")
        self._backend = backend if backend is not None else _load_backend()
        self._maxsize = int(maxsize)
        self._lock = threading.RLock()
        self._stores: dict[str, OrderedDict] = {"calc": OrderedDict(), "houses": OrderedDict()}
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._errors = 0
        self._context = self._normalize_context(context or {})

    @staticmethod
    def _normalize_context(context: dict) -> tuple:
        return tuple(sorted((str(k), repr(v)) for k, v in context.items()))

    @property
    def maxsize(self) -> int:
        return self._maxsize

    def set_context(self, **context: Any) -> None:
        """Смена контекста (путь эфемерид, сидерический режим) сбрасывает кэш."""
        new = self._normalize_context(context)
        with self._lock:
            if new != self._context:
                self._context = new
                self._clear_locked()

    def clear(self) -> None:
        with self._lock:
            self._clear_locked()

    def _clear_locked(self) -> None:
        for store in self._stores.values():
            store.clear()

    def reset_stats(self) -> None:
        with self._lock:
            self._hits = self._misses = self._evictions = self._errors = 0

    def size(self) -> int:
        with self._lock:
            return sum(len(store) for store in self._stores.values())

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "errors": self._errors,
                "size": self.size(),
                "maxsize": self._maxsize,
                "hit_rate": (self._hits / total) if total else 0.0,
            }

    def _lookup(self, store_name: str, key: tuple):
        store = self._stores[store_name]
        with self._lock:
            if key in store:
                store.move_to_end(key)
                self._hits += 1
                return True, store[key]
            self._misses += 1
            return False, None

    def _store(self, store_name: str, key: tuple, value: Any) -> None:
        store = self._stores[store_name]
        with self._lock:
            store[key] = value
            store.move_to_end(key)
            while len(store) > self._maxsize:
                store.popitem(last=False)
                self._evictions += 1

    def calc_ut(self, jd: float, body: int, flags: int = DEFAULT_FLAGS):
        """Кэшированный аналог swe.calc_ut(jd, body, flags)."""
        key = (float(jd), int(body), int(flags), self._context)
        found, value = self._lookup("calc", key)
        if found:
            return value
        try:
            result = self._backend.calc_ut(float(jd), int(body), int(flags))
        except Exception:
            with self._lock:
                self._errors += 1
            raise
        retflag = result[1] if isinstance(result, tuple) and len(result) > 1 else 0
        if isinstance(retflag, int) and retflag < 0:
            return result  # ошибку не кэшируем
        self._store("calc", key, result)
        return result

    def houses_ex(self, jd: float, lat: float, lon: float, hsys: bytes = b"P"):
        """Кэшированный аналог swe.houses_ex(jd, lat, lon, hsys)."""
        key = ("houses_ex", float(jd), float(lat), float(lon), bytes(hsys), self._context)
        found, value = self._lookup("houses", key)
        if found:
            return value
        try:
            result = self._backend.houses_ex(float(jd), float(lat), float(lon), bytes(hsys))
        except Exception:
            with self._lock:
                self._errors += 1
            raise
        self._store("houses", key, result)
        return result


def _load_backend():
    try:
        import swisseph as swe
    except ImportError as exc:  # pragma: no cover - зависит от окружения
        raise RuntimeError(
            "Swiss Ephemeris недоступен. Установите: py -3.11 -m pip install pyswisseph"
        ) from exc
    return swe


_default: EphemerisCache | None = None
_default_lock = threading.Lock()


def default_cache() -> EphemerisCache:
    """Ленивый синглтон кэша на реальном swisseph."""
    global _default
    with _default_lock:
        if _default is None:
            _default = EphemerisCache()
        return _default


def configure(maxsize: int = DEFAULT_MAXSIZE, **context: Any) -> EphemerisCache:
    """Создаёт/перенастраивает общий кэш (размер, путь эфемерид, режим зодиака)."""
    global _default
    with _default_lock:
        if _default is None or maxsize != _default.maxsize:
            _default = EphemerisCache(maxsize=maxsize, context=context)
        else:
            _default.set_context(**context)
        return _default


def calc_ut(jd: float, body: int, flags: int = DEFAULT_FLAGS):
    return default_cache().calc_ut(jd, body, flags)


def houses_ex(jd: float, lat: float, lon: float, hsys: bytes = b"P"):
    return default_cache().houses_ex(jd, lat, lon, hsys)


def set_context(**context: Any) -> None:
    default_cache().set_context(**context)


def clear() -> None:
    default_cache().clear()


def reset_stats() -> None:
    default_cache().reset_stats()


def stats() -> dict:
    return default_cache().stats()


def size() -> int:
    """Количество записей в общем кэше (диагностика и тесты)."""
    return default_cache().size()
