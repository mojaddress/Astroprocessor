import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from astro_core.chart import build_natal_chart
from astro_core.ephemeris import SWISSEPH_AVAILABLE, SWISSEPH_IMPORT_ERROR
from astro_core.time_service import parse_local_datetime, datetime_to_jd
from astro_core.aspects import calculate_aspects
from astro_core.transits import get_transit_calendar, find_transit_events


def selftest():
    """
    Простая самопроверка базовой логики без обязательного расчёта эфемерид.
    """

    try:
        local_dt, utc_dt = parse_local_datetime("1990-05-15", "14:30", 3)

        if local_dt != datetime(1990, 5, 15, 14, 30, 0):
            raise AssertionError("Local datetime parsing failed.")

        if utc_dt != datetime(1990, 5, 15, 11, 30, 0):
            raise AssertionError("UTC conversion failed.")

        jd = datetime_to_jd(datetime(2000, 1, 1, 12, 0, 0))

        if abs(jd - 2451545.0) > 1e-6:
            raise AssertionError("Julian Day calculation failed.")

        points = [
            {"name": "A", "longitude": 0.0},
            {"name": "B", "longitude": 90.5},
        ]

        settings = {
            "enabled_aspects": ["square"],
            "orbs": {"square": 1.0},
        }

        aspects = calculate_aspects(points, settings)

        if len(aspects) != 1:
            raise AssertionError("Aspect calculation failed.")

        if aspects[0]["aspect"] != "square":
            raise AssertionError("Aspect type detection failed.")

        print("Selftest OK")
        return 0

    except Exception as error:
        print(f"Selftest FAILED: {error}")
        return 1

def format_transit_calendar(calendar, group_by_date=True):
    """
    Форматирует календарь транзитов для читаемого вывода в терминал.
    """

    if not calendar:
        return "No transits found for the specified period."

    lines = []

    if group_by_date:
        # Группируем транзиты по датам
        dates = {}
        for entry in calendar:
            date = entry.get("date", "unknown")
            if date not in dates:
                dates[date] = []
            dates[date].append(entry)

        for date in sorted(dates.keys()):
            lines.append(f"\n{date}:")
            for entry in dates[date]:
                transit_planet = entry.get("transit_planet", "?")
                aspect = entry.get("aspect", "?")
                natal_point = entry.get("natal_point", "?")
                orb = entry.get("orb", "?")
                strength = entry.get("strength", "?")

                lines.append(
                    f"  {transit_planet} {aspect} {natal_point} "
                    f"(orb {orb}°, strength {strength})"
                )
    else:
        for entry in calendar:
            date = entry.get("date", "unknown")
            transit_planet = entry.get("transit_planet", "?")
            aspect = entry.get("aspect", "?")
            natal_point = entry.get("natal_point", "?")
            orb = entry.get("orb", "?")

            lines.append(
                f"{date}: {transit_planet} {aspect} {natal_point} (orb {orb}°)"
            )

    return "\n".join(lines)

