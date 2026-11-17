"""Файлы эфемерид: состояние, возможности продукта, загрузка и проверка.

Модуль не зависит от интерфейса и работает в замороженной сборке (PyInstaller),
где внешнего Python нет. Файлы Swiss Ephemeris лицензированы Astrodienst
(AGPL-3.0 или коммерческая лицензия) и не входят в дистрибутив продукта.

Запуск из командной строки:
  py -3.11 -m astro_core.ephe_manager
  py -3.11 -m astro_core.ephe_manager --download
  py -3.11 -m astro_core.ephe_manager --folder D:\\Astro\\ephe
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .constants import DEFAULT_EPHE_PATH

BASE_URL = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/"
VERIFIED_AT = "2026-11-16"
TIMEOUT = 60
RETRIES = 3
CHUNK = 65536


class EpheDownloadError(RuntimeError):
    """Файл не удалось получить по сети."""


class EpheIntegrityError(RuntimeError):
    """Контрольная сумма полученного файла не совпала с проверенной."""


@dataclass(frozen=True)
class EpheFile:
    name: str
    purpose: str
    sha1: str
    size: int
    strict: bool = True


FILES = (
    EpheFile("sepl_18.se1", "Планеты Солнце-Плутон, высокая точность",
             "786702cd04506371ee6223af1ebac02d54c848b8", 484061),
    EpheFile("semo_18.se1", "Луна, высокая точность",
             "5427d9f885fd6cb9489584ade37e52c6abb4d407", 1304771),
    EpheFile("seas_18.se1", "Хирон и основные астероиды",
             "8f900cab7e557e4c41f758a6bf3a3c3967e7e3db", 223004),
    EpheFile("seorbel.txt", "Селена и Прозерпина (фиктивные тела)",
             "9edd9634bbb109666ed118835ef5efd99dca8a4c", 6119, strict=False),
)

STATE_LABELS = {
    "ok": "в порядке",
    "missing": "отсутствует",
    "changed": "сумма не совпала",
    "variant": "другая редакция (допустимо)",
}


def blob_sha1(data: bytes) -> str:
    """Контрольная сумма в формате git blob - сравнима с суммами upstream."""
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


def default_folder() -> Path:
    """Папка эфемерид по умолчанию.

    В замороженной сборке __file__ ядра указывает внутрь бандла, поэтому
    там мы ищем папку рядом с исполняемым файлом - именно туда пользователь
    или инсталлятор кладёт файлы.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "ephe"
    return Path(DEFAULT_EPHE_PATH)


def resolve_folder(folder=None, settings=None) -> Path:
    if folder is not None:
        return Path(str(folder)).expanduser()
    if settings and settings.get("ephe_path"):
        return Path(str(settings["ephe_path"])).expanduser()
    return default_folder()


def inspect_file(item: EpheFile, folder: Path) -> dict:
    path = folder / item.name
    if not path.exists():
        return {"name": item.name, "purpose": item.purpose, "state": "missing",
                "size": 0, "sha1": "", "expected_sha1": item.sha1}
    data = path.read_bytes()
    actual = blob_sha1(data)
    if actual == item.sha1:
        state = "ok"
    elif item.strict:
        state = "changed"
    else:
        state = "variant"
    return {"name": item.name, "purpose": item.purpose, "state": state,
            "size": len(data), "sha1": actual, "expected_sha1": item.sha1}


def status(folder=None, settings=None) -> list:
    target = resolve_folder(folder, settings)
    return [inspect_file(item, target) for item in FILES]


def capabilities(entries) -> dict:
    """Что реально доступно продукту при текущем наборе файлов."""
    states = {entry["name"]: entry["state"] for entry in entries}

    def present(name):
        return states.get(name) in ("ok", "variant", "changed")

    return {
        "high_precision_planets": present("sepl_18.se1") and present("semo_18.se1"),
        "chiron_and_asteroids": present("seas_18.se1"),
        "fictitious_points": present("seorbel.txt"),
    }


def summary(folder=None, settings=None) -> dict:
    entries = status(folder, settings)
    missing = [e["name"] for e in entries if e["state"] == "missing"]
    changed = [e["name"] for e in entries if e["state"] == "changed"]
    return {
        "folder": str(resolve_folder(folder, settings)),
        "files": entries,
        "capabilities": capabilities(entries),
        "missing": missing,
        "changed": changed,
        "complete": not missing and not changed,
    }


