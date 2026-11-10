"""Hittites: "Archer and Siege civilization" (RoR string 120155).

• All archers +1 attack
• Stone Thrower, Catapult, and Heavy Catapult +50% hit points
• War ships (except Fire Galley) +1/+2/+3 range in Tool/Bronze/Iron Age
• Wheel -50% cost and research time
Team Bonus:
Towers provide +4 population room
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(1),
        stat=Stat.ATTACK,
        groups=(Group.ARCHERS,),
        tags=(Tag.ARCHER, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.HITTITES,
        name="Hittites 1",
        icon=Icon.ARCHER,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(0.5),
        stat=Stat.HP,
        targets=("stone_thrower", "catapult", "heavy_catapult"),
        tags=(Tag.SIEGE, Tag.SIEGE_WORKSHOP, Tag.UNIT),
        civ=Civ.HITTITES,
        name="Hittites 2",
        icon=Icon.SIEGE,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=flat(3),
        stat=Stat.RANGE,
        targets=("scout_ship", "war_galley", "trireme", "catapult_trireme", "juggernaut"),
        tags=(Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.HITTITES,
        name="Hittites 3",
        icon=Icon.SHIP,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(-0.5),
        stat=Stat.COST,
        techs=("wheel",),
        tags=(Tag.MARKET, Tag.TECHNOLOGY),
        civ=Civ.HITTITES,
        name="Hittites 4",
        icon=Icon.MARKET,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(-0.5),
        stat=Stat.RESEARCH_TIME,
        techs=("wheel",),
        tags=(Tag.MARKET, Tag.TECHNOLOGY),
        civ=Civ.HITTITES,
        name="Hittites 5",
        icon=Icon.MARKET,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=flat(4),
        stat=Stat.POPULATION,
        groups=(Group.TOWERS,),
        tags=(Tag.TOWER, Tag.DEFENCE, Tag.BUILDING, Tag.TEAM),
        civ=Civ.HITTITES,
        name="Hittites 6",
        icon=Icon.TOWER,
        rarity=Rarity.RARE,
    ),
)
