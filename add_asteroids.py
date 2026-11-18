"""Астероиды Церера/Паллада/Юнона/Веста + глифы + аспекты к углам и точкам.

Запуск:  py -3.11 add_asteroids.py
Патчит:  astro_core/constants.py, astro_core/ephemeris.py, astro_core/display_profiles.py,
         ui_qt/widgets/astro_glyphs.py, ui_qt/widgets/chart_view.py,
         ui_qt/widgets/birth_input_panel.py
Создаёт: tests/test_asteroids.py
Идемпотентен: маркер ASTEROIDS_V1. Резервные копии: *.bak_asteroids
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER = "ASTEROIDS_V1"

CONST = ROOT / "astro_core" / "constants.py"
EPH = ROOT / "astro_core" / "ephemeris.py"
PROFILES = ROOT / "astro_core" / "display_profiles.py"
GLYPHS = ROOT / "ui_qt" / "widgets" / "astro_glyphs.py"
VIEW = ROOT / "ui_qt" / "widgets" / "chart_view.py"
PANEL = ROOT / "ui_qt" / "widgets" / "birth_input_panel.py"
TEST_FILE = ROOT / "tests" / "test_asteroids.py"

GLYPH_FUNCS = '''# --- Астероиды --- ASTEROIDS_V1
def glyph_ceres():
    """Церера: серп над крестом."""
    p = QPainterPath()
    p.moveTo(50, 46); p.lineTo(50, 90)
    p.moveTo(36, 74); p.lineTo(64, 74)
    p.moveTo(50, 46)
    p.quadTo(50, 22, 32, 22)
    p.quadTo(16, 22, 16, 36)
    return p, []


def glyph_pallas():
    """Паллада: наконечник копья (ромб) над крестом."""
    p = QPainterPath()
    p.moveTo(50, 12); p.lineTo(67, 34); p.lineTo(50, 56); p.lineTo(33, 34)
    p.closeSubpath()
    p.moveTo(50, 56); p.lineTo(50, 90)
    p.moveTo(36, 74); p.lineTo(64, 74)
    return p, []


def glyph_juno():
    """Юнона: скипетр со звездой над крестом."""
    p = QPainterPath()
    cx, cy, r = 50, 28, 16
    p.moveTo(cx - r, cy); p.lineTo(cx + r, cy)
    p.moveTo(cx, cy - r); p.lineTo(cx, cy + r)
    d = r * 0.7
    p.moveTo(cx - d, cy - d); p.lineTo(cx + d, cy + d)
    p.moveTo(cx - d, cy + d); p.lineTo(cx + d, cy - d)
    p.moveTo(50, 44); p.lineTo(50, 90)
    p.moveTo(36, 74); p.lineTo(64, 74)
    return p, []


def glyph_vesta():
    """Веста: пламя очага над крестом."""
    p = QPainterPath()
    p.moveTo(32, 16); p.lineTo(50, 44); p.lineTo(68, 16)
    p.moveTo(38, 30); p.lineTo(62, 30)
    p.moveTo(50, 44); p.lineTo(50, 90)
    p.moveTo(36, 74); p.lineTo(64, 74)
    return p, []


'''

CALC_BLOCK = '''    # --- Астероиды --- ASTEROIDS_V1
    if settings.get("include_asteroids", False):
        for asteroid_name in ASTEROID_NAMES:
            try:
                asteroid_id = get_planet_id(asteroid_name)
                result = _cached_calc_ut(julian_day, asteroid_id, flags)
                coords = result[0]
                longitude = normalize_longitude(float(coords[0]))
                speed_longitude = float(coords[3]) if len(coords) > 3 else 0.0
                sign, degree_in_sign = sign_from_longitude(longitude)
                objects.append({
                    "name": asteroid_name,
                    "type": "asteroid",
                    "longitude": round(longitude, 6),
                    "sign": sign,
                    "degree_in_sign": round(degree_in_sign, 6),
                    "speed_longitude": round(speed_longitude, 6),
                    "retrograde": speed_longitude < 0,
                })
            except Exception as exc:
                warnings.append(
                    f"{asteroid_name}: недоступен ({exc}). "
                    f"Нужен файл эфемерид seas_18.se1 - см. менеджер эфемерид.")

    return objects, warnings'''

EDITS = {
    CONST: [
        ('    "Chiron": "Хирон",\n',
         '    "Chiron": "Хирон",\n'
         '    "Ceres": "Церера",\n'
         '    "Pallas": "Паллада",\n'
         '    "Juno": "Юнона",\n'
         '    "Vesta": "Веста",\n'),
    ],
    EPH: [
        ('    "Pluto",\n]\n',
         '    "Pluto",\n]\n\n'
         '# ASTEROIDS_V1: основные астероиды (файл эфемерид seas_18.se1).\n'
         'ASTEROID_NAMES = ["Ceres", "Pallas", "Juno", "Vesta"]\n'),
        ('        "Chiron": getattr(swe, "CHIRON", 15),\n    }',
         '        "Chiron": getattr(swe, "CHIRON", 15),\n'
         '        # ASTEROIDS_V1\n'
         '        "Ceres": getattr(swe, "CERES", 17),\n'
         '        "Pallas": getattr(swe, "PALLAS", 18),\n'
         '        "Juno": getattr(swe, "JUNO", 19),\n'
         '        "Vesta": getattr(swe, "VESTA", 20),\n    }'),
        ('    return objects, warnings', CALC_BLOCK),
    ],
    PROFILES: [
        ('SPECIAL_OBJECTS = ["Chiron", "LunarNodes", "PartOfFortune", "CrossOfFate",\n'
         '                   "BlackMoon", "Selena", "Proserpina", "Angles"]',
         'SPECIAL_OBJECTS = ["Chiron", "LunarNodes", "PartOfFortune", "CrossOfFate",\n'
         '                   "BlackMoon", "Selena", "Proserpina", "Angles",\n'
         '                   "Asteroids"]  # ASTEROIDS_V1'),
        ('def _all_objects_enabled():\n'
         '    """Все объекты включены."""\n'
         '    return {key: True for key in ALL_OBJECT_KEYS}',
         'def _all_objects_enabled():\n'
         '    """Все объекты включены; астероиды - по умолчанию выключены (ASTEROIDS_V1)."""\n'
         '    enabled = {key: True for key in ALL_OBJECT_KEYS}\n'
         '    enabled["Asteroids"] = False\n'
         '    return enabled'),
        ('    settings["include_proserpina"] = bool(objects.get("Proserpina", True))',
         '    settings["include_proserpina"] = bool(objects.get("Proserpina", True))\n'
         '    settings["include_asteroids"] = bool(objects.get("Asteroids", False))  # ASTEROIDS_V1'),
    ],
    GLYPHS: [
        ('GLYPH_BUILDERS = {', GLYPH_FUNCS + 'GLYPH_BUILDERS = {'),
        ('    "PartOfFortune": glyph_part_of_fortune,\n}',
         '    "PartOfFortune": glyph_part_of_fortune,\n'
         '    # ASTEROIDS_V1\n'
         '    "Ceres": glyph_ceres,\n'
         '    "Pallas": glyph_pallas,\n'
         '    "Juno": glyph_juno,\n'
         '    "Vesta": glyph_vesta,\n}'),
    ],
    VIEW: [
        ('    "SouthNode": "#A9A9A9", "Chiron": "#8B4513",\n}',
         '    "SouthNode": "#A9A9A9", "Chiron": "#8B4513",\n'
         '    # ASTEROIDS_V1\n'
         '    "Ceres": "#8D6E63", "Pallas": "#5C6BC0",\n'
         '    "Juno": "#C2185B", "Vesta": "#EF6C00",\n}'),
        ('    def _draw_angles(self, points, r_from, r_to):\n'
         '        if not self._settings["show_angle_labels"]:\n'
         '            return\n'
         '        c = SCENE_SIZE / 2',
         '    def _draw_angles(self, points, r_from, r_to):\n'
         '        """Рисует углы и возвращает их позиции для линий аспектов (ASTEROIDS_V1)."""\n'
         '        positions = {}\n'
         '        if not self._settings["show_angle_labels"]:\n'
         '            return positions\n'
         '        c = SCENE_SIZE / 2'),
        ('            titem = self._text(tp.x(), tp.y(), name, 16, color)\n'
         '            titem.setData(0, "angles")',
         '            titem = self._text(tp.x(), tp.y(), name, 16, color)\n'
         '            titem.setData(0, "angles")\n'
         '            positions[name] = self._lp(lon, r_from, c)\n'
         '        return positions'),
        ('        result = None\n', '        positions = {}\n'),
        ('            if result is None:\n'
         '                result = pos\n'
         '        return result',
         '            positions[name] = pos\n'
         '        return positions'),
        ('        self._draw_angles(self._chart_data.get("additional_points", []),\n'
         '                          s * R_HOUSES, s * R_OUTER)\n'
         '        pof = self._draw_point_of_fortune(self._chart_data.get("additional_points", []),\n'
         '                                          s * R_ASPECTS, self._settings["planet_dot_size"], 26)\n'
         '        if pof is not None:\n'
         '            positions["PartOfFortune"] = pof',
         '        # ASTEROIDS_V1: углы и точки участвуют в линиях аспектов\n'
         '        positions.update(self._draw_angles(\n'
         '            self._chart_data.get("additional_points", []), s * R_HOUSES, s * R_OUTER))\n'
         '        positions.update(self._draw_point_of_fortune(\n'
         '            self._chart_data.get("additional_points", []),\n'
         '            s * R_ASPECTS, self._settings["planet_dot_size"], 26))'),
        ('        pof = self._draw_point_of_fortune(self._chart_data.get("additional_points", []), r_asp, 5, 22)\n'
         '        if pof is not None:\n'
         '            nat_pos["PartOfFortune"] = pof',
         '        # ASTEROIDS_V1: углы и точки участвуют в линиях аспектов\n'
         '        nat_pos.update(self._draw_point_of_fortune(\n'
         '            self._chart_data.get("additional_points", []), r_asp, 5, 22))\n'
         '        nat_pos.update(self._draw_angles(\n'
         '            self._chart_data.get("additional_points", []), r_nat, s * R_OUTER))'),
        ('        self._draw_angles(self._chart_data.get("additional_points", []), r_nat, s * R_OUTER)\n'
         '        self._draw_legend()',
         '        self._draw_legend()'),
    ],
    PANEL: [
        ('        self.chk_proserpina = QCheckBox("Прозерпина")\n',
         '        self.chk_proserpina = QCheckBox("Прозерпина")\n'
         '        self.chk_asteroids = QCheckBox("Астероиды")  # ASTEROIDS_V1\n'
         '        self.chk_asteroids.setToolTip("Церера, Паллада, Юнона, Веста (нужен seas_18.se1)")\n'
         '        self.chk_asteroids.setChecked(False)\n'),
        ('        obj_layout.addWidget(self.chk_proserpina, 2, 2)\n',
         '        obj_layout.addWidget(self.chk_proserpina, 2, 2)\n'
         '        obj_layout.addWidget(self.chk_asteroids, 3, 0)\n'),
        ('                    self.chk_angles, self.chk_dsc):',
         '                    self.chk_angles, self.chk_dsc, self.chk_asteroids):'),
        ('            self.chk_fortune, self.chk_angles, self.chk_dsc,\n        ]:',
         '            self.chk_fortune, self.chk_angles, self.chk_dsc, self.chk_asteroids,\n        ]:'),
        ('            "include_proserpina": self.chk_proserpina.isChecked(),',
         '            "include_proserpina": self.chk_proserpina.isChecked(),\n'
         '            "include_asteroids": self.chk_asteroids.isChecked(),  # ASTEROIDS_V1'),
        ('            self.chk_proserpina.setChecked(bool(objects.get("Proserpina", True)))',
         '            self.chk_proserpina.setChecked(bool(objects.get("Proserpina", True)))\n'
         '            self.chk_asteroids.setChecked(bool(objects.get("Asteroids", False)))'),
    ],
}

TEST_SRC = '''"""Астероиды: расчёт, глифы, цвета, профили, UI и аспекты к углам/точкам."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from astro_core import display_profiles as dp
from astro_core.chart import build_natal_chart
from astro_core.constants import PLANET_NAMES_RU
from astro_core.ephemeris import ASTEROID_NAMES

