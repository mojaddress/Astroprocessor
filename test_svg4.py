import re
from astro_core.controllers import ChartController
from astro_core.controllers.chart_controller import BirthData, ChartSettings
from datetime import date, time

chart_ctrl = ChartController()
birth = BirthData(name='Test', birth_date=date(1990, 5, 15), birth_time=time(14, 30), latitude=55.7558, longitude=37.6173, utc_offset_hours=3.0)
settings = ChartSettings(house_system='placidus', zodiac='tropical', ayanamsha='lahiri', include_chiron=True, include_nodes=True, include_part_of_fortune=True, include_angles=True, ephe_path='ephe')
result = chart_ctrl.calculate_chart(birth, settings, 'full', include_svg=True)
svg = result.get('svg', '')

# Write full SVG to file
with open('full_output.svg', 'w', encoding='utf-8') as f:
    f.write(svg)
print('Written full_output.svg, length:', len(svg))