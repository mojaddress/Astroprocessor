"""Тест для проверки рендеринга карт"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Диагностика рендеринга ===")
print(f"Python: {sys.version}")
print(f"Рабочая папка: {os.getcwd()}")

# Проверяем откуда загружается модуль
try:
    from astro_core.chart_svg import render_natal_chart_svg, render_transit_chart_svg
    import astro_core.chart_svg as chart_svg_module
    print(f"✅ chart_svg загружен из: {chart_svg_module.__file__}")
    
    # Проверяем наличие функции
    if hasattr(chart_svg_module, 'render_natal_chart_svg'):
        print("✅ render_natal_chart_svg доступна")
    else:
        print("❌ render_natal_chart_svg НЕ найдена")
        
    if hasattr(chart_svg_module, 'render_transit_chart_svg'):
        print("✅ render_transit_chart_svg доступна")
    else:
        print("❌ render_transit_chart_svg НЕ найдена")
        
    # Проверяем источник функции (чтобы увидеть, что она обновлена)
    import inspect
    source_file = inspect.getfile(chart_svg_module.render_natal_chart_svg)
    print(f"📁 Файл с функцией: {source_file}")
    
    # Проверяем, есть ли в коде проверка should_show_label
    source_code = inspect.getsource(chart_svg_module.render_natal_chart_svg)
    if 'should_show_label' in source_code:
        print("✅ В коде есть проверка should_show_label (обновлённая версия)")
    else:
        print("❌ В коде НЕТ проверки should_show_label (старая версия)")
        
    if 'devicePixelRatio' in open('ui_qt/widgets/chart_view.py', 'r', encoding='utf-8').read():
        print("✅ В chart_view есть devicePixelRatio (обновлённая версия)")
    else:
        print("❌ В chart_view НЕТ devicePixelRatio (старая версия)")
        
    print("\n=== Создание тестовой натальной карты ===")
    
    # Создаём тестовые данные
    test_chart_data = {
        "planets": [
            {
                "name": "Sun",
                "longitude": 45.5,
                "sign": "Taurus",
                "degree_in_sign": 15.5,
                "house": 2,
                "retrograde": False,
                "speed_longitude": 0.98
            },
            {
                "name": "Moon",
                "longitude": 120.3,
                "sign": "Leo",
                "degree_in_sign": 0.3,
                "house": 5,
                "retrograde": False,
                "speed_longitude": 13.2
            },
            {
                "name": "Mercury",
                "longitude": 52.8,
                "sign": "Taurus",
                "degree_in_sign": 22.8,
                "house": 2,
                "retrograde": False,
                "speed_longitude": 1.1
            }
        ],
        "houses": [
            {"house": 1, "longitude": 0.0},
            {"house": 2, "longitude": 30.0},
            {"house": 3, "longitude": 60.0}
        ],
        "aspects": [],
        "additional_points": [
            {
                "name": "ASC",
                "longitude": 0.0,
                "sign": "Aries",
                "degree_in_sign": 0.0,
                "house": 1,
                "type": "angle"
            }
        ]
    }

    # Генерируем натальную карту
    svg_natal = render_natal_chart_svg(
        test_chart_data,
        show_planet_labels=True,
        label_mode="symbols"
    )

    # Сохраняем для проверки
    output_file = 'test_natal_output.svg'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_natal)

    print(f"✅ Натальная карта создана: {output_file}")
    print(f"📄 Размер SVG: {len(svg_natal)} символов")

    # Проверяем, есть ли текст планет в SVG
    planet_symbols_found = []
    for symbol in ["☉", "☽", "☿"]:  # Солнце, Луна, Меркурий
        if symbol in svg_natal:
            planet_symbols_found.append(symbol)
    
    if planet_symbols_found:
        print(f"✅ Знаки планет найдены в натальной карте: {', '.join(planet_symbols_found)}")
    else:
        print("❌ Знаки планет НЕ найдены в натальной карте")
        # Проверяем, есть ли вообще какие-то планеты
        if "circle" in svg_natal:
            print("⚠️  Но в карте есть элементы <circle> (точки планет)")
        if "text" in svg_natal:
            print("⚠️  Но в карте есть элементы <text> (текст)")

    # Проверяем viewBox
    import re
    viewbox_match = re.search(r'viewBox="([^"]+)"', svg_natal)
    if viewbox_match:
        print(f"📐 ViewBox: {viewbox_match.group(1)}")
    
    # Ищем размеры
    width_match = re.search(r'width="(\d+)"', svg_natal)
    height_match = re.search(r'height="(\d+)"', svg_natal)
    if width_match and height_match:
        print(f"📏 Размеры: {width_match.group(1)}x{height_match.group(1)}")
    
    # Ищем наличие devicePixelRatio в chart_view
    print("\n=== Проверка chart_view.py ===")
    try:
        with open('ui_qt/widgets/chart_view.py', 'r', encoding='utf-8') as f:
            chart_view_content = f.read()
        
        if 'devicePixelRatio' in chart_view_content:
            print("✅ В chart_view есть поддержка HiDPI")
        else:
            print("❌ В chart_view НЕТ поддержки HiDPI")
            
        if 'setDevicePixelRatio' in chart_view_content:
            print("✅ В chart_view есть setDevicePixelRatio")
        else:
            print("❌ В chart_view НЕТ setDevicePixelRatio")
            
        # Проверяем размер
        lines = chart_view_content.split('\n')
        print(f"📄 chart_view.py: {len(lines)} строк")
        
    except Exception as e:
        print(f"❌ Ошибка чтения chart_view.py: {e}")
    
    print("\n=== Рекомендации ===")
    print("1. Откройте файл test_natal_output.svg в браузере")
    print("2. Проверьте, видны ли символы планет ☉ ☽ ☿")
    print("3. Проверьте качество линий (должны быть чёткими)")
    
    print("\n✅ Диагностика завершена")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()