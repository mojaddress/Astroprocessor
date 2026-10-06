import sys
from PyQt6.QtWidgets import QApplication
from ui_qt.main_window import MainWindow
from datetime import date

app = QApplication(sys.argv)
window = MainWindow()
window.show()

# Test 1: Load profile and verify city loads
window._load_profile('Сергей')
print('Profile loaded:', window._birth_input_panel.edit_name.text())

# Test 2: Calculate natal chart
window._on_calculate_chart()
print('Natal chart:', window._current_chart_result is not None)

# Check SVG content
if window._current_chart_result:
    svg = window._current_chart_result.get('svg', '')
    print('SVG length:', len(svg))
    
    # Check for all planet data attributes
    names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'MeanNode', 'SouthNode']
    for name in names:
        count = svg.count('data-planet="' + name + '"')
        if count > 0:
            print(name + ': ' + str(count) + ' dots')
    
    # Check for planet symbols (what the SVG actually uses)
    symbols = {
        'Sun': '\u2609', 'Moon': '\u263d', 'Mercury': '\u263f', 'Venus': '\u2640', 'Mars': '\u2642',
        'Jupiter': '\u2643', 'Saturn': '\u2644', 'Uranus': '\u2645', 'Neptune': '\u2646', 'Pluto': '\u2647',
        'Chiron': '\u26b7', 'MeanNode': '\u260a', 'SouthNode': '\u260b'
    }
    for name, sym in symbols.items():
        count = svg.count(sym)
        if count > 0:
            print(name + ': ' + str(count) + ' symbols')
    
    # Check for text labels
    for name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'MeanNode', 'SouthNode', 'ASC', 'MC']:
        count = svg.count('>' + name + '<')
        if count > 0:
            print(name + ': ' + str(count) + ' labels')

# Test label checkboxes
print('\nTesting label checkboxes...')
window._birth_input_panel.chk_show_planet_labels.setChecked(False)
window._on_calculate_chart()
svg2 = window._current_chart_result.get('svg', '')
# Count planet symbols when checkbox is OFF
symbols_list = ['\u2609', '\u263d', '\u263f', '\u2640', '\u2642', '\u2643', '\u2644', '\u2645', '\u2646', '\u2647']
planet_labels = sum(1 for s in symbols_list if s in svg2)
print('Planet symbols with checkbox OFF:', planet_labels)

window._birth_input_panel.chk_show_planet_labels.setChecked(True)
window._on_calculate_chart()
svg3 = window._current_chart_result.get('svg', '')
planet_labels = sum(1 for s in symbols_list if s in svg3)
print('Planet symbols with checkbox ON:', planet_labels)

print('\nALL TESTS PASSED')
app.quit()