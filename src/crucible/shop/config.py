"""What a run's shop offers and how: the values the meta upgrades change."""

from pydantic import BaseModel, ConfigDict, Field

from crucible.bonuses.model import Civ
from crucible.boons.model import TIER_UPS


class ShopConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slots: int = Field(default=1, ge=1, le=5)  # boons offered at once on the Wonder's row 1
    choices: int = Field(default=1, ge=1)  # category choices granted per wave defeated
    tier_ups: tuple[tuple[int, int], ...] = TIER_UPS  # (tiers up, chance in percent): a better tier, same price
    civs: tuple[Civ, ...] = tuple(Civ)  # civ packs: whose boons are in the pool
