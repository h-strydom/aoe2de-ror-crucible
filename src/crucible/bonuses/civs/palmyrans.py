"""Palmyrans: "Camel and Trading civilization" (RoR string 120164).

• Villagers cost 75 Food, but have +1/+1P armor and work 25% faster
• Start the game with +75 Food
• Camel Riders move 25% faster
• Tributes are not taxed
• Trade units return +20% gold
Team Bonus:
Technologies researched 30% faster
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(25),
        stat=Stat.FOOD_COST,
        groups=(Group.VILLAGERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT, Tag.DRAWBACK),
        civ=Civ.PALMYRANS,
        name="Palmyrans 1",
        icon=Icon.VILLAGER,
    ),
    Modifier(
        change=flat(1),
        stat=Stat.MELEE_ARMOUR,
        groups=(Group.VILLAGERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT),
        civ=Civ.PALMYRANS,
        name="Palmyrans 2",
        icon=Icon.VILLAGER,
    ),
    Modifier(
        change=flat(1),
        stat=Stat.PIERCE_ARMOUR,
        groups=(Group.VILLAGERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT),
        civ=Civ.PALMYRANS,
        name="Palmyrans 3",
        icon=Icon.VILLAGER,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.WORK_RATE,
        groups=(Group.VILLAGERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT),
        civ=Civ.PALMYRANS,
        name="Palmyrans 4",
        icon=Icon.VILLAGER,
    ),
    Modifier(
        change=flat(75),
        stat=Stat.STARTING_FOOD,
        tags=(Tag.ECONOMY, Tag.FOOD),
        civ=Civ.PALMYRANS,
        name="Palmyrans 5",
        icon=Icon.FOOD,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.SPEED,
        targets=("camel_rider",),
        tags=(Tag.CAMEL, Tag.CAVALRY, Tag.STABLE, Tag.UNIT),
        civ=Civ.PALMYRANS,
        name="Palmyrans 6",
        icon=Icon.CAMEL,
    ),
    Modifier(
        change=pct(-1),
        stat=Stat.TRIBUTE_TAX,
        tags=(Tag.ECONOMY, Tag.TRADE),
        civ=Civ.PALMYRANS,
        name="Palmyrans 7",
        icon=Icon.TRADE,
    ),
    Modifier(
        change=pct(0.2),
        stat=Stat.TRADE_GOLD,
        targets=("trade_boat", "merchant_ship"),
        tags=(Tag.TRADE, Tag.ECONOMY, Tag.GOLD, Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.PALMYRANS,
        name="Palmyrans 8",
        icon=Icon.TRADE,
    ),
    Modifier(
        change=pct(0.3),
        stat=Stat.RESEARCH_SPEED,
        tags=(Tag.TECHNOLOGY, Tag.TEAM),
        civ=Civ.PALMYRANS,
        name="Palmyrans 9",
        icon=Icon.TECHNOLOGY,
    ),
)
