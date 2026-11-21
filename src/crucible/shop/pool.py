"""Which boons a run's shop can offer (crucible.boons), and the categories the choices can be: every tag of every axis
that has a boon in the pool."""

from crucible.boons import catalogue
from crucible.boons.model import AXES, Boon, Category, Flag
from crucible.datamod.boons import key
from crucible.shop.config import ShopConfig


def boons(config: ShopConfig, techs: dict[str, int]) -> list[Boon]:
    """The boons of the civs in the config (its civ packs) with a tier in the data mod, drawbacks left out."""
    return [
        b
        for b in catalogue.ALL
        if b.civ in config.civs
        and not b.in_category(Flag.DRAWBACK)
        and any(key(b, tier) in techs for tier in b.tiers)
    ]


def categories(pool: list[Boon]) -> list[Category]:
    """Every tag with a boon in the pool, axis by axis (Drawback isn't one)."""
    return [c for axis in AXES for c in axis if c is not Flag.DRAWBACK and any(b.in_category(c) for b in pool)]
