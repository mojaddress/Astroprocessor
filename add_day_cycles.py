"""Суточные циклы: восход/заход, планетарные часы, лунные сутки, фазы Луны.

Запуск:  py -3.11 add_day_cycles.py
Создаёт: astro_core/day_cycles.py, ui_qt/widgets/day_panel.py, tests/test_day_cycles.py
Патчит:  ui_qt/main_window.py (вкладка «День и часы»)
Маркер:  DAY_TAB_V1 (один на файл). Резервные копии: *.bak_daycycles
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "astro_core" / "day_cycles.py"
PANEL = ROOT / "ui_qt" / "widgets" / "day_panel.py"
TEST = ROOT / "tests" / "test_day_cycles.py"
WIN = ROOT / "ui_qt" / "main_window.py"
MARKER = "DAY_TAB_V1"

CORE_SRC = '''"""Суточные циклы: восход/заход Солнца, планетарные часы, лунные сутки, фазы.

Восход и заход вычисляются геометрически (высота Солнца над горизонтом)
через проверенные swe.calc_ut и swe.sidtime, БЕЗ swe.rise_trans: сигнатуры
и константы rise_trans различаются между версиями pyswisseph, а продукт
не должен зависеть от недокументированного API. Точность метода - лучше
минуты; полярный день и полярная ночь обрабатываются явно.

