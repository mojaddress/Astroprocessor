# Сборка установщика (Windows)

## Шаг 1. PyInstaller (onedir)
```cmd
py -3.11 -m pip install pyinstaller
py -3.11 -m PyInstaller --noconfirm --onedir --windowed --name AstroProcessor ^
  --add-data "ephe;ephe" --add-data "data;data" --add-data "config;config" ^
  --hidden-import swisseph ui_qt/app_qt.py
  ```
Проверка: `dist\AstroProcessor\AstroProcessor.exe` запускается и считает карту.

## Шаг 2. Inno Setup
1. Установить Inno Setup 6.
2. Открыть `installer/AstroProcessor.iss`, собрать (F9).
3. Результат: `installer/installer_output/AstroProcessor-0.9.1-setup.exe`.

## Шаг 3. Проверка на чистой машине
1. Установить из setup.exe (права администратора не требуются).
2. Запустить ярлык → рассчитать натальную карту → экспорт PNG.
3. Удаление через «Установку и удаление программ» убирает папку полностью.

## Замечания
- `.env` в установщик НЕ включается (секреты не распространяются).
- Папки `profiles/`, `logs/`, `config/user_settings.json` создаются при первом запуске.
