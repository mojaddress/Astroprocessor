import sys
from PyQt6.QtWidgets import QApplication
from ui_qt.main_window import MainWindow
from datetime import date

app = QApplication(sys.argv)
window = MainWindow()
window.show()

window._load_profile('Сергей')
window._on_calculate_chart()

svg = window._current_chart_result.get('svg', '')
print('SVG length:', len(svg))

# Check for planet text labels
for name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'MeanNode', 'SouthNode', 'ASC', 'MC']:
    count = svg.count('>' + name + '<')
    if count > 0:
        print(name + ': ' + str(count) + ' labels')

# Write SVG to file for inspection
with open('debug_svg.svg', 'w', encoding='utf-8') as f:
    f.write(svg)
print('Written to debug_svg.svg')

app.quit()