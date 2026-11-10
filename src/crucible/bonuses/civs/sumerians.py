"""Sumerians: "Economic and Siege civilization" (RoR string 120157).

• Villagers +15 hit points
• Stone Thrower, Catapult, Heavy Catapult fire 45% faster
• Farms +125 Food
• Camels +1P Armor
Team Bonus:
Town Centers cost -25%
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(15),
        stat=Stat.HP,
        groups=(Group.VILLAGERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT),
        civ=Civ.SUMERIANS,
        name="Sumerians 1",
        icon=Icon.VILLAGER,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=pct(0.45),
        stat=Stat.ATTACK_SPEED,
        targets=("stone_thrower", "catapult", "heavy_catapult"),
        tags=(Tag.SIEGE, Tag.SIEGE_WORKSHOP, Tag.UNIT),
        civ=Civ.SUMERIANS,
        name="Sumerians 2",
        icon=Icon.SIEGE,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=flat(125),
        stat=Stat.FOOD,
        targets=("farm",),
        tags=(Tag.FOOD, Tag.ECONOMY, Tag.BUILDING),
        civ=Civ.SUMERIANS,
        name="Sumerians 3",
        icon=Icon.FARM,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=flat(1),
        stat=Stat.PIERCE_ARMOUR,
        targets=("camel_rider",),
        tags=(Tag.CAMEL, Tag.CAVALRY, Tag.STABLE, Tag.UNIT),
        civ=Civ.SUMERIANS,
        name="Sumerians 4",
        icon=Icon.CAMEL,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(-0.25),
        stat=Stat.COST,
        targets=("town_center",),
        tags=(Tag.TOWN_CENTER, Tag.ECONOMY, Tag.BUILDING, Tag.TEAM),
        civ=Civ.SUMERIANS,
        name="Sumerians 5",
        icon=Icon.TOWN_CENTER,
        rarity=Rarity.COMMON,
    ),
)
