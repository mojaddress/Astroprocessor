"""Тесты LRU-кэша эфемерид: попадания, вытеснение, инвалидация, ошибки, потоки."""
import threading

import pytest

from astro_core.ephemeris_cache import DEFAULT_FLAGS, EphemerisCache


class FakeBackend:
    """Детерминированная подмена swisseph со счётчиком вызовов."""

    def __init__(self, fail: bool = False, err: bool = False):
        self.calc_calls = 0
        self.houses_calls = 0
        self.fail = fail
        self.err = err

    def calc_ut(self, jd, body, flags):
        self.calc_calls += 1
        if self.fail:
            raise RuntimeError("backend failure")
        retflag = -1 if self.err else flags
        return ((jd % 360, 0.0, 1.0, 1.0, 0.0, 0.0), retflag)

    def houses_ex(self, jd, lat, lon, hsys):
        self.houses_calls += 1
        return (tuple(range(12)), (jd % 360, 0.0, 0.0, 0.0))


def make(maxsize=8, **kw):
    backend = FakeBackend(**kw)
    return EphemerisCache(backend=backend, maxsize=maxsize), backend


def test_miss_then_hit():
    cache, backend = make()
    first = cache.calc_ut(2451545.0, 0)
    second = cache.calc_ut(2451545.0, 0)
    assert first == second
    assert backend.calc_calls == 1
    s = cache.stats()
    assert s["hits"] == 1 and s["misses"] == 1 and s["hit_rate"] == 0.5


def test_exact_jd_is_not_rounded():
    cache, backend = make()
    cache.calc_ut(2451545.0, 0)
    cache.calc_ut(2451545.000001, 0)
    assert backend.calc_calls == 2  # разные jd - разные записи, точность сохранена


def test_body_and_flags_are_part_of_key():
    cache, backend = make()
    cache.calc_ut(2451545.0, 0)
    cache.calc_ut(2451545.0, 1)
    cache.calc_ut(2451545.0, 0, DEFAULT_FLAGS | 4)
    assert backend.calc_calls == 3


def test_lru_eviction_order():
    cache, backend = make(maxsize=2)
    cache.calc_ut(1.0, 0)
    cache.calc_ut(2.0, 0)
    cache.calc_ut(1.0, 0)      # освежаем 1.0
    cache.calc_ut(3.0, 0)      # вытесняет 2.0
    assert cache.size() == 2
    assert cache.stats()["evictions"] == 1
    cache.calc_ut(1.0, 0)      # всё ещё в кэше
    assert backend.calc_calls == 3
    cache.calc_ut(2.0, 0)      # был вытеснен - новый вызов
    assert backend.calc_calls == 4


def test_maxsize_bound():
    cache, _ = make(maxsize=3)
    for i in range(50):
        cache.calc_ut(float(i), 0)
    assert cache.size() <= 3


def test_invalid_maxsize():
    with pytest.raises(ValueError):
        EphemerisCache(backend=FakeBackend(), maxsize=0)


def test_clear_and_reset_stats():
    cache, backend = make()
    cache.calc_ut(1.0, 0)
    cache.clear()
    assert cache.size() == 0
    cache.calc_ut(1.0, 0)
    assert backend.calc_calls == 2
    cache.reset_stats()
    s = cache.stats()
    assert s["hits"] == 0 and s["misses"] == 0


def test_context_change_invalidates():
    cache, backend = make()
    cache.set_context(ephe_path="ephe", zodiac="tropical")
    cache.calc_ut(1.0, 0)
    cache.set_context(ephe_path="ephe", zodiac="sidereal")
    assert cache.size() == 0
    cache.calc_ut(1.0, 0)
    assert backend.calc_calls == 2


def test_exception_is_not_cached():
    cache, backend = make(fail=True)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            cache.calc_ut(1.0, 0)
    assert backend.calc_calls == 3
    assert cache.stats()["errors"] == 3
    assert cache.size() == 0


def test_error_retflag_is_not_cached():
    cache, backend = make(err=True)
    cache.calc_ut(1.0, 0)
    cache.calc_ut(1.0, 0)
    assert backend.calc_calls == 2
    assert cache.size() == 0


def test_houses_cached_by_all_params():
    cache, backend = make()
    cache.houses_ex(2451545.0, 55.75, 37.61, b"P")
    cache.houses_ex(2451545.0, 55.75, 37.61, b"P")
    assert backend.houses_calls == 1
    cache.houses_ex(2451545.0, 55.75, 37.61, b"K")
    cache.houses_ex(2451545.0, 55.76, 37.61, b"P")
    assert backend.houses_calls == 3


def test_thread_safety_smoke():
    cache, backend = make(maxsize=64)
    errors = []

    def worker():
        try:
            for i in range(200):
                cache.calc_ut(float(i % 32), i % 4)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    s = cache.stats()
    assert s["hits"] + s["misses"] == 8 * 200
    assert cache.size() <= 64