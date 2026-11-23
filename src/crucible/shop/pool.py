"""Which boons a run's shop can offer (crucible.boons), and the categories the choices can be: the offer axes' tags
with enough boons in the pool (catalogue.choices)."""

from crucible.boons import catalogue
from crucible.boons.model import Boon, Category, Flag
from crucible.datamod.boons import key
from crucible.shop.config import ShopConfig


def boons(config: ShopConfig, techs: dict[str, int]) -> list[Boon]:
    """The boons of the civs in the config (its civ packs) with a level in the data mod, drawbacks left out."""
    return [
        b
        for b in catalogue.ALL
        if b.civ in config.civs
        and not b.in_category(Flag.DRAWBACK)
        and any(key(b, level) in techs for level in b.steps)
    ]


def categories(pool: list[Boon]) -> list[Category]:
    """The tags a choice can be (catalogue.choices): civs, civ types and flags never are."""
    return catalogue.choices(pool)
