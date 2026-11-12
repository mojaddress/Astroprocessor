@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal

set "PY=py -3.11"

:: Защита от сбоя temp-путей Windows
if not defined TEMP set "TEMP=%USERPROFILE%\AppData\Local\Temp"
if not defined TMP set "TMP=%TEMP%"

echo ==========================================
echo    ASTRO PROCESSOR - STARTUP
echo ==========================================
echo.

%PY% --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python 3.11 не найден (py launcher). Установите с python.org.
    pause
    exit /b 1
)

:: Дозастановка зависимостей, если в глобальной среде чего-то не хватает
%PY% -c "import PyQt6, swisseph" >nul 2>&1
if errorlevel 1 (
    echo [*] Установка недостающих зависимостей...
    %PY% -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
    if errorlevel 1 (
        echo [X] Ошибка установки зависимостей.
        pause
        exit /b 1
    )
)

echo [*] Запуск Astro Processor...
%PY% -m ui_qt.app_qt

if errorlevel 1 (
    echo.
    echo [X] Приложение завершилось с ошибкой.
    pause
)
endlocal