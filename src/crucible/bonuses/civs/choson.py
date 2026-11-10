"""Choson: "Infantry and Tower civilization" (RoR string 120161).

• Axeman, Short/Broad/Long Swordsmen and Legion +5/+15/+20/+60/+80 hit points
• Storage Pit technologies cost -40%
• Towers +2 range
• Priests cost -30%
Team Bonus:
Buildings +2 line of sight
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(5),
        stat=Stat.HP,
        targets=("axeman",),
        tags=(Tag.INFANTRY, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 1",
        icon=Icon.INFANTRY,
    ),
    Modifier(
        change=flat(15),
        stat=Stat.HP,
        targets=("short_swordsman",),
        tags=(Tag.INFANTRY, Tag.SWORDSMAN, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 2",
        icon=Icon.INFANTRY,
    ),
    Modifier(
        change=flat(20),
        stat=Stat.HP,
        targets=("broad_swordsman",),
        tags=(Tag.INFANTRY, Tag.SWORDSMAN, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 3",
        icon=Icon.INFANTRY,
    ),
    Modifier(
        change=flat(60),
        stat=Stat.HP,
        targets=("long_swordsman",),
        tags=(Tag.INFANTRY, Tag.SWORDSMAN, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 4",
        icon=Icon.INFANTRY,
    ),
    Modifier(
        change=flat(80),
        stat=Stat.HP,
        targets=("legionary",),
        tags=(Tag.INFANTRY, Tag.SWORDSMAN, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 5",
        icon=Icon.INFANTRY,
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
        name="Choson 6",
        subject="Storage Pit technologies",
        icon=Icon.STORAGE_PIT,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.RANGE,
        groups=(Group.TOWERS,),
        tags=(Tag.TOWER, Tag.DEFENCE, Tag.BUILDING),
        civ=Civ.CHOSON,
        name="Choson 7",
        icon=Icon.TOWER,
    ),
    Modifier(
        change=pct(-0.3),
        stat=Stat.COST,
        targets=("priest",),
        tags=(Tag.PRIEST, Tag.TEMPLE, Tag.UNIT),
        civ=Civ.CHOSON,
        name="Choson 8",
        icon=Icon.PRIEST,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.LINE_OF_SIGHT,
        groups=(Group.BUILDINGS,),
        tags=(Tag.BUILDING, Tag.TEAM),
        civ=Civ.CHOSON,
        name="Choson 9",
        icon=Icon.BUILDING,
    ),
)
