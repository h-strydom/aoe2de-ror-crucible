"""The XS data block the shop runtime (shop.xs) reads: constants, and crucibleShopData() filling the arrays."""

from crucible.bonuses.model import Civ
from crucible.boons.model import AXES, TIER_COSTS, Boon, Category, Tier
from crucible.datamod.boons import key
from crucible.datamod.shop import BOON_BUTTONS, MAX_OFFERED, choice_key
from crucible.datamod.upgrades import RESEARCH_TIME as BOON_TIME
from crucible.datamod.upgrades import WONDER
from crucible.shop.config import ShopConfig

CATEGORY_WEIGHT = 10  # every category's weight at the start
CATEGORY_BOOST = 10  # added to a category's weight each time the player picks it (playtest 2026-11-23)


def label(category: Category) -> str:
    """How a choice names its category: "Archery Range", "Lac Viet", "Defensive civ"."""
    return category.value.title() if isinstance(category, Civ) else str(category)


def axis(category: Category) -> int:
    return next(n for n, a in enumerate(AXES) if isinstance(category, a))


def xs_data(
    config: ShopConfig,
    techs: dict[str, int],
    pool: list[Boon],
    categories: list[Category],
    choices_variable: int,
    *,
    slots_variable: int = -1,
    speed_variable: int = -1,
    speed_tiers: int = 5,
    discount_variable: int = -1,
    discounts: tuple[int, ...] = (),
) -> str:
    """`techs` is the data mod's manifest; `choices_variable` is the trigger variable that re-enables the choices.
    `slots_variable` (more boons per decision) and `speed_variable` (out of `speed_tiers`: shorter research, instant
    at the last) are the trigger variables of meta upgrades, read at each offer; -1 for none. `discount_variable`:
    the boon discount's level, `discounts` the percent off each level adds."""
    tiers = len(Tier)
    sets = [
        *(
            f"    xsArraySetInt(crucibleBoonTier, {b * tiers + tier}, {techs[key(boon, tier)]});"
            for b, boon in enumerate(pool)
            for tier in boon.steps
            if key(boon, tier) in techs
        ),
        *(f"    xsArraySetInt(crucibleBoonLowest, {b}, {int(boon.lowest)});" for b, boon in enumerate(pool)),
        *(
            f"    xsArraySetInt(crucibleBoonMember, {c * len(pool) + b}, 1);"
            for c, category in enumerate(categories)
            for b, boon in enumerate(pool)
            if boon.in_category(category)
        ),
        *(f'    xsArraySetString(crucibleCategoryName, {c}, "{label(cat)}");' for c, cat in enumerate(categories)),
        *(f"    xsArraySetInt(crucibleCategoryAxis, {c}, {axis(cat)});" for c, cat in enumerate(categories)),
        *(f"    xsArraySetInt(crucibleBoonNext, {b}, {int(boon.lowest)});" for b, boon in enumerate(pool)),
        *(
            f"    xsArraySetInt(crucibleTierCost, {int(tier) * 4 + resource}, {amount});"
            for tier in Tier
            for resource, amount in TIER_COSTS[tier].items()
        ),
        *(
            f"    xsArraySetInt(crucibleShopDiscount, {level + 1}, {sum(discounts[: level + 1])});"
            for level in range(len(discounts))
        ),
    ]
    lines = "\n".join(sets)

    return f"""// ---- Crucible shop: data (generated) ----
const int cCrucibleBoons = {len(pool)};
const int cCrucibleTiers = {tiers};
const int cCrucibleCategories = {len(categories)};
const int cCrucibleCategoryWeight = {CATEGORY_WEIGHT};
const int cCrucibleCategoryBoost = {CATEGORY_BOOST};
const int cCrucibleDiscountVariable = {discount_variable};
const int cCrucibleSlots = {min(config.slots, MAX_OFFERED)};
const int cCrucibleChoices = {config.choices};
const int cCrucibleWonder = {WONDER};
const int cCrucibleChoice1 = {techs[choice_key(1)]};
const int cCrucibleChoice2 = {techs[choice_key(2)]};
const int cCrucibleChoicesVariable = {choices_variable};
const int cCrucibleMaxSlots = {MAX_OFFERED};
const int cCrucibleButtons = {len(BOON_BUTTONS)};
const int cCrucibleSlotsVariable = {slots_variable};
const int cCrucibleSpeedVariable = {speed_variable};
const int cCrucibleSpeedTiers = {speed_tiers};
const int cCrucibleBoonTime = {BOON_TIME};

int crucibleBoonTier = -1;  // boon * cCrucibleTiers + tier -> its tech, -1 if it has none
int crucibleBoonLowest = -1;
int crucibleBoonMember = -1;  // category * cCrucibleBoons + boon -> 1 if the boon is in the category
int crucibleBoonNext = -1;  // the next tier the shop offers it at (from its lowest, one up a purchase)
int crucibleBoonPending = -1;  // 1 while on the Wonder, unbought
int crucibleCategoryName = -1;
int crucibleCategoryAxis = -1;  // choices come from different axes
int crucibleCategoryWeight = -1;  // its chance to be a choice: up each time the player picks it
int crucibleTierCost = -1;  // tier * 4 + resource (food, wood, stone, gold) -> its price
int crucibleShopDiscount = -1;  // the boon discount's level -> percent off

void crucibleShopData() {{
    crucibleBoonTier = xsArrayCreateInt(cCrucibleBoons * cCrucibleTiers, -1, "crucibleBoonTier");
    crucibleBoonLowest = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonLowest");
    crucibleBoonMember = xsArrayCreateInt(cCrucibleCategories * cCrucibleBoons, 0, "crucibleBoonMember");
    crucibleBoonNext = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonNext");
    crucibleBoonPending = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonPending");
    crucibleCategoryName = xsArrayCreateString(cCrucibleCategories, "", "crucibleCategoryName");
    crucibleCategoryAxis = xsArrayCreateInt(cCrucibleCategories, 0, "crucibleCategoryAxis");
    crucibleCategoryWeight = xsArrayCreateInt(cCrucibleCategories, cCrucibleCategoryWeight, "crucibleCategoryWeight");
    crucibleTierCost = xsArrayCreateInt(cCrucibleTiers * 4, 0, "crucibleTierCost");
    crucibleShopDiscount = xsArrayCreateInt({len(discounts) + 1}, 0, "crucibleShopDiscount");
{lines}
}}
"""
