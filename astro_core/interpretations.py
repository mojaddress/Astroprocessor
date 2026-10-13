"""
Локальная база астрологических интерпретаций (Вариант C, локальная часть).

Формулировки — обобщённая классическая традиция западной астрологии
(Базhaf, Подводный, Арройо, Радьяр — в пересказе, без дословных цитат).
Интерпретации носят справочно-символический характер и не являются
гарантированными предсказаниями (см. DISCLAIMER).
"""

from .constants import get_planet_name_ru, get_sign_name_ru

DISCLAIMER = (
    "Примечание: интерпретации основаны на классической астрологической "
    "традиции и носят справочно-символический характер. Они не являются "
    "научно подтверждёнными утверждениями или гарантиями событий."
)

# ------------------------------------------------------------ Аспекты
ASPECT_INFO = {
    "conjunction": {
        "name": "Соединение",
        "phrase": "в соединении с",
        "harmony": "neutral",
        "meaning": "слияние и взаимное усиление энергий: обе темы звучат ярко и одновременно.",
    },
    "sextile": {
        "name": "Секстиль",
        "phrase": "в секстиле с",
        "harmony": "harmonious",
        "meaning": "мягкая поддержка: возможности, которыми легко воспользоваться при желании.",
    },
    "square": {
        "name": "Квадрат",
        "phrase": "в квадрате с",
        "harmony": "tense",
        "meaning": "внутреннее напряжение: требует действий и интеграции противоположных стремлений.",
    },
    "trine": {
        "name": "Тригон",
        "phrase": "в трине с",
        "harmony": "harmonious",
        "meaning": "естественный поток: талант и поддержка, работающие без усилий.",
    },
    "opposition": {
        "name": "Оппозиция",
        "phrase": "в оппозиции с",
        "harmony": "tense",
        "meaning": "полюса: нужен баланс двух тем, часто через партнёров и внешние обстоятельства.",
    },
}

# ------------------------------------------------------------ Планеты
PLANET_KEYWORDS = {
    "Sun": "воля, эго, жизненная сила",
    "Moon": "эмоции, инстинкты, забота",
    "Mercury": "мышление, общение, обучение",
    "Venus": "любовь, красота, деньги",
    "Mars": "действие, энергия, напор",
    "Jupiter": "рост, удача, масштаб",
    "Saturn": "дисциплина, границы, зрелость",
    "Uranus": "свобода, перемены, озарения",
    "Neptune": "мечты, интуиция, иллюзии",
    "Pluto": "трансформация, власть, кризисы",
    "MeanNode": "вектор развития жизни",
    "TrueNode": "вектор развития жизни",
    "SouthNode": "багаж прошлого опыта",
    "Chiron": "рана и целительство",
    "PartOfFortune": "удача и самореализация",
}

# ------------------------------------------------------------ Знаки
SIGN_KEYWORDS = {
    "Aries": "импульс и инициатива",
    "Taurus": "устойчивость и чувственность",
    "Gemini": "подвижность и любознательность",
    "Cancer": "чувствительность и привязанность",
    "Leo": "творчество и лидерство",
    "Virgo": "точность и практичность",
    "Libra": "партнёрство и гармония",
    "Scorpio": "глубина и страстность",
    "Sagittarius": "широта взглядов и энтузиазм",
    "Capricorn": "целеустремлённость и ответственность",
    "Aquarius": "независимость и новаторство",
    "Pisces": "сострадание и воображение",
}

# ------------------------------------------------------------ Дома
HOUSE_KEYWORDS = {
    1: "личность и самовыражение",
    2: "ресурсы и ценности",
    3: "коммуникации и обучение",
    4: "дом и корни",
    5: "творчество и романтика",
    6: "работа и здоровье",
    7: "партнёрство и брак",
    8: "кризисы и трансформация",
    9: "мировоззрение и дальние горизонты",
    10: "карьера и статус",
    11: "друзья и планы",
    12: "уединение и подсознание",
}


# ============================================================ Функции
def aspect_tooltip(aspect: str, point_a: str, point_b: str) -> str:
    """Короткий тултип для линии аспекта."""
    info = ASPECT_INFO.get(aspect, {})
    ru_a = get_planet_name_ru(point_a)
    ru_b = get_planet_name_ru(point_b)
    phrase = info.get("phrase", "в аспекте с")
    meaning = info.get("meaning", "взаимодействие двух тем.")
    return f"{ru_a} {phrase} {ru_b}\n{meaning}"