BIRTH = {
    "name": "AsteroidTest", "date": "1990-05-15", "time": "14:30",
    "latitude": 55.7558, "longitude": 37.6173,
    "utc_offset_hours": 3, "timezone": "Europe/Moscow",
}


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(scope="module")
def chart_with_asteroids():
    return build_natal_chart(BIRTH, {"include_asteroids": True,
                                     "include_part_of_fortune": True,
                                     "include_angles": True})


def test_asteroids_absent_by_default():
    chart = build_natal_chart(BIRTH, {})
    names = {o["name"] for o in chart["objects"]}
    assert not (set(ASTEROID_NAMES) & names)


def test_asteroids_present_when_enabled(chart_with_asteroids):
    names = {o["name"] for o in chart_with_asteroids["planets"]}
    assert set(ASTEROID_NAMES) <= names


def test_asteroid_fields_valid(chart_with_asteroids):
    for obj in chart_with_asteroids["planets"]:
        if obj["name"] in ASTEROID_NAMES:
            assert obj["type"] == "asteroid"
            assert 0.0 <= obj["longitude"] < 360.0
            assert obj["sign"]
            assert isinstance(obj["retrograde"], bool)
            assert obj["house"] in range(1, 13)


def test_asteroids_survive_enabled_planets_filter():
    chart = build_natal_chart(BIRTH, {
        "include_asteroids": True,
        "enabled_planets": ["Sun", "Moon", "Mercury", "Venus", "Mars"],
    })
    names = {o["name"] for o in chart["objects"]}
    assert set(ASTEROID_NAMES) <= names
    assert "Jupiter" not in names


