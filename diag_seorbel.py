"""Проверка: подхватывает ли Swiss Ephemeris файл seorbel.txt для Селены/Прозерпины.

Запуск: py -3.11 diag_seorbel.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import swisseph as swe

from astro_core.constants import DEFAULT_EPHE_PATH


def main() -> int:
    print("Ожидаемое имя файла (swe.FICTFILE):", repr(getattr(swe, "FICTFILE", "нет константы")))
    print("Путь эфемерид:", DEFAULT_EPHE_PATH)
    folder = Path(DEFAULT_EPHE_PATH)
    print("seorbel.txt на месте:", (folder / "seorbel.txt").exists())
    print("Файлы в ephe:", sorted(p.name for p in folder.glob("seorbel*")))
    swe.set_ephe_path(str(folder))
    jd = 2451545.0
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    for body, name in ((56, "Selena (White Moon)"), (57, "Proserpina")):
        try:
            result = swe.calc_ut(jd, body, flags)
            print(f"{name}: OK  lon={result[0][0]:.6f}  speed={result[0][3]:.6f}")
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: FAIL  {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