def format_transit_events(events, group_by_date=True):
    """
    Форматирует события транзитов для читаемого вывода в терминал.

    Каждое событие содержит точную дату и время аспекта,
    транзитную планету, аспект, натальную точку и направление движения.

    R = retrograde (ретроградное движение)
    D = direct (директное движение)
    """

    if not events:
        return "No transit events found for the specified period."

    lines = []

    if group_by_date:
        # Группируем события по датам
        dates = {}
        for event in events:
            # Извлекаем дату из exact_datetime (формат ISO: YYYY-MM-DDTHH:MM:SS)
            date_part = event["exact_datetime"].split("T")[0]
            if date_part not in dates:
                dates[date_part] = []
            dates[date_part].append(event)

        for date in sorted(dates.keys()):
            lines.append(f"\n{date}:")
            # Сортируем события внутри дня по времени
            for event in sorted(dates[date], key=lambda e: e["exact_datetime"]):
                time_part = event["exact_datetime"].split("T")[1]
                direction_marker = "R" if event["direction"] == "retrograde" else "D"
                lines.append(
                    f"  {time_part} [{direction_marker}] "
                    f"{event['transit_planet']} {event['aspect']} {event['natal_point']}"
                )
    else:
        for event in events:
            direction_marker = "R" if event["direction"] == "retrograde" else "D"
            lines.append(
                f"{event['exact_datetime']} [{direction_marker}] "
                f"{event['transit_planet']} {event['aspect']} {event['natal_point']}"
            )

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Astro Processor - modular version"
    )

    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run basic internal checks",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Calculate demo chart",
    )

    parser.add_argument("--name", help="Person or chart name")
    parser.add_argument("--date", help="Birth date YYYY-MM-DD")
    parser.add_argument("--time", help="Birth time HH:MM")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")

    parser.add_argument(
        "--utc-offset",
        type=float,
        help="UTC offset in hours, e.g. 3 for UTC+3, -5 for UTC-5",
    )

    parser.add_argument(
        "--timezone",
        default="manual",
        help="Timezone name, informational at this stage",
    )

    parser.add_argument(
        "--zodiac",
        default="tropical",
        help="Zodiac type. Currently only tropical is fully supported.",
    )

    parser.add_argument(
        "--house-system",
        default="placidus",
        help="House system: placidus, koch, equal, whole_sign, porphyry",
    )

    parser.add_argument(
        "--node-type",
        default="mean",
        choices=["mean", "true"],
        help="Lunar node type",
    )

    parser.add_argument(
        "--no-chiron",
        action="store_true",
        help="Do not include Chiron",
    )

    parser.add_argument(
        "--no-nodes",
        action="store_true",
        help="Do not include lunar nodes",
    )

    parser.add_argument(
        "--no-fortune",
        action="store_true",
        help="Do not include Part of Fortune",
    )

    parser.add_argument(
        "--no-angles",
        action="store_true",
        help="Do not include ASC/MC angles",
    )

    parser.add_argument(
        "--ephe-path",
        help="Path to Swiss Ephemeris data folder",
    )

    parser.add_argument(
        "--output",
        help="Output JSON file path",
    )

    # Аргументы для режима транзитов
    parser.add_argument(
        "--transits",
        action="store_true",
        help="Enable transit calendar mode",
    )

    parser.add_argument(
        "--start-date",
        help="Transit period start date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end-date",
        help="Transit period end date (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--transit-date",
        help="Single transit date (YYYY-MM-DD). Alternative to --start-date/--end-date",
    )

    parser.add_argument(
        "--transit-days",
        type=int,
        default=7,
        help="Number of days for transit calendar if no dates specified (default: 7)",
    )

    parser.add_argument(
        "--transit-utc-offset",
        type=float,
        default=0,
        help="UTC offset for transit dates (default: 0)",
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output transit calendar as JSON instead of readable text",
    )

    parser.add_argument(
        "--precise",
        action="store_true",
        help="Use precise transit events with exact dates and times (slower, use for short periods)",
    )

    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if not SWISSEPH_AVAILABLE:
        print("ERROR: Swiss Ephemeris library is not available.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Install with:", file=sys.stderr)
        print("", file=sys.stderr)
        print("    py -3.11 -m pip install pyswisseph", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Import error: {SWISSEPH_IMPORT_ERROR}", file=sys.stderr)
        sys.exit(1)

    if args.demo:
        birth = {
            "name": "Demo Person",
            "date": "1990-05-15",
            "time": "14:30",
            "latitude": 55.7558,
            "longitude": 37.6173,
            "utc_offset_hours": 3,
            "timezone": "Europe/Moscow",
        }
    else:
        required_present = (
            args.date is not None
            and args.time is not None
            and args.lat is not None
            and args.lon is not None
            and args.utc_offset is not None
        )

        if not required_present:
            print("No input data provided.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Use demo mode:", file=sys.stderr)
            print("", file=sys.stderr)
            print("    py -3.11 run.py --demo", file=sys.stderr)
            print("", file=sys.stderr)
            print("Or provide birth data:", file=sys.stderr)
            print("", file=sys.stderr)
            print(
                "    py -3.11 run.py "
                "--name \"Person\" "
                "--date 1990-05-15 "
                "--time 14:30 "
                "--lat 55.7558 "
                "--lon 37.6173 "
                "--utc-offset 3",
                file=sys.stderr,
            )
            sys.exit(1)

        birth = {
            "name": args.name or "Chart",
            "date": args.date,
            "time": args.time,
            "latitude": args.lat,
            "longitude": args.lon,
            "utc_offset_hours": args.utc_offset,
            "timezone": args.timezone,
        }

    settings = {}

    settings["zodiac"] = args.zodiac
    settings["house_system"] = args.house_system
    settings["node_type"] = args.node_type

    if args.no_chiron:
        settings["include_chiron"] = False

    if args.no_nodes:
        settings["include_nodes"] = False

    if args.no_fortune:
        settings["include_part_of_fortune"] = False

    if args.no_angles:
        settings["include_angles"] = False

    if args.ephe_path:
        settings["ephe_path"] = args.ephe_path

    # Обработка режима транзитов
    if args.transits:
        if not SWISSEPH_AVAILABLE:
            print("ERROR: Swiss Ephemeris is not available.", file=sys.stderr)
            sys.exit(1)

        # Определяем период транзитов
        if args.transit_date:
            # Одна конкретная дата
            start_date = args.transit_date
            end_date = args.transit_date
        elif args.start_date and args.end_date:
            # Указанный период
            start_date = args.start_date
            end_date = args.end_date
        elif args.start_date:
            # Только начальная дата — добавляем transit_days дней
            start_dt = datetime.fromisoformat(args.start_date)
            end_dt = start_dt + timedelta(days=args.transit_days - 1)
            start_date = args.start_date
            end_date = end_dt.strftime("%Y-%m-%d")
        else:
            # По умолчанию: сегодня + transit_days дней
            today = datetime.now()
            start_date = today.strftime("%Y-%m-%d")
            end_dt = today + timedelta(days=args.transit_days - 1)
            end_date = end_dt.strftime("%Y-%m-%d")

        # Строим натальную карту
        try:
            natal = build_natal_chart(birth, settings)
        except Exception as error:
            print(f"ERROR building natal chart: {error}", file=sys.stderr)
            sys.exit(1)

        # Добавляем настройки для транзитов
        transit_settings = dict(settings)
        transit_settings["transit_utc_offset"] = args.transit_utc_offset

                # Получаем транзиты в зависимости от режима
        if args.precise:
            # Точный режим: события с точными датами и временем
            try:
                events = find_transit_events(
                    natal["objects"],
                    start_date,
                    end_date,
                    transit_settings,
                )
            except Exception as error:
                print(f"ERROR calculating precise transits: {error}", file=sys.stderr)
                sys.exit(1)

            # Выводим результат
            if args.json_output:
                output_json = json.dumps(events, ensure_ascii=False, indent=2)
                if args.output:
                    output_path = Path(args.output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(output_json, encoding="utf-8")
                    print(f"Precise transit events saved to: {output_path}")
                else:
                    print(output_json)
            else:
                print(f"\nPrecise Transit Events for: {birth.get('name', 'Chart')}")
                print(f"Period: {start_date} to {end_date}")
                print(f"Total events: {len(events)}")
                print(format_transit_events(events))
        else:
            # Быстрый режим: календарь по дням
            try:
                calendar = get_transit_calendar(
                    natal["objects"],
                    start_date,
                    end_date,
                    transit_settings,
                )
            except Exception as error:
                print(f"ERROR calculating transits: {error}", file=sys.stderr)
                sys.exit(1)

            # Выводим результат
            if args.json_output:
                output_json = json.dumps(calendar, ensure_ascii=False, indent=2)
                if args.output:
                    output_path = Path(args.output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(output_json, encoding="utf-8")
                    print(f"Transit calendar saved to: {output_path}")
                else:
                    print(output_json)
            else:
                print(f"\nTransit Calendar for: {birth.get('name', 'Chart')}")
                print(f"Period: {start_date} to {end_date}")
                print(f"Total entries: {len(calendar)}")
                print(format_transit_calendar(calendar))

        return

    # Если не режим транзитов, продолжаем обычную обработку натальной карты

    try:
        result = build_natal_chart(birth, settings)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding="utf-8")
        print(f"Chart saved to: {output_path}")
    else:
        print(output_json)

    if result.get("warnings"):
        print("", file=sys.stderr)
        print("Warnings:", file=sys.stderr)
        for warning in result["warnings"]:
            print(f"- {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()