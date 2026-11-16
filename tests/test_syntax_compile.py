"""Регрессия: все .py проекта обязаны компилироваться и не содержать разметки.

Ловит SyntaxError, неверный порядок __future__-импортов и markdown-ограждения,
случайно попавшие в исходники, - до запуска приложения и до коммита.
"""
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FENCE = chr(96) * 3


def _project_python_files():
    for folder in ("ui_qt", "astro_core", "tests"):
        base = ROOT / folder
        if base.exists():
            for path in base.rglob("*.py"):
                if "__pycache__" not in path.parts:
                    yield path
    for path in ROOT.glob("*.py"):
        yield path


@pytest.mark.parametrize("package", ["ui_qt", "astro_core"])
def test_package_compiles(package):
    bad = []
    for path in (ROOT / package).rglob("*.py"):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            bad.append(f"{path}: {exc}")
    assert not bad, "\n".join(bad)


def test_root_scripts_compile():
    bad = []
    for path in sorted(ROOT.glob("*.py")):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            bad.append(f"{path.name}: {exc}")
    assert not bad, "\n".join(bad)


def test_no_markdown_fences_in_sources():
    bad = []
    for path in _project_python_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if FENCE in text:
            bad.append(str(path.relative_to(ROOT)))
    assert not bad, "Markdown-разметка в исходниках: " + ", ".join(bad)