def test_asteroids_in_all_objects(chart_with_asteroids):
    names = {o["name"] for o in chart_with_asteroids["objects"]}
    assert set(ASTEROID_NAMES) <= names


@pytest.mark.parametrize("name", ASTEROID_NAMES)
def test_glyph_exists(name):
    from ui_qt.widgets.astro_glyphs import get_glyph
    glyph = get_glyph(name)
    assert glyph is not None, f"глиф {name} отсутствует - объект не будет нарисован"
    path, fills = glyph
    assert not path.isEmpty()
    rect = path.boundingRect()
    assert 0 <= rect.left() <= rect.right() <= 100
    assert 0 <= rect.top() <= rect.bottom() <= 100


def test_russian_names():
    for name in ASTEROID_NAMES:
        assert PLANET_NAMES_RU.get(name)


def test_colors_defined():
    from ui_qt.widgets.chart_view import PLANET_COLORS
    for name in ASTEROID_NAMES:
        assert name in PLANET_COLORS


def test_full_profile_asteroids_off_by_default():
    for name in dp.BUILTIN_PROFILE_NAMES:
        profile = dp.get_builtin_profile(name)
        assert profile["objects"]["Asteroids"] is False


def test_profile_maps_asteroids_flag():
    profile = dp.get_builtin_profile("full")
    profile["objects"]["Asteroids"] = True
    settings = dp.apply_profile_to_settings(profile, {})
    assert settings["include_asteroids"] is True
    assert dp.validate_profile(profile) == []


