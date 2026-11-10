"""Carthaginians: "Elephant, Camel, and Naval civilization" (RoR string 120163).

• Start the game with +50 of all resources
• Academy units and elephant units +25% hit points, Camel Riders +15% hit points
• Fire Galley +25% attack
• Transport ships move 25% faster
• Nobility free (requires Government Center)
Team Bonus:
Academies work 20% faster
"""

from crucible.bonuses.model import Civ, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(50),
        stat=Stat.ALL_RESOURCES,
        tags=(Tag.ECONOMY,),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 1",
        icon=Icon.FARM,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.HP,
        targets=("hoplite", "phalangite", "centurion"),
        tags=(Tag.ACADEMY, Tag.INFANTRY, Tag.HOPLITE, Tag.UNIT),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 2",
        icon=Icon.ACADEMY,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.HP,
        targets=("war_elephant", "armored_elephant", "elephant_archer"),
        tags=(Tag.ELEPHANT, Tag.STABLE, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 3",
        icon=Icon.ELEPHANT,
    ),
    Modifier(
        change=pct(0.15),
        stat=Stat.HP,
        targets=("camel_rider",),
        tags=(Tag.CAMEL, Tag.CAVALRY, Tag.STABLE, Tag.UNIT),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 4",
        icon=Icon.CAMEL,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.ATTACK,
        targets=("fire_galley",),
        tags=(Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 5",
        icon=Icon.SHIP,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.SPEED,
        targets=("light_transport", "heavy_transport"),
        tags=(Tag.SHIP, Tag.TRANSPORT, Tag.DOCK, Tag.UNIT),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 6",
        icon=Icon.TRANSPORT,
    ),
    Modifier(
        change=pct(-1),
        stat=Stat.COST,
        techs=("nobility",),
        tags=(Tag.GOVERNMENT_CENTER, Tag.ECONOMY, Tag.TECHNOLOGY),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 7",
        icon=Icon.GOVERNMENT_CENTER,
    ),
    Modifier(
        change=pct(0.2),
        stat=Stat.WORK_RATE,
        targets=("academy",),
        tags=(Tag.ACADEMY, Tag.BUILDING, Tag.TEAM),
        civ=Civ.CARTHAGINIANS,
        name="Carthaginians 8",
        icon=Icon.ACADEMY,
    ),
)
