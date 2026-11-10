"""Carthaginians: "Elephant, Camel, and Naval civilization" (RoR string 120163).

• Start the game with +50 of all resources
• Academy units and elephant units +25% hit points, Camel Riders +15% hit points
• Fire Galley +25% attack
• Transport ships move 25% faster
• Nobility free (requires Government Center)
Team Bonus: Academies work 20% faster
"""

from crucible.bonuses.model import Modifier, Stat, flat, pct

CIV = "carthaginians"

MODIFIERS = (
    Modifier(flat(50), Stat.START_RESOURCES, (), ("economy",), CIV, "Start resources"),
    Modifier(pct(0.25), Stat.HP, ("hoplite", "phalangite", "centurion"), ("academy",), CIV, "Academy HP"),
    Modifier(
        pct(0.25),
        Stat.HP,
        ("war_elephant", "armored_elephant", "elephant_archer"),
        ("elephant", "stable", "archery_range"),
        CIV,
        "Elephant HP",
    ),
    Modifier(pct(0.15), Stat.HP, ("camel_rider",), ("camel", "stable"), CIV, "Camel HP"),
    Modifier(pct(0.25), Stat.ATTACK, ("fire_galley",), ("ship", "dock"), CIV, "Fire Galley attack"),
    Modifier(
        pct(0.25),
        Stat.SPEED,
        ("light_transport", "heavy_transport"),
        ("ship", "dock", "transport"),
        CIV,
        "Transport speed",
    ),
    Modifier(pct(-1), Stat.TECH_COST, ("nobility",), ("government_center", "economy"), CIV, "Free Nobility"),
    Modifier(pct(0.2), Stat.WORK_RATE, ("academy",), ("academy",), CIV, "Academies work faster", kind="team"),
)