def _http_get(url, cancel=None, progress=None) -> bytes:
    last_error = None
    for attempt in range(1, RETRIES + 1):
        if cancel is not None:
            cancel()
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                total = int(response.headers.get("Content-Length") or 0)
                chunks = []
                received = 0
                while True:
                    if cancel is not None:
                        cancel()
                    chunk = response.read(CHUNK)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    received += len(chunk)
                    if progress is not None and total:
                        progress(int(received * 100 / total), f"{received}/{total} байт")
                return b"".join(chunks)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(1.5 * attempt)
    raise EpheDownloadError(f"Не удалось скачать {url}: {last_error}")


def fetch(item: EpheFile, folder=None, settings=None, progress=None, cancel=None,
          accept_upstream=False) -> Path:
    """Скачивает один файл с проверкой целостности и атомарной записью."""
    target = resolve_folder(folder, settings)
    target.mkdir(parents=True, exist_ok=True)
    data = _http_get(BASE_URL + item.name, cancel=cancel, progress=progress)
    actual = blob_sha1(data)
    if actual != item.sha1 and item.strict and not accept_upstream:
        raise EpheIntegrityError(
            f"{item.name}: контрольная сумма не совпала "
            f"(ожидалось {item.sha1[:12]}, получено {actual[:12]}). "
            f"Upstream изменился с {VERIFIED_AT} - проверьте источник.")
    path = target / item.name
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_bytes(data)
    temp.replace(path)
    return path


def download(name, **kwargs) -> Path:
    for item in FILES:
        if item.name == name:
            return fetch(item, **kwargs)
    raise KeyError(f"Неизвестный файл эфемерид: {name}")


def download_missing(folder=None, settings=None, progress=None, cancel=None,
                     accept_upstream=False) -> dict:
    report = {"downloaded": [], "skipped": [], "failed": {}}
    entries = status(folder, settings)
    catalog = {item.name: item for item in FILES}
    total = len(entries)
    for index, entry in enumerate(entries):
        if entry["state"] in ("ok", "variant"):
            report["skipped"].append(entry["name"])
        else:
            try:
                fetch(catalog[entry["name"]], folder, settings,
                      progress=None, cancel=cancel, accept_upstream=accept_upstream)
                report["downloaded"].append(entry["name"])
            except (EpheDownloadError, EpheIntegrityError) as exc:
                report["failed"][entry["name"]] = str(exc)
        if progress is not None:
            progress(int((index + 1) * 100 / total), entry["name"])
    return report


def apply_path(folder=None, settings=None) -> None:
    """Заставляет Swiss Ephemeris перечитать файлы и сбрасывает кэш расчётов."""
    target = resolve_folder(folder, settings)
    try:
        import swisseph as swe
    except ImportError:
        return  # библиотека недоступна - перечитывать нечего
    close = getattr(swe, "close", None)
    if callable(close):
        close()  # сбрасывает открытые Handles файлов эфемерид
    from . import ephemeris
    ephemeris.initialize_ephemeris({"ephe_path": str(target)})


def _print_report(info: dict) -> None:
    print(f"Папка эфемерид: {info['folder']}")
    print("=" * 78)
    for entry in info["files"]:
        mark = "ok " if entry["state"] == "ok" else "!! "
        print(f"[{mark}] {entry['name']:<16} {STATE_LABELS[entry['state']]:<28} "
              f"{entry['purpose']}")
    print("-" * 78)
    caps = info["capabilities"]
    print("Высокая точность планет и Луны: " +
          ("да" if caps["high_precision_planets"] else "НЕТ - расчёт по Moshier, точность ниже"))
    print("Хирон и астероиды:              " +
          ("да" if caps["chiron_and_asteroids"] else "НЕТ - объекты недоступны"))
    print("Селена и Прозерпина:            " +
          ("да" if caps["fictitious_points"] else "НЕТ - точки недоступны"))
    print("=" * 78)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Файлы эфемерид Astro Processor")
    parser.add_argument("--folder", help="папка с файлами эфемерид")
    parser.add_argument("--download", action="store_true", help="скачать недостающее")
    parser.add_argument("--accept-upstream", action="store_true",
                        help="принять файл, если upstream изменился")
    args = parser.parse_args(argv)

    info = summary(args.folder)
    _print_report(info)
    if not args.download:
        if not info["complete"]:
            print("Получение файлов: py -3.11 -m astro_core.ephe_manager --download")
            return 1
        return 0

    def report(percent, message):
        print(f"  {percent:3d}% {message}")

    result = download_missing(args.folder, progress=report,
                              accept_upstream=args.accept_upstream)
    print(f"Скачано: {result['downloaded']}")
    print(f"Пропущено (уже есть): {result['skipped']}")
    if result["failed"]:
        for name, error in result["failed"].items():
            print(f"Ошибка {name}: {error}")
    apply_path(args.folder)
    _print_report(summary(args.folder))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