def interpret_synastry_aspect(point_a: str, name_a: str,
                              point_b: str, name_b: str, aspect: str) -> str:
    """Интерпретация межкартового аспекта для синастрии."""
    info = ASPECT_INFO.get(aspect, {})
    ru_a = get_planet_name_ru(point_a)
    ru_b = get_planet_name_ru(point_b)
    kw_a = PLANET_KEYWORDS.get(point_a, "тема")
    kw_b = PLANET_KEYWORDS.get(point_b, "тема")
    phrase = info.get("phrase", "в аспекте с")
    meaning = info.get("meaning", "взаимодействие двух тем.")
    return (f"{ru_a} ({name_a}: {kw_a}) {phrase} {ru_b} ({name_b}: {kw_b}) — {meaning}")


def summarize_synastry(aspects, name_a: str, name_b: str, top_n: int = 8) -> str:
    """Текстовая сводка синастрии: сильные аспекты первыми."""
    if not aspects:
        return "Точных межкартовых аспектов не найдено."
    ordered = sorted(aspects, key=lambda a: abs(a.get("score", 0)), reverse=True)
    lines = [f"Ключевые связи между {name_a} и {name_b}:"]
    for a in ordered[:top_n]:
        lines.append("• " + interpret_synastry_aspect(
            a["point_a"], "A" if a.get("point_a_chart") == "A" else "B",
            a["point_b"], "B" if a.get("point_b_chart") == "B" else "A",
            a["aspect"]))
    return "\n".join(lines)


def _planet_line(planet: dict) -> str:
    name = planet.get("name", "?")
    sign = planet.get("sign", "")
    house = planet.get("house")
    kw_p = PLANET_KEYWORDS.get(name, "тема")
    kw_s = SIGN_KEYWORDS.get(sign, "знак")
    house_part = f", дом {house}: {HOUSE_KEYWORDS.get(house, 'сфера жизни')}" if house else ""
    return (f"{get_planet_name_ru(name)} в знаке {get_sign_name_ru(sign)} "
            f"({kw_s}){house_part} — {kw_p}.")


def summarize_natal(chart: dict) -> str:
    """Описание человека по натальной карте (локальная база)."""
    planets = {p.get("name"): p for p in chart.get("planets", [])}
    name = chart.get("birth", {}).get("name", "Человек")
    sections = [f"Портрет: {name}"]

    core = [planets[k] for k in ("Sun", "Moon") if k in planets]
    asc = next((p for p in chart.get("additional_points", []) if p.get("name") == "ASC"), None)
    if core or asc:
        lines = []
        for p in core:
            lines.append(_planet_line(p))
        if asc:
            lines.append(f"Асцендент в знаке {get_sign_name_ru(asc.get('sign', ''))} — "
                         f"внешнее поведение и первое впечатление: "
                         f"{SIGN_KEYWORDS.get(asc.get('sign', ''), 'стиль общения')}.")
        sections.append("Ядро личности:\n" + "\n".join(lines))

    pairs = [
        ("Мышление и общение", ("Mercury",)),
        ("Чувства и отношения", ("Venus",)),
        ("Действие и энергия", ("Mars",)),
        ("Рост и задачи", ("Jupiter", "Saturn")),
    ]
    for title, keys in pairs:
        lines = [_planet_line(planets[k]) for k in keys if k in planets]
        if lines:
            sections.append(title + ":\n" + "\n".join(lines))

    aspects = chart.get("aspects", [])
    if aspects:
        top = sorted(aspects, key=lambda a: abs(a.get("orb", 99)))[:5]
        lines = []
        for a in top:
            info = ASPECT_INFO.get(a.get("aspect"), {})
            lines.append(f"{get_planet_name_ru(a['point_a'])} "
                         f"{info.get('phrase', 'в аспекте с')} "
                         f"{get_planet_name_ru(a['point_b'])} — "
                         f"{info.get('meaning', '')}")
        sections.append("Ключевые аспекты:\n" + "\n".join(lines))

    return "\n\n".join(sections)


def summarize_transits(chart: dict, transit_events: list) -> str:
    """Описание текущего влияния транзитов (локальная база)."""
    if not transit_events:
        return "Существенных точных транзитов на выбранный период не найдено."
    harmonious = [e for e in transit_events
                  if ASPECT_INFO.get(e.get("aspect"), {}).get("harmony") == "harmonious"]
    tense = [e for e in transit_events
             if ASPECT_INFO.get(e.get("aspect"), {}).get("harmony") == "tense"]
    name = chart.get("birth", {}).get("name", "Человек")
    sections = [f"Транзитное влияние для: {name}"]

    if harmonious:
        lines = []
        for e in harmonious[:6]:
            info = ASPECT_INFO.get(e.get("aspect"), {})
            lines.append(f"{get_planet_name_ru(e.get('transit_planet', ''))} "
                         f"{info.get('phrase', '')} "
                         f"{get_planet_name_ru(e.get('natal_point', ''))} — "
                         f"{info.get('meaning', '')}")
        sections.append("Поддерживающие периоды (традиционно: время для действий "
                        "по соответствующим темам):\n" + "\n".join(lines))
    if tense:
        lines = []
        for e in tense[:6]:
            info = ASPECT_INFO.get(e.get("aspect"), {})
            lines.append(f"{get_planet_name_ru(e.get('transit_planet', ''))} "
                         f"{info.get('phrase', '')} "
                         f"{get_planet_name_ru(e.get('natal_point', ''))} — "
                         f"{info.get('meaning', '')}")
        sections.append("Напряжённые периоды (традиционно: время осторожности, "
                        "пересмотра и отдыха по соответствующим темам):\n" + "\n".join(lines))

    sections.append("Общая рекомендация традиции: в поддерживающие периоды легче "
                    "начинать и вкладываться в темы аспектов; в напряжённые — "
                    "разумнее завершать старое и избегать рисков.")
    return "\n\n".join(sections)

