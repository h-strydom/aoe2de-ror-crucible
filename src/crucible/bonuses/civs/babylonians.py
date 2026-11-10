"""Babylonians: "Defensive civilization" (RoR string 120152).

• Stone Miners work 20% faster and carry +2 stone
• Market technologies cost -30%
• Walls and towers +60% hit points
• Priests rejuvenate 30% faster
• Chariots +1P Armor
Team Bonus:
Builders work 10% faster
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=pct(0.2),
        stat=Stat.WORK_RATE,
        groups=(Group.STONE_MINERS,),
        tags=(Tag.ECONOMY, Tag.STONE, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.BABYLONIANS,
        name="Babylonians 1",
        icon=Icon.STONE,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.CARRY,
        groups=(Group.STONE_MINERS,),
        tags=(Tag.ECONOMY, Tag.STONE, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.BABYLONIANS,
        name="Babylonians 2",
        icon=Icon.STONE,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(-0.3),
        stat=Stat.COST,
        techs=(
            "wheel",
            "coinage",
            "plow",
            "artisanship",
            "irrigation",
            "domestication",
            "woodworking",
            "gold_mining",
            "stone_mining",
            "craftmanship",
            "siegecraft",
        ),
        tags=(Tag.MARKET, Tag.ECONOMY, Tag.TECHNOLOGY),
        civ=Civ.BABYLONIANS,
        name="Babylonians 3",
        subject="Market technologies",
        icon=Icon.MARKET,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(0.6),
        stat=Stat.HP,
        groups=(Group.WALLS, Group.TOWERS),
        tags=(Tag.DEFENCE, Tag.WALL, Tag.TOWER, Tag.BUILDING),
        civ=Civ.BABYLONIANS,
        name="Babylonians 4",
        icon=Icon.TOWER,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(0.3),
        stat=Stat.REJUVENATION,
        targets=("priest",),
        tags=(Tag.PRIEST, Tag.TEMPLE, Tag.UNIT),
        civ=Civ.BABYLONIANS,
        name="Babylonians 5",
        icon=Icon.PRIEST,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=flat(1),
        stat=Stat.PIERCE_ARMOUR,
        targets=("chariot", "chariot_archer", "scythe_chariot"),
        tags=(Tag.CHARIOT, Tag.STABLE, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.BABYLONIANS,
        name="Babylonians 6",
        icon=Icon.CHARIOT,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(0.1),
        stat=Stat.WORK_RATE,
        groups=(Group.BUILDERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT, Tag.TEAM),
        civ=Civ.BABYLONIANS,
        name="Babylonians 7",
        icon=Icon.VILLAGER,
        rarity=Rarity.COMMON,
    ),
)