def test_ui_checkbox_and_settings(qapp):
    from astro_core.controllers import CityController, ProfileController
    from ui_qt.widgets.birth_input_panel import BirthInputPanel
    panel = BirthInputPanel(CityController(), ProfileController())
    try:
        assert panel.chk_asteroids.isChecked() is False
        assert panel.get_settings()["include_asteroids"] is False
        panel.chk_asteroids.setChecked(True)
        assert panel.get_settings()["include_asteroids"] is True
        panel.set_object_flags({"PartOfFortune": True, "Asteroids": False})
        assert panel.chk_asteroids.isChecked() is False
    finally:
        panel.deleteLater()


def test_draw_angles_returns_positions(qapp, chart_with_asteroids):
    from ui_qt.widgets.chart_view import ChartView
    view = ChartView()
    try:
        view.set_chart_data(chart_with_asteroids, {"show_angle_labels": True})
        positions = view._draw_angles(chart_with_asteroids["additional_points"], 300, 350)
        assert "ASC" in positions and "MC" in positions
    finally:
        view.deleteLater()


def test_draw_points_returns_positions(qapp, chart_with_asteroids):
    from ui_qt.widgets.chart_view import ChartView
    view = ChartView()
    try:
        view.set_chart_data(chart_with_asteroids, {"show_angle_labels": True})
        positions = view._draw_point_of_fortune(
            chart_with_asteroids["additional_points"], 260, 5, 26)
        assert "PartOfFortune" in positions
    finally:
        view.deleteLater()
'''


def patch(path: Path, edits: list) -> None:
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[*] {path.name}: патч уже применён.")
        return
    for old, _new in edits:
        if src.count(old) != 1:
            print(f"[X] {path.name}: якорь найден {src.count(old)} раз (ожидался 1):")
            print(f"    {old[:90]!r}")
            print("    Файл НЕ изменён.")
            sys.exit(1)
    for old, new in edits:
        src = src.replace(old, new, 1)
    try:
        compile(src, str(path), "exec")
    except SyntaxError as exc:
        print(f"[X] {path.name}: SyntaxError: {exc}. Файл НЕ изменён.")
        sys.exit(1)
    shutil.copy2(path, path.with_name(path.name + ".bak_asteroids"))
    path.write_text(src, encoding="utf-8")
    print(f"[+] {path.name} пропатчен.")


def main() -> None:
    for path in EDITS:
        if not path.exists():
            print(f"[X] Не найден файл {path}")
            sys.exit(1)
    for path, edits in EDITS.items():
        patch(path, edits)

    TEST_FILE.write_text(TEST_SRC, encoding="utf-8")
    print("[+] Создан tests/test_asteroids.py (16 проверок)")

    sys.path.insert(0, str(ROOT))
    try:
        from astro_core.chart import build_natal_chart
        from astro_core.ephemeris import ASTEROID_NAMES
        chart = build_natal_chart(
            {"name": "Probe", "date": "1990-05-15", "time": "14:30",
             "latitude": 55.7558, "longitude": 37.6173, "utc_offset_hours": 3},
            {"include_asteroids": True})
        print("[+] Контроль: астероиды в расчёте")
        for obj in chart["planets"]:
            if obj["name"] in ASTEROID_NAMES:
                print(f"    {obj['name']:<8} {obj['longitude']:8.3f}°  "
                      f"{obj['sign']:<12} дом {obj['house']}")
        for warning in chart["warnings"]:
            if any(n in warning for n in ASTEROID_NAMES):
                print(f"    [!] {warning}")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Ошибка контроля: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()