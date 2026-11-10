"""Shang: "Economic and Cavalry civilization" (RoR string 120159).

• Villagers cost 40 Food
• Start the game with -40 Food
• Walls +60% hit points
• Cavalry-line attacks 10% faster
Team Bonus:
Town centers provide +4 population room
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(-10),
        stat=Stat.FOOD_COST,
        groups=(Group.VILLAGERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT),
        civ=Civ.SHANG,
        name="Shang 1",
        icon=Icon.VILLAGER,
    ),
    Modifier(
        change=flat(-40),
        stat=Stat.STARTING_FOOD,
        tags=(Tag.ECONOMY, Tag.FOOD, Tag.DRAWBACK),
        civ=Civ.SHANG,
        name="Shang 2",
        icon=Icon.FOOD,
    ),
    Modifier(
        change=pct(0.6),
        stat=Stat.HP,
        groups=(Group.WALLS,),
        tags=(Tag.WALL, Tag.DEFENCE, Tag.BUILDING),
        civ=Civ.SHANG,
        name="Shang 3",
        icon=Icon.WALL,
    ),
    Modifier(
        change=pct(0.1),
        stat=Stat.ATTACK_SPEED,
        targets=("cavalry", "heavy_cavalry", "cataphract"),
        tags=(Tag.CAVALRY, Tag.STABLE, Tag.UNIT),
        civ=Civ.SHANG,
        name="Shang 4",
        icon=Icon.CAVALRY,
    ),
    Modifier(
        change=flat(4),
        stat=Stat.POPULATION,
        targets=("town_center",),
        tags=(Tag.TOWN_CENTER, Tag.ECONOMY, Tag.BUILDING, Tag.TEAM),
        civ=Civ.SHANG,
        name="Shang 5",
        icon=Icon.TOWN_CENTER,
    ),
)
