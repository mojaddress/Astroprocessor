# PyInstaller Spec File for Astro Processor
# Run with: pyinstaller --clean AstroProcessor.spec

import sys
from pathlib import Path

# Project root - spec file is in the same directory as this script
PROJECT_ROOT = Path.cwd()

# Data files to include
data_files = [
    # Ephemeris files
    ("ephe", "ephe"),
    # Cities database
    ("data/cities.json", "data"),
    # Settings template
    ("config/default_settings.json", "config"),
]

# Hidden imports
hidden_imports = [
    "pyswisseph",
    "zoneinfo",
    "tzdata",
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtWidgets",
    "PyQt6.QtGui",
    "PyQt6.QtSvg",
    "astro_core",
    "astro_core.chart",
    "astro_core.aspects",
    "astro_core.transits",
    "astro_core.progressions",
    "astro_core.cities",
    "astro_core.timezone_service",
    "astro_core.time_service",
    "astro_core.ephemeris",
    "astro_core.chart_svg",
    "astro_core.display_profiles",
    "astro_core.profiles",
    "astro_core.constants",
    "astro_core.controllers",
    "astro_core.controllers.chart_controller",
    "astro_core.controllers.transit_controller",
    "astro_core.controllers.progression_controller",
    "astro_core.controllers.profile_controller",
    "astro_core.controllers.display_profile_controller",
    "astro_core.controllers.city_controller",
    "astro_core.state",
    "astro_core.state.session_state",
    "astro_core.state.settings_manager",
    "astro_core.paths",
    "ui_qt",
    "ui_qt.main_window",
    "ui_qt.app_qt",
    "ui_qt.widgets.chart_view",
    "ui_qt.widgets.birth_input_panel",
    "ui_qt.widgets.transit_panel",
    "ui_qt.widgets.progression_panel",
    "ui_qt.widgets.profile_manager",
    "ui_qt.widgets.display_profile_editor",
    "ui_qt.widgets.city_selector",
    "ui_qt.models.chart_model",
    "ui_qt.dialogs.settings_dialog",
]

# Exclude modules
excludes = [
    "tests",
    "test_*",
    "ui_streamlit",
    "streamlit",
    "pandas",
    "numpy",
    "matplotlib",
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
    "setuptools",
    "pip",
    "wheel",
    "__pycache__",
    "*.pyc",
    ".git",
    ".gitignore",
    "*.md",
    "*.bat",
    "run.py",
    "app.py",
    "app_legacy.py",
]

# Analysis
a = Analysis(
    ["ui_qt/app_qt.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out unwanted data files
a.datas = [x for x in a.datas if not any(ex in x[0] for ex in ["__pycache__", ".pyc", ".git"])]

# PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AstroProcessor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico" if (PROJECT_ROOT / "assets" / "icon.ico").exists() else None,
)

# Create the spec
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AstroProcessor",
)