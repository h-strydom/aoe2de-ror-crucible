"""Carthaginians: "Elephant, Camel, and Naval civilization" (RoR string 120163).

• Start the game with +50 of all resources
• Academy units and elephant units +25% hit points, Camel Riders +15% hit points
• Fire Galley +25% attack
• Transport ships move 25% faster
• Nobility free (requires Government Center)
Team Bonus: Academies work 20% faster
"""

from crucible.bonuses.model import Civ, Kind, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(50),
        stat=Stat.START_RESOURCES,
        targets=(),
        tags=(Tag.ECONOMY,),
        civ=Civ.CARTHAGINIANS,
        name="Start resources",
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.HP,
        targets=("hoplite", "phalangite", "centurion"),
        tags=(Tag.ACADEMY, Tag.INFANTRY),
        civ=Civ.CARTHAGINIANS,
        name="Academy HP",
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.HP,
        targets=("war_elephant", "armored_elephant", "elephant_archer"),
        tags=(Tag.ELEPHANT, Tag.STABLE, Tag.ARCHERY_RANGE),
        civ=Civ.CARTHAGINIANS,
        name="Elephant HP",
    ),
    Modifier(
        change=pct(0.15),
        stat=Stat.HP,
        targets=("camel_rider",),
        tags=(Tag.CAMEL, Tag.CAVALRY, Tag.STABLE),
        civ=Civ.CARTHAGINIANS,
        name="Camel HP",
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.ATTACK,
        targets=("fire_galley",),
        tags=(Tag.SHIP, Tag.DOCK),
        civ=Civ.CARTHAGINIANS,
        name="Fire Galley attack",
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.SPEED,
        targets=("light_transport", "heavy_transport"),
        tags=(Tag.SHIP, Tag.TRANSPORT, Tag.DOCK),
        civ=Civ.CARTHAGINIANS,
        name="Transport speed",
    ),
    Modifier(
        change=pct(-1),
        stat=Stat.TECH_COST,
        targets=("nobility",),
        tags=(Tag.GOVERNMENT_CENTER, Tag.ECONOMY),
        civ=Civ.CARTHAGINIANS,
        name="Free Nobility",
    ),
    Modifier(
        change=pct(0.2),
        stat=Stat.WORK_RATE,
        targets=("academy",),
        tags=(Tag.ACADEMY,),
        civ=Civ.CARTHAGINIANS,
        name="Academies work faster",
        kind=Kind.TEAM,
    ),
)
