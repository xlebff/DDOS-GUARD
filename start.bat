@echo off
chcp 65001 >nul

echo Активация виртуального окружения...
if exist ".venv\Scripts\activate" (
    call ".venv\Scripts\activate"
) else (
    echo Виртуальное окружение .venv не найдено!
    pause
    exit /b 1
)

echo Установка библиотек из requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo Файл requirements.txt не найден!
    pause
    exit /b 1
)

echo Запуск main.py с параметрами...
if exist "scripts\main.py" (
    python scripts\main.py %1 %2
) else (
    echo Файл scripts\main.py не найден!
    pause
    exit /b 1
)

pause