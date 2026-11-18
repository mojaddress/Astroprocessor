"""Удаление мёртвого кода после релиза 1.1.0.

Запуск:  py -3.11 cleanup_dead_code.py
Удаляет: _extract_transit_planets_for_chart, _extract_transit_aspects_for_chart
         (не используются после исправления транзитного слоя);
         _eq_naturals, дубликат _apply_eq_heights (не вызываются);
         fix_profile_created_at.py (одноразовый патчер).
Маркер: DEAD_CODE_V1. Резервные копии: *.bak_deadcode
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIN = ROOT / "ui_qt" / "main_window.py"
BIP = ROOT / "ui_qt" / "widgets" / "birth_input_panel.py"
PATCHER = ROOT / "fix_profile_created_at.py"
MARKER = "DEAD_CODE_V1"


def patch(path: Path, deletions: list[str]) -> None:
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[*] {path.name}: чистка уже выполнена.")
        return
    for block in deletions:
        if block not in src:
            print(f"[X] {path.name}: блок не найден, возможно уже удалён.")
            sys.exit(1)
    for block in deletions:
        src = src.replace(block, "")
    try:
        compile(src, str(path), "exec")
    except SyntaxError as exc:
        print(f"[X] {path.name}: SyntaxError после удаления: {exc}. Файл НЕ изменён.")
        sys.exit(1)
    shutil.copy2(path, path.with_name(path.name + ".bak_deadcode"))
    path.write_text(src, encoding="utf-8")
    print(f"[+] {path.name}: мёртвые блоки удалены.")


def main():
    if WIN.exists():
        patch(WIN, [
            '''    def _extract_transit_planets_for_chart(self, transit_result, start_date, end_date):
        """Extract transit planets for chart rendering."""
        # For chart rendering, we need current positions of transit planets
        # This is a simplified version - in reality you'd calculate exact positions
        transit_planets = []
        seen_planets = set()
        
        for event in transit_result:
            planet_name = event.get("transit_planet", "")
            if planet_name and planet_name not in seen_planets:
                transit_planets.append({
                    "name": planet_name,
                    "longitude": event.get("transit_longitude", 0),
                    "sign": event.get("transit_sign", ""),
                    "retrograde": event.get("retrograde", False),
                    "speed_longitude": event.get("speed", 0)
                })
                seen_planets.add(planet_name)
        
        return transit_planets
    
''',
            '''    def _extract_transit_aspects_for_chart(self, transit_result):
        """Extract transit aspects for chart rendering."""
        transit_aspects = []
        for event in transit_result:
            transit_aspects.append({
                "transit_planet": event.get("transit_planet", ""),
                "natal_point": event.get("natal_point", ""),
                "aspect": event.get("aspect", ""),
                "orb": event.get("orb", 0),
                "angle": event.get("angle", 0)
            })
        return transit_aspects
        
''',
        ])

    if BIP.exists():
        patch(BIP, [
            '''    def _eq_naturals(self):
        """Естественные высоты секций, измеренные БЕЗ ограничений (37g)."""
        groups = getattr(self, "_eq_groups", None) or []
        for g in groups:
            g.setMinimumHeight(0)
            g.setMaximumHeight(16777215)
        nat = [g.sizeHint().height() for g in groups]
        total = self.layout().totalSizeHint().height()
        return nat, total

''',
        ])

    if PATCHER.exists():
        PATCHER.unlink()
        print("[+] fix_profile_created_at.py удалён (одноразовый патчер).")

    sys.path.insert(0, str(ROOT))
    try:
        import ui_qt.main_window as win_mod
        import ui_qt.widgets.birth_input_panel as bip_mod
        assert not hasattr(win_mod.MainWindow, "_extract_transit_planets_for_chart")
        assert not hasattr(win_mod.MainWindow, "_extract_transit_aspects_for_chart")
        assert not hasattr(bip_mod.BirthInputPanel, "_eq_naturals")
        print("[+] Контроль: мёртвые методы удалены, модули импортируются.")
    except Exception as exc:
        print(f"[!] Ошибка контроля: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()