Халдейский порядок планет (убывание скорости): Сатурн, Юпитер, Марс,
Солнце, Венера, Меркурий, Луна. Первый час дня принадлежит управителю
дня недели, далее порядок циклически продолжается и в ночные часы.
"""
from __future__ import annotations

import math
from datetime import timedelta

from .ephemeris import ensure_swisseph, get_planet_position
from .time_service import datetime_to_jd, jd_to_datetime

# Стандартная высота центра Солнца на момент восхода/захода:
# учтены атмосферная рефракция и угловой радиус диска.
SUNRISE_ALTITUDE = -0.833

# Наклонение эклиптики (J2000). Погрешность медленного изменения наклона
# даёт ошибку восхода меньше минуты на горизонте десятилетий.
OBLIQUITY = 23.4392911

CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Управитель первого часа по дню недели (Monday=0 .. Sunday=6)
DAY_RULERS = {
    0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter",
    4: "Venus", 5: "Saturn", 6: "Sun",
}

PHASE_NAMES = [
    "Новолуние", "Растущий серп", "Первая четверть", "Растущая Луна",
    "Полнолуние", "Убывающая Луна", "Последняя четверть", "Убывающий серп",
]


def _jd_from_local(local_dt, utc_offset):
    return datetime_to_jd(local_dt - timedelta(hours=float(utc_offset)))


def _local_from_jd(jd, utc_offset):
    return jd_to_datetime(jd) + timedelta(hours=float(utc_offset))


def _sun_equatorial(jd_ut):
    """Экваториальные координаты Солнца (RA, Dec) в градусах."""
    lon, _ = get_planet_position(jd_ut, "Sun")
    lam = math.radians(lon)
    eps = math.radians(OBLIQUITY)
    ra = math.degrees(math.atan2(math.sin(lam) * math.cos(eps), math.cos(lam))) % 360.0
    dec = math.degrees(math.asin(math.sin(lam) * math.sin(eps)))
    return ra, dec


def local_sidereal_deg(jd_ut, longitude):
    """Локальное звёздное время в градусах."""
    import swisseph as swe
    return (swe.sidtime(jd_ut) * 15.0 + longitude) % 360.0


def sun_altitude(jd_ut, latitude, longitude):
    """Высота центра Солнца над горизонтом в градусах."""
    ra, dec = _sun_equatorial(jd_ut)
    lst = local_sidereal_deg(jd_ut, longitude)
    hour = math.radians(lst - ra)
    phi = math.radians(latitude)
    delta = math.radians(dec)
    sin_alt = (math.sin(phi) * math.sin(delta)
               + math.cos(phi) * math.cos(delta) * math.cos(hour))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))


def _refine_altitude(jd_low, jd_high, latitude, longitude):
    """Бисекция момента, когда высота Солнца равна SUNRISE_ALTITUDE."""
    def value(jd):
        return sun_altitude(jd, latitude, longitude) - SUNRISE_ALTITUDE

    low, high = jd_low, jd_high
    f_low = value(low)
    for _ in range(48):
        mid = (low + high) / 2.0
        f_mid = value(mid)
        if abs(f_mid) < 1e-7 or (high - low) < 1e-7:
            return mid
        if (f_low > 0.0) == (f_mid > 0.0):
            low, f_low = mid, f_mid
        else:
            high = mid
    return (low + high) / 2.0


def sun_events(day_local_midnight, latitude, longitude, utc_offset):
    """Восход и заход Солнца для локальных суток.

    Возвращает словарь: rise/set - Julian Day (UTC) или None, polar - флаг,
    polar_day - True при полярном дне (иначе полярная ночь).
    """
    ensure_swisseph()
    start = _jd_from_local(day_local_midnight, utc_offset)
    steps = 288  # шаг 5 минут
    rises, sets = [], []
    prev_alt = None
    prev_jd = None
    for index in range(steps + 1):
        jd = start + index / float(steps)
        alt = sun_altitude(jd, latitude, longitude)
        if prev_alt is not None:
            if prev_alt < SUNRISE_ALTITUDE <= alt:
                rises.append(_refine_altitude(prev_jd, jd, latitude, longitude))
            elif prev_alt >= SUNRISE_ALTITUDE > alt:
                sets.append(_refine_altitude(prev_jd, jd, latitude, longitude))
        prev_alt, prev_jd = alt, jd
    rise = rises[0] if rises else None
    sunset = sets[0] if sets else None
    polar = rise is None or sunset is None
    return {
        "rise": rise,
        "set": sunset,
        "polar": polar,
        "polar_day": bool(polar and sun_altitude(start + 0.5, latitude, longitude) > 0.0),
    }


def _chaldean_from(start_ruler):
    """24 управителя подряд, начиная с управителя дня."""
    offset = CHALDEAN_ORDER.index(start_ruler)
    return [CHALDEAN_ORDER[(offset + i) % 7] for i in range(24)]


def planetary_hours(day_local_midnight, latitude, longitude, utc_offset):
    """24 планетарных часа локальных суток (12 дневных + 12 ночных).

    Возвращает список словарей либо пустой список при полярном дне/ночи.
    """
    today = sun_events(day_local_midnight, latitude, longitude, utc_offset)
    if today["polar"]:
        return []
    tomorrow = sun_events(day_local_midnight + timedelta(days=1),
                          latitude, longitude, utc_offset)
    if tomorrow["rise"] is None:
        return []

    rise, sunset = today["rise"], today["set"]
    next_rise = tomorrow["rise"]
    day_step = (sunset - rise) / 12.0
    night_step = (next_rise - sunset) / 12.0
    rulers = _chaldean_from(DAY_RULERS[day_local_midnight.weekday()])

    hours = []
    cursor = rise
    for index in range(24):
        step = day_step if index < 12 else night_step
        start_jd, end_jd = cursor, cursor + step
        hours.append({
            "index": index + 1,
            "kind": "day" if index < 12 else "night",
            "ruler": rulers[index],
            "start_jd": start_jd,
            "end_jd": end_jd,
            "start_local": _local_from_jd(start_jd, utc_offset),
            "end_local": _local_from_jd(end_jd, utc_offset),
        })
        cursor = end_jd
    return hours


def moon_sun_elongation(jd_ut):
    """Угловое расстояние Луны от Солнца, 0..360."""
    sun, _ = get_planet_position(jd_ut, "Sun")
    moon, _ = get_planet_position(jd_ut, "Moon")
    return (moon - sun) % 360.0


def _lunar_day_from_elongation(elongation):
    """Лунные сутки 1..30: каждые 12 градусов элонгации."""
    return int(float(elongation) // 12.0) + 1


def _phase_from_elongation(elongation):
    index = int((float(elongation) + 22.5) % 360.0 // 45.0)
    return PHASE_NAMES[index]


def lunar_day(jd_ut):
    return _lunar_day_from_elongation(moon_sun_elongation(jd_ut))


def moon_phase(jd_ut):
    return _phase_from_elongation(moon_sun_elongation(jd_ut))
'''

PANEL_SRC = '''"""Панель суточных циклов: планетарные часы, лунные сутки, фаза Луны (DAY_TAB_V1)."""
from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QAbstractItemView, QDateEdit, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from astro_core import day_cycles as dc
from astro_core.constants import get_planet_name_ru


class DayPanel(QWidget):
    """Планетарные часы и лунные сутки для даты и места."""

    def __init__(self, birth_provider, parent=None):
        super().__init__(parent)
        self._birth_provider = birth_provider
        self._hours = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        top = QGroupBox("Дата и место")
        form = QFormLayout(top)
        self.edit_date = QDateEdit()
        self.edit_date.setDate(QDate.currentDate())
        self.edit_date.setCalendarPopup(True)
        form.addRow("Дата:", self.edit_date)
        self.lbl_place = QLabel("место не задано")
        form.addRow("Место:", self.lbl_place)
        self.btn_calculate = QPushButton("🔄 Рассчитать день")
        self.btn_calculate.clicked.connect(self._on_calculate)
        form.addRow(self.btn_calculate)
        layout.addWidget(top)

        info = QGroupBox("Солнце и Луна")
        info_layout = QFormLayout(info)
        self.lbl_sun = QLabel("—")
        self.lbl_sun.setWordWrap(True)
        info_layout.addRow("Солнце:", self.lbl_sun)
        self.lbl_moon = QLabel("—")
        self.lbl_moon.setWordWrap(True)
        info_layout.addRow("Луна:", self.lbl_moon)
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["№", "Начало", "Конец", "Управитель", "Часть суток"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def _place(self):
        birth = self._birth_provider() if callable(self._birth_provider) else None
        if not birth:
            return None
        return (float(birth.get("latitude", 0.0)),
                float(birth.get("longitude", 0.0)),
                float(birth.get("utc_offset_hours", 0.0)),
                str(birth.get("city_name") or birth.get("name") or "место"))

    def _on_calculate(self):
        place = self._place()
        if place is None:
            self.lbl_place.setText("сначала рассчитайте натальную карту")
            self.table.setRowCount(0)
            return
        lat, lon, offset, name = place
        self.lbl_place.setText(f"{name} · {lat:.2f}, {lon:.2f} · UTC{offset:+.1f}")

        day = self.edit_date.date().toPyDate()
        midnight = datetime(day.year, day.month, day.day, 0, 0)
        events = dc.sun_events(midnight, lat, lon, offset)
        jd_noon = dc._jd_from_local(midnight, offset) + 0.5

        if events["polar"]:
            kind = "полярный день" if events["polar_day"] else "полярная ночь"
            self.lbl_sun.setText(f"{kind}: восход и заход в эту дату отсутствуют, "
                                 f"планетарные часы не определены")
            self._hours = []
            self.table.setRowCount(0)
        else:
            rise = dc._local_from_jd(events["rise"], offset)
            sunset = dc._local_from_jd(events["set"], offset)
            length = sunset - rise
            self.lbl_sun.setText(
                f"восход {rise:%H:%M}, заход {sunset:%H:%M}, "
                f"долгота дня {length.seconds // 3600} ч {(length.seconds % 3600) // 60} мин")
            self._hours = dc.planetary_hours(midnight, lat, lon, offset)
            self._fill_table(midnight, offset)

        self.lbl_moon.setText(
            f"лунные сутки {dc.lunar_day(jd_noon)}, фаза: {dc.moon_phase(jd_noon)}")

    def _fill_table(self, midnight, offset):
        now = datetime.now()
        same_day = now.date() == midnight.date()
        self.table.setRowCount(len(self._hours))
        for row, hour in enumerate(self._hours):
            values = [
                str(hour["index"]),
                f"{hour['start_local']:%H:%M}",
                f"{hour['end_local']:%H:%M}",
                get_planet_name_ru(hour["ruler"]),
                "день" if hour["kind"] == "day" else "ночь",
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                self.table.setItem(row, column, item)
            if same_day and hour["start_local"] <= now < hour["end_local"]:
                for column in range(5):
                    current = self.table.item(row, column)
                    font = current.font()
                    font.setBold(True)
                    current.setFont(font)
        self.table.resizeColumnsToContents()
'''

TEST_SRC = '''"""Суточные циклы: чистые функции, инварианты восхода, планетарные часы."""
import math
from datetime import datetime

import pytest

from astro_core import day_cycles as dc

MOSCOW = (55.7558, 37.6173, 3.0)


def test_lunar_day_from_elongation():
    assert dc._lunar_day_from_elongation(0.0) == 1
    assert dc._lunar_day_from_elongation(11.9) == 1
    assert dc._lunar_day_from_elongation(12.0) == 2
    assert dc._lunar_day_from_elongation(359.9) == 30


def test_phase_from_elongation():
    assert dc._phase_from_elongation(0.0) == "Новолуние"
    assert dc._phase_from_elongation(90.0) == "Первая четверть"
    assert dc._phase_from_elongation(180.0) == "Полнолуние"
    assert dc._phase_from_elongation(270.0) == "Последняя четверть"


def test_chaldean_rotation_from_sun():
    assert dc._chaldean_from("Sun")[:7] == [
        "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]


def test_day_rulers_weekday():
    assert dc.DAY_RULERS[datetime(2026, 11, 16).weekday()] == "Moon"  # понедельник
    assert dc.DAY_RULERS[datetime(2026, 11, 21).weekday()] == "Saturn"  # суббота


def test_sun_altitude_range():
    jd = dc._jd_from_local(datetime(2026, 6, 21, 12, 0), 3.0)
    alt = dc.sun_altitude(jd, *MOSCOW[:2])
    assert 50.0 < alt < 62.0, f"полуденная высота летом вне разумного: {alt}"


def test_sun_events_order_and_day_length():
    events = dc.sun_events(datetime(2026, 3, 20), *MOSCOW)
    assert not events["polar"]
    assert events["rise"] < events["set"]
    day_hours = (events["set"] - events["rise"]) * 24
    assert 11.0 < day_hours < 13.5, f"долгота дня в равноденствие: {day_hours}"


def test_summer_day_longer_than_winter():
    summer = dc.sun_events(datetime(2026, 6, 21), *MOSCOW)
    winter = dc.sun_events(datetime(2026, 12, 21), *MOSCOW)
    assert (summer["set"] - summer["rise"]) > (winter["set"] - winter["rise"])


def test_polar_day_detected():
    events = dc.sun_events(datetime(2026, 6, 21), 78.0, 15.0, 1.0)
    assert events["polar"] and events["polar_day"]
    assert dc.planetary_hours(datetime(2026, 6, 21), 78.0, 15.0, 1.0) == []


def test_planetary_hours_structure():
    midnight = datetime(2026, 3, 20)
    hours = dc.planetary_hours(midnight, *MOSCOW)
    assert len(hours) == 24
    assert hours[0]["ruler"] == dc.DAY_RULERS[midnight.weekday()]
    day_lengths = {(h["end_jd"] - h["start_jd"]) for h in hours if h["kind"] == "day"}
    night_lengths = {(h["end_jd"] - h["start_jd"]) for h in hours if h["kind"] == "night"}
    assert len(day_lengths) == 1 and len(night_lengths) == 1
    sequence = [h["ruler"] for h in hours]
    assert sequence == dc._chaldean_from(sequence[0])
    assert hours[0]["start_jd"] < hours[-1]["end_jd"]


def test_lunar_day_in_range():
    jd = dc._jd_from_local(datetime(2026, 11, 16, 12, 0), 3.0)
    assert 1 <= dc.lunar_day(jd) <= 30
    assert dc.moon_phase(jd) in dc.PHASE_NAMES
'''

WIN_EDIT = [
    ('        self._calc_tabs.addTab(self._midpoints_panel, "🔗 Средние точки")',
     '        self._calc_tabs.addTab(self._midpoints_panel, "🔗 Средние точки")\n'
     '        # DAY_TAB_V1: суточные циклы - планетарные часы и лунные сутки\n'
     '        from ui_qt.widgets.day_panel import DayPanel\n'
     '        self._day_panel = DayPanel(lambda: self._current_birth_data)\n'
     '        self._calc_tabs.addTab(self._day_panel, "🌙 День и часы")'),
]


def patch_win():
    src = WIN.read_text(encoding="utf-8")
    if MARKER in src:
        print("[*] main_window.py: вкладка уже добавлена.")
        return
    old, new = WIN_EDIT[0]
    if src.count(old) != 1:
        print(f"[X] main_window.py: якорь найден {src.count(old)} раз. Файл НЕ изменён.")
        sys.exit(1)
    src = src.replace(old, new, 1)
    try:
        compile(src, str(WIN), "exec")
    except SyntaxError as exc:
        print(f"[X] main_window.py: SyntaxError: {exc}. Файл НЕ изменён.")
        sys.exit(1)
    shutil.copy2(WIN, WIN.with_name(WIN.name + ".bak_daycycles"))
    WIN.write_text(src, encoding="utf-8")
    print("[+] main_window.py пропатчен (вкладка «День и часы»).")


def main():
    for path in (WIN,):
        if not path.exists():
            print(f"[X] Не найден файл {path}")
            sys.exit(1)

    CORE.write_text(CORE_SRC, encoding="utf-8")
    print("[+] Создан astro_core/day_cycles.py")
    PANEL.write_text(PANEL_SRC, encoding="utf-8")
    print("[+] Создан ui_qt/widgets/day_panel.py")
    TEST.write_text(TEST_SRC, encoding="utf-8")
    print("[+] Создан tests/test_day_cycles.py (10 проверок)")
    patch_win()

    sys.path.insert(0, str(ROOT))
    try:
        from datetime import datetime as _dt
        from astro_core import day_cycles as module
        events = module.sun_events(_dt(2026, 3, 20), 55.7558, 37.6173, 3.0)
        if events["polar"]:
            print("[X] Восход/заход не найдены для Москвы 20.03.2026 — сообщите агенту")
            sys.exit(1)
        rise = module._local_from_jd(events["rise"], 3.0)
        sunset = module._local_from_jd(events["set"], 3.0)
        hours = module.planetary_hours(_dt(2026, 3, 20), 55.7558, 37.6173, 3.0)
        jd = module._jd_from_local(_dt(2026, 11, 16, 12, 0), 3.0)
        print("[+] Контроль (Москва, 20.03.2026):")
        print(f"    восход {rise:%H:%M}, заход {sunset:%H:%M}")
        print(f"    планетарных часов: {len(hours)}, первый управитель: {hours[0]['ruler']}")
        print(f"    лунные сутки 16.11.2026: {module.lunar_day(jd)}, фаза: {module.moon_phase(jd)}")
        print("[+] Проверено: суточные циклы считаются.")
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Ошибка контроля: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()