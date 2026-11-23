"""Which boons a run's shop can offer (crucible.boons), and the categories the choices can be: every tag of every axis
that has a boon in the pool."""

from crucible.boons import catalogue
from crucible.boons.model import OFFER_AXES, Boon, Category, Flag
from crucible.datamod.boons import key
from crucible.shop.config import ShopConfig


def boons(config: ShopConfig, techs: dict[str, int]) -> list[Boon]:
    """The boons of the civs in the config (its civ packs) with a tier in the data mod, drawbacks left out."""
    return [
        b
        for b in catalogue.ALL
        if b.civ in config.civs
        and not b.in_category(Flag.DRAWBACK)
        and any(key(b, tier) in techs for tier in b.steps)
    ]


def categories(pool: list[Boon]) -> list[Category]:
    """Every tag of the offer axes with a boon in the pool (Drawback isn't one; nor are civs and civ types)."""
    return [c for axis in OFFER_AXES for c in axis if c is not Flag.DRAWBACK and any(b.in_category(c) for b in pool)]
