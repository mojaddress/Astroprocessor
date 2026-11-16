"""Получение и проверка файлов Swiss Ephemeris локально (в репозитории их нет).

Запуск:
  py -3.11 fetch_ephe.py            скачать недостающее
  py -3.11 fetch_ephe.py --check    только проверить локальные файлы
  py -3.11 fetch_ephe.py --force    перекачать всё заново

Источник: официальный публичный репозиторий Swiss Ephemeris (aloistr/swisseph),
указанный Astrodienst как место распространения файлов эфемерид.
Целостность: git blob SHA1, сверенный с upstream на дату VERIFIED_AT.
Лицензия данных: Astrodienst (AGPL-3.0 или коммерческая) - см. LICENSES.md.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EPHE = ROOT / "ephe"
BASE_URL = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/"
VERIFIED_AT = "2026-11-16"
TIMEOUT = 60
RETRIES = 3

FILES = [
    {"name": "sepl_18.se1", "size": 484061,
     "sha1": "786702cd04506371ee6223af1ebac02d54c848b8",
     "purpose": "Планеты Солнце-Плутон", "strict": True},
    {"name": "semo_18.se1", "size": 1304771,
     "sha1": "5427d9f885fd6cb9489584ade37e52c6abb4d407",
     "purpose": "Луна", "strict": True},
    {"name": "seas_18.se1", "size": 223004,
     "sha1": "8f900cab7e557e4c41f758a6bf3a3c3967e7e3db",
     "purpose": "Хирон и астероиды", "strict": True},
    {"name": "seorbel.txt", "size": 6119,
     "sha1": "9edd9634bbb109666ed118835ef5efd99dca8a4c",
     "purpose": "Селена, Прозерпина (фиктивные тела)", "strict": False},
]


def blob_sha1(data: bytes) -> str:
    """Контрольная сумма в формате git blob - сравнима с SHA из upstream."""
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


def download(url: str) -> bytes:
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                return response.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_error = exc
            print(f"    попытка {attempt}/{RETRIES} не удалась: {exc}")
            if attempt < RETRIES:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Не удалось скачать {url}: {last_error}")


def check_only() -> int:
    print(f"Проверка локальных файлов эфемерид в {EPHE}")
    print("=" * 72)
    missing = 0
    for item in FILES:
        path = EPHE / item["name"]
        if not path.exists():
            print(f"[нет]  {item['name']:<16} {item['purpose']} - НЕДОСТУПНО")
            missing += 1
            continue
        actual = blob_sha1(path.read_bytes())
        if actual == item["sha1"]:
            print(f"[ok]   {item['name']:<16} сумма совпадает с upstream ({VERIFIED_AT})")
        else:
            note = "версия отличается от upstream" if not item["strict"] else "ВНИМАНИЕ: расхождение"
            print(f"[?]    {item['name']:<16} {note}: {actual[:12]}...")
    print("=" * 72)
    if missing:
        print(f"Отсутствует файлов: {missing}. Получение: py -3.11 fetch_ephe.py")
        return 1
    print("Все файлы на месте.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Файлы эфемерид Swiss Ephemeris")
    parser.add_argument("--check", action="store_true", help="только проверить локальные файлы")
    parser.add_argument("--force", action="store_true", help="перекачать существующие файлы")
    parser.add_argument("--accept-upstream", action="store_true",
                        help="принять файл, даже если upstream изменился с даты сверки")
    args = parser.parse_args()

    if args.check:
        return check_only()

    EPHE.mkdir(parents=True, exist_ok=True)
    failures = 0
    for item in FILES:
        path = EPHE / item["name"]
        if path.exists() and not args.force:
            print(f"[skip] {item['name']} уже есть (--force для перекачивания)")
            continue
        url = BASE_URL + item["name"]
        print(f"[get ] {item['name']} <- {url}")
        try:
            data = download(url)
        except RuntimeError as exc:
            print(f"[X]    {exc}")
            failures += 1
            continue

        actual = blob_sha1(data)
        if actual != item["sha1"]:
            if item["strict"] and not args.accept_upstream:
                print(f"[X]    Сумма не совпала: ожидалось {item['sha1'][:12]}..., получено {actual[:12]}...")
                print("       Upstream изменился. Проверьте источник и повторите с --accept-upstream.")
                failures += 1
                continue
            print(f"[!]    Upstream изменился с {VERIFIED_AT}: {actual[:12]}... (принимаю)")

        temp = path.with_suffix(path.suffix + ".part")
        temp.write_bytes(data)
        temp.replace(path)
        print(f"[ok]   {item['name']} сохранён ({len(data)} байт)")

    print("=" * 72)
    if failures:
        print(f"Ошибок: {failures}. Часть расчётов будет недоступна - см. ephe/README.md")
        return 1
    print("Готово. Проверка: py -3.11 fetch_ephe.py --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())