# ============================================================
# Профиль натала: темперамент, черты, сферы деятельности (итерация 23)
# ============================================================

ELEMENTS = {
    "Aries": "огонь", "Leo": "огонь", "Sagittarius": "огонь",
    "Taurus": "земля", "Virgo": "земля", "Capricorn": "земля",
    "Gemini": "воздух", "Libra": "воздух", "Aquarius": "воздух",
    "Cancer": "вода", "Scorpio": "вода", "Pisces": "вода",
}

ELEMENT_TRAITS = {
    "огонь": "энергичность, импульсивность, инициативность",
    "земля": "практичность, устойчивость, надёжность",
    "воздух": "коммуникативность, гибкость мышления, любознательность",
    "вода": "чувствительность, интуиция, эмпатия",
}

PROFESSION_HINTS = {
    "Mercury": ["письмо и редактура", "преподавание", "аналитика", "торговля"],
    "Venus": ["искусство и дизайн", "музыка", "индустрия красоты", "финансы"],
    "Mars": ["спорт", "техника и инженерия", "хирургия", "спасательные службы"],
    "Jupiter": ["образование", "право", "международные проекты", "издательское дело"],
    "Saturn": ["управление", "строительство", "системная работа", "госструктуры"],
    "Uranus": ["IT и инновации", "авиация", "исследования"],
    "Neptune": ["искусство", "психология", "морские профессии", "благотворительность"],
    "Pluto": ["кризис-менеджмент", "расследования", "трансформационный консалтинг"],
}

HOUSE_PROFESSIONS = {
    1: "самостоятельные проекты и спорт",
    2: "финансы и ремёсла",
    3: "коммуникации и обучение",
    4: "недвижимость и семейное дело",
    5: "творчество и работа с детьми",
    6: "медицина и сервис",
    7: "консультации и партнёрства",
    8: "финансовые расследования и аудит",
    9: "наука, преподавание, зарубежье",
    10: "карьера и руководство",
    11: "команды и социальные проекты",
    12: "уединённый труд и психология",
}


def natal_profile(chart: dict) -> dict:
    """Темперамент по стихиям, черты, сферы деятельности (традиция)."""
    planets = chart.get("planets", [])
    elements = {"огонь": 0, "земля": 0, "воздух": 0, "вода": 0}
    for p in planets:
        el = ELEMENTS.get(p.get("sign", ""))
        if el:
            elements[el] += 1
    traits = [ELEMENT_TRAITS[el] for el, cnt in
              sorted(elements.items(), key=lambda kv: -kv[1]) if cnt]
    asc = next((x for x in chart.get("additional_points", [])
                if x.get("name") == "ASC"), None)
    if asc:
        traits.append("внешняя подача — " +
                      SIGN_KEYWORDS.get(asc.get("sign", ""), "по знаку асцендента"))
    professions = []
    for p in planets:
        house = p.get("house")
        if house in HOUSE_PROFESSIONS:
            professions.append(HOUSE_PROFESSIONS[house])
        professions.extend(PROFESSION_HINTS.get(p.get("name", ""), []))
    seen = set()
    professions = [x for x in professions if not (x in seen or seen.add(x))]
    notes = []
    retro = [p for p in planets if p.get("retrograde")]
    if retro:
        notes.append("ретроградные планеты: " +
                     ", ".join(get_planet_name_ru(p["name"]) for p in retro) +
                     " — традиция читает как внутреннюю переработку темы")
    return {"traits": traits, "professions": professions[:8],
            "notes": notes, "elements": elements}


def format_natal_profile(chart: dict) -> str:
    prof = natal_profile(chart)
    lines = ["Предрасположенности и характер (локальная база):"]
    lines.append("Черты характера: " +
                 ("; ".join(prof["traits"]) if prof["traits"] else "—"))
    lines.append("Подходящие сферы деятельности (традиция): " +
                 ("; ".join(prof["professions"]) if prof["professions"] else "—"))
    for n in prof["notes"]:
        lines.append("Примечание: " + n)
    return "\n".join(lines)
