"""Choson: "Infantry and Tower civilization" (RoR string 120161).

• Axeman, Short/Broad/Long Swordsmen and Legion +5/+15/+20/+60/+80 hit points (here: Axemen +5, the Swordsman line +30)
• Storage Pit technologies cost -40%
• Towers +2 range
• Priests cost -30%
Team Bonus:
Buildings +2 line of sight
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(5),
        stat=Stat.HP,
        targets=("axeman",),
        tags=(Tag.INFANTRY, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 1",
        icon=Icon.INFANTRY,
        rarity=Rarity.COMMON,
    ),
    Modifier(  # one boon for the whole line (RoR gives each unit its own amount: +15/+20/+60/+80)
        change=flat(30),
        stat=Stat.HP,
        targets=("short_swordsman", "broad_swordsman", "long_swordsman", "legionary"),
        tags=(Tag.INFANTRY, Tag.SWORDSMAN, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 2",
        icon=Icon.INFANTRY,
        rarity=Rarity.RARE,
        subject="Swordsman line",
    ),
    Modifier(
        change=pct(-0.4),
        stat=Stat.COST,
        techs=(
            "leather_armor_for_infantry",
            "leather_armor_archers",
            "leather_armor_for_cavalry",
            "scale_armor_for_infantry",
            "scale_armor_archers",
            "scale_armor_cavalry",
            "toolworking",
            "bronze_shield",
            "chain_mail_for_infantry",
            "chain_mail_archers",
            "chain_mail_cavalry",
            "metalworking",
            "metallurgy",
            "iron_shield",
            "tower_shield",
        ),
        tags=(Tag.STORAGE_PIT, Tag.TECHNOLOGY),
        civ=Civ.CHOSON,
        name="Choson 3",
        subject="Storage Pit technologies",
        icon=Icon.STORAGE_PIT,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.RANGE,
        groups=(Group.TOWERS,),
        tags=(Tag.TOWER, Tag.DEFENCE, Tag.BUILDING),
        civ=Civ.CHOSON,
        name="Choson 4",
        icon=Icon.TOWER,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=pct(-0.3),
        stat=Stat.COST,
        targets=("priest",),
        tags=(Tag.PRIEST, Tag.TEMPLE, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 5",
        icon=Icon.PRIEST,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.LINE_OF_SIGHT,
        groups=(Group.BUILDINGS,),
        tags=(Tag.BUILDING, Tag.TEAM),
        civ=Civ.CHOSON,
        name="Choson 6",
        icon=Icon.BUILDING,
        rarity=Rarity.COMMON,
    ),
)
