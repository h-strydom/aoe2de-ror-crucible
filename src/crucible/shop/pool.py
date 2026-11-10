"""Which boons a run's shop can offer, and the categories the choices can be."""

from crucible.bonuses import catalogue
from crucible.bonuses.model import Category, Modifier, Tag
from crucible.shop.config import ShopConfig


def boons(config: ShopConfig) -> list[Modifier]:
    """The boons of the civs in the config (its civ packs), drawbacks left out."""
    return [
        m
        for m in catalogue.query(exclude=[Tag.DRAWBACK])
        if m.civ in config.civs and any(m.in_category(c) for c in config.categories)
    ]


def categories(config: ShopConfig, pool: list[Modifier]) -> list[Category]:
    """The config's categories that have any boon in the pool."""
    return [c for c in config.categories if any(m.in_category(c) for m in pool)]
