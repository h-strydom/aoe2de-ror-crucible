"""Yamato: "Cavalry and Naval civilization" (RoR string 120160).

• Fishing boats work 20% faster
• All cavalry units and Horse Archers cost -15%
• Ships +10/+15/+20/+25% HP in Stone/Tool/Bronze/Iron Age
• Stable and Archery Range upgrades cost -30%
Team Bonus:
Stables and Archery Ranges cost -33% wood
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, pct

MODIFIERS = (
    Modifier(
        change=pct(0.2),
        stat=Stat.WORK_RATE,
        targets=("fishing_boat", "fishing_ship"),
        tags=(Tag.FOOD, Tag.ECONOMY, Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.YAMATO,
        name="Yamato 1",
        icon=Icon.FISH,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(-0.15),
        stat=Stat.COST,
        targets=("horse_archer", "heavy_horse_archer"),
        groups=(Group.CAVALRY,),
        tags=(Tag.CAVALRY, Tag.STABLE, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.YAMATO,
        name="Yamato 2",
        icon=Icon.CAVALRY,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.HP,
        groups=(Group.SHIPS,),
        tags=(Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.YAMATO,
        name="Yamato 3",
        icon=Icon.SHIP,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(-0.3),
        stat=Stat.COST,
        techs=(
            "chariot",
            "cavalry",
            "war_elephant",
            "heavy_cavalry",
            "cataphract",
            "armored_elephant",
            "heavy_chariots",
            "advanced_horse_archer",
            "improved_bow",
            "composite_bow",
            "chariot_archer",
            "horse_archer",
            "elephant_archer",
        ),
        tags=(Tag.STABLE, Tag.ARCHERY_RANGE, Tag.TECHNOLOGY),
        civ=Civ.YAMATO,
        name="Yamato 4",
        subject="Stable and Archery Range upgrades",
        icon=Icon.STABLE,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(-0.33),
        stat=Stat.WOOD_COST,
        targets=("stable", "archery_range"),
        tags=(Tag.STABLE, Tag.ARCHERY_RANGE, Tag.BUILDING, Tag.TEAM),
        civ=Civ.YAMATO,
        name="Yamato 5",
        icon=Icon.STABLE,
        rarity=Rarity.COMMON,
    ),
)
