"""Аудит упаковки к продаже (итерация 31): что есть, чего не хватает."""
import glob
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

checks = [
    ("requirements.txt", os.path.exists(os.path.join(ROOT, "requirements.txt")), True),
    ("ephe/*.se1 (эфемериды)", len(glob.glob(os.path.join(ROOT, "ephe", "*.se1"))) > 0, True),
    ("data/cities.json", os.path.exists(os.path.join(ROOT, "data", "cities.json")), True),
    ("config/default_settings.json",
     os.path.exists(os.path.join(ROOT, "config", "default_settings.json")), False),
    (".env.example", os.path.exists(os.path.join(ROOT, ".env.example")), False),
    ("README.md", os.path.exists(os.path.join(ROOT, "README.md")), True),
    ("USER_GUIDE.md", os.path.exists(os.path.join(ROOT, "USER_GUIDE.md")), False),
    ("LICENSES.md", os.path.exists(os.path.join(ROOT, "LICENSES.md")), False),
    ("LOG.md", os.path.exists(os.path.join(ROOT, "LOG.md")), False),
    ("installer/AstroProcessor.iss",
     os.path.exists(os.path.join(ROOT, "installer", "AstroProcessor.iss")), False),
    ("installer/README_INSTALL.md",
     os.path.exists(os.path.join(ROOT, "installer", "README_INSTALL.md")), False),
    ("tests (>=20 файлов)", len(glob.glob(os.path.join(ROOT, "tests", "test_*.py"))) >= 20, False),
]

missing_critical = []
print("Аудит упаковки Astro Processor")
print("=" * 60)
for name, ok, critical in checks:
    print(f"{'✅' if ok else '❌'} {name}" + (" (критично)" if critical and not ok else ""))
    if critical and not ok:
        missing_critical.append(name)
print("=" * 60)
if missing_critical:
    print("Критично не хватает:", ", ".join(missing_critical))
    raise SystemExit(1)
print("Критичных пробелов нет. Далее: сборка по installer/README_INSTALL.md")
