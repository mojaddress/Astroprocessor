"""Регрессия: все .py в ui_qt и astro_core обязаны компилироваться.

Ловит SyntaxError и неверный порядок __future__-импортов до запуска приложения.
"""
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("package", ["ui_qt", "astro_core"])
def test_package_compiles(package):
    bad = []
    for path in (ROOT / package).rglob("*.py"):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            bad.append(f"{path}: {exc}")
    assert not bad, "\n".join(bad)
