"""Greeks: "Infantry and Naval civilization" (RoR string 120151).

• Town Centers work 10% faster starting from Tool Age
• Academy units move 30% faster and cost -20%
• Ships move 20% faster
• Polytheism and Astrology free (requires Temple)
Team Bonus:
Markets cost -50%
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, pct

MODIFIERS = (
    Modifier(
        change=pct(0.1),
        stat=Stat.WORK_RATE,
        targets=("town_center",),
        tags=(Tag.TOWN_CENTER, Tag.ECONOMY, Tag.BUILDING),
        civ=Civ.GREEKS,
        name="Greeks 1",
        icon=Icon.TOWN_CENTER,
    ),
    Modifier(
        change=pct(0.3),
        stat=Stat.SPEED,
        targets=("hoplite", "phalangite", "centurion"),
        tags=(Tag.ACADEMY, Tag.INFANTRY, Tag.HOPLITE, Tag.UNIT),
        civ=Civ.GREEKS,
        name="Greeks 2",
        icon=Icon.ACADEMY,
    ),
    Modifier(
        change=pct(-0.2),
        stat=Stat.COST,
        targets=("hoplite", "phalangite", "centurion"),
        tags=(Tag.ACADEMY, Tag.INFANTRY, Tag.HOPLITE, Tag.UNIT),
        civ=Civ.GREEKS,
        name="Greeks 3",
        icon=Icon.ACADEMY,
    ),
    Modifier(
        change=pct(0.2),
        stat=Stat.SPEED,
        groups=(Group.SHIPS,),
        tags=(Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.GREEKS,
        name="Greeks 4",
        icon=Icon.SHIP,
    ),
    Modifier(
        change=pct(-1),
        stat=Stat.COST,
        techs=("polytheism", "astrology"),
        tags=(Tag.TEMPLE, Tag.PRIEST, Tag.TECHNOLOGY),
        civ=Civ.GREEKS,
        name="Greeks 5",
        icon=Icon.TEMPLE,
    ),
    Modifier(
        change=pct(-0.5),
        stat=Stat.COST,
        targets=("market",),
        tags=(Tag.MARKET, Tag.ECONOMY, Tag.BUILDING, Tag.TEAM),
        civ=Civ.GREEKS,
        name="Greeks 6",
        icon=Icon.MARKET,
    ),
)
