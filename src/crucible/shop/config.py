"""What a run's shop offers and how: the values the meta upgrades change."""

from pydantic import BaseModel, ConfigDict, Field

from crucible.bonuses.model import Category, Civ, Rarity, Tag

CATEGORIES: tuple[Category, ...] = (  # what the two choices after a wave can be
    Tag.ACADEMY,
    Tag.ARCHERY_RANGE,
    Tag.BARRACKS,
    Tag.DOCK,
    Tag.SIEGE_WORKSHOP,
    Tag.STABLE,
    Tag.TEMPLE,
    Tag.BUILDING,
    Tag.ECONOMY,
    Tag.VILLAGER,
)


class ShopConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slots: int = Field(default=1, ge=1, le=5)  # boons offered at once on the Wonder's row 1
    rarity_points: dict[Rarity, int] = {Rarity.COMMON: 6, Rarity.RARE: 3, Rarity.LEGENDARY: 1}  # offer odds
    categories: tuple[Category, ...] = CATEGORIES
    civs: tuple[Civ, ...] = tuple(Civ)  # civ packs: whose boons are in the pool
