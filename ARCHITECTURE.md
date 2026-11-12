# Architecture: Astro Processor

Документ описывает архитектуру, компоненты и потоки данных локального астропроцессора для Windows.

## Оглавление

1. [Общая схема](#общая-схема)
2. [Расчётное ядро (astro_core)](#расчётное-ядро-astro_core)
3. [Слой интерфейса (ui_qt)](#слой-интерфейса-ui_qt)
4. [Конфигурация и данные](#конфигурация-и-данные)
5. [Тестовая инфраструктура](#тестовая-инфраструктура)
6. [Экспорт и сборка](#экспорт-и-сборка)
7. [Зависимости и ограничения](#зависимости-и-ограничения)

---

## Общая схема

Проект построен по принципу разделения ответственности: чистое Python-ядро без привязки к UI и независимый графический слой.

```mermaid
graph TD
    User[Пользователь] -->|Ввод данных| UI[ui_qt: PyQt6]
    UI -->|Запрос расчёта| Ctrl[controllers/]
    Ctrl -->|Расчёт| Core[astro_core]

    subgraph "Расчётное ядро (astro_core)"
        Core --> Eph[ephemeris.py]
        Core --> Ch[chart.py]
        Core --> Asp[aspects.py]
        Core --> Tr[transits.py / progressions.py]
    end

    Eph -->|Чтение| Ephe[(ephe/ Swiss Ephemeris)]
    Ch -->|Чтение| Cities[(data/cities.json)]
    Core -->|Чтение| KB[(База Знаний)]

    Core -->|Результат (JSON/Dataclass)| UI
    UI -->|Рендер SVG| Paint[QPainter / QGraphicsView]
    UI -->|Экспорт| Exp[portfolio_export.py]
```
