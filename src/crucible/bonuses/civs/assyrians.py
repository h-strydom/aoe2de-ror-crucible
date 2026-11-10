"""Assyrians: "Archer and Siege civilization" (RoR string 120153).

• Villagers move 10% faster
• Archers fire 11/22/33% faster in Tool/Bronze/Iron Age
• Siege unit upgrades cost -50%
Team Bonus:
Siege Workshops work 20% faster
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, pct

MODIFIERS = (
    Modifier(
        change=pct(0.1),
        stat=Stat.SPEED,
        groups=(Group.VILLAGERS,),
        tags=(Tag.VILLAGER, Tag.ECONOMY, Tag.UNIT),
        civ=Civ.ASSYRIANS,
        name="Assyrians 1",
        icon=Icon.VILLAGER,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=pct(0.33),
        stat=Stat.ATTACK_SPEED,
        groups=(Group.ARCHERS,),
        tags=(Tag.ARCHER, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.ASSYRIANS,
        name="Assyrians 2",
        icon=Icon.ARCHER,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(-0.5),
        stat=Stat.COST,
        techs=("catapult", "heavy_catapult", "helepolis", "balista"),
        tags=(Tag.SIEGE, Tag.SIEGE_WORKSHOP, Tag.TECHNOLOGY),
        civ=Civ.ASSYRIANS,
        name="Assyrians 3",
        subject="Siege Workshop upgrades",
        icon=Icon.SIEGE,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(0.2),
        stat=Stat.WORK_RATE,
        targets=("siege_workshop",),
        tags=(Tag.SIEGE_WORKSHOP, Tag.SIEGE, Tag.BUILDING, Tag.TEAM),
        civ=Civ.ASSYRIANS,
        name="Assyrians 4",
        icon=Icon.SIEGE_WORKSHOP,
        rarity=Rarity.COMMON,
    ),
)
