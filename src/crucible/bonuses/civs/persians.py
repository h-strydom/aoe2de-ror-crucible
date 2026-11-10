"""Persians: "Elephant and Naval civilization" (RoR string 120158).

• Hunters work 30% faster and carry +3 food
• Elephant units move 25% faster
• Scout Ship line fires 18/25/33% faster in Tool/Bronze/Iron Age
• Walls cost -20%
Team Bonus:
Stables work 20% faster
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=pct(0.3),
        stat=Stat.WORK_RATE,
        groups=(Group.HUNTERS,),
        tags=(Tag.FOOD, Tag.ECONOMY, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.PERSIANS,
        name="Persians 1",
        icon=Icon.FOOD,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=flat(3),
        stat=Stat.CARRY,
        groups=(Group.HUNTERS,),
        tags=(Tag.FOOD, Tag.ECONOMY, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.PERSIANS,
        name="Persians 2",
        icon=Icon.FOOD,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.SPEED,
        targets=("war_elephant", "armored_elephant", "elephant_archer"),
        tags=(Tag.ELEPHANT, Tag.STABLE, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.PERSIANS,
        name="Persians 3",
        icon=Icon.ELEPHANT,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=pct(0.33),
        stat=Stat.ATTACK_SPEED,
        targets=("scout_ship", "war_galley", "trireme"),
        tags=(Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.PERSIANS,
        name="Persians 4",
        icon=Icon.SHIP,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(-0.2),
        stat=Stat.COST,
        groups=(Group.WALLS,),
        tags=(Tag.WALL, Tag.DEFENCE, Tag.BUILDING),
        civ=Civ.PERSIANS,
        name="Persians 5",
        icon=Icon.WALL,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=pct(0.2),
        stat=Stat.WORK_RATE,
        targets=("stable",),
        tags=(Tag.STABLE, Tag.CAVALRY, Tag.BUILDING, Tag.TEAM),
        civ=Civ.PERSIANS,
        name="Persians 6",
        icon=Icon.STABLE,
        rarity=Rarity.COMMON,
    ),
)
