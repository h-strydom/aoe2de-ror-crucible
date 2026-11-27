"""The XS data block the shop runtime (shop.xs) reads: constants, and crucibleShopData() filling the arrays."""

from crucible import meta
from crucible.bonuses.model import Civ
from crucible.boons.model import AXES, LEVELS, RARITY_COSTS, Boon, Category, Rarity
from crucible.datamod.boons import key
from crucible.datamod.shop import BOON_BUTTONS, MAX_OFFERED, REROLL_FREE, REROLL_PAID, SPIES, choice_key
from crucible.datamod.upgrades import RESEARCH_TIME as BOON_TIME
from crucible.datamod.upgrades import WONDER
from crucible.shop.config import ShopConfig

CATEGORY_WEIGHT = 10  # every category's weight at the start
CATEGORY_BOOST = 10  # added to a category's weight each time the player picks it (playtest 2026-11-23)
CATEGORY_REROLL_PENALTY = 5  # taken off each category a reroll turns down (playtest 2026-11-24)
CATEGORY_MIN = 2  # no category weighs less


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
    rerolls_variable: int = -1,
    reroll_signal: int = -1,
) -> str:
    """`techs` is the data mod's manifest; `choices_variable` is the trigger variable that re-enables the choices.
    `slots_variable` (more boons per choice) and `speed_variable` (out of `speed_tiers`: shorter research, instant
    at the last) are the trigger variables of meta upgrades, read at each offer; -1 for none. `discount_variable`:
    the boon discount's level, `discounts` the percent off each level adds. `rerolls_variable`: the Rerolls
    upgrade's level (-1: no reroll button); `reroll_signal`: the trigger variable that shows a reroll."""
    rarities = list(Rarity)
    sets = [
        *(
            f"    xsArraySetInt(crucibleBoonLevel, {b * LEVELS + level - 1}, {techs[key(boon, level)]});"
            for b, boon in enumerate(pool)
            for level in boon.steps
            if key(boon, level) in techs
        ),
        *(f"    xsArraySetInt(crucibleBoonRarity, {b}, {rarities.index(boon.rarity)});" for b, boon in enumerate(pool)),
        *(
            f"    xsArraySetInt(crucibleBoonMember, {c * len(pool) + b}, 1);"
            for c, category in enumerate(categories)
            for b, boon in enumerate(pool)
            if boon.in_category(category)
        ),
        *(f'    xsArraySetString(crucibleCategoryName, {c}, "{label(cat)}");' for c, cat in enumerate(categories)),
        *(f"    xsArraySetInt(crucibleCategoryAxis, {c}, {axis(cat)});" for c, cat in enumerate(categories)),
        *(
            f"    xsArraySetInt(crucibleRarityCost, {r * 4 + resource}, {amount});"
            for r, rarity in enumerate(rarities)
            for resource, amount in RARITY_COSTS[rarity].items()
        ),
        *(
            f"    xsArraySetInt(crucibleShopDiscount, {level + 1}, {sum(discounts[: level + 1])});"
            for level in range(len(discounts))
        ),
    ]
    lines = "\n".join(sets)

    return f"""// ---- Crucible shop: data (generated) ----
const int cCrucibleBoons = {len(pool)};
const int cCrucibleLevels = {LEVELS};
const int cCrucibleRarities = {len(rarities)};
const int cCrucibleCategories = {len(categories)};
const int cCrucibleCategoryWeight = {CATEGORY_WEIGHT};
const int cCrucibleCategoryBoost = {CATEGORY_BOOST};
const int cCrucibleCategoryRerollPenalty = {CATEGORY_REROLL_PENALTY};
const int cCrucibleCategoryMin = {CATEGORY_MIN};
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
const int cCrucibleRerollsVariable = {rerolls_variable};
const int cCrucibleRerollSignal = {reroll_signal};
const int cCrucibleRerollFree = {techs.get(REROLL_FREE, -1) if reroll_signal >= 0 else -1};
const int cCrucibleRerollPaid = {techs.get(REROLL_PAID, -1) if reroll_signal >= 0 else -1};
const int cCrucibleRerollGold = {meta.REROLL_GOLD};
const int cCrucibleSpies = {techs.get(SPIES, -1)};

int crucibleBoonLevel = -1;  // boon * cCrucibleLevels + level (from 0) -> its tech, -1 if it has none
int crucibleBoonRarity = -1;  // 0 common, 1 rare, 2 legendary: its price
int crucibleBoonMember = -1;  // category * cCrucibleBoons + boon -> 1 if the boon is in the category
int crucibleBoonNext = -1;  // the level the shop offers it at next (from 0, one up a purchase)
int crucibleBoonPending = -1;  // 1 while on the Wonder, unbought
int crucibleCategoryName = -1;
int crucibleCategoryAxis = -1;  // choices come from different axes
int crucibleCategoryWeight = -1;  // its chance to be a choice: up each time the player picks it
int crucibleRarityCost = -1;  // rarity * 4 + resource (food, wood, stone, gold) -> a level's price
int crucibleShopDiscount = -1;  // the boon discount's level -> percent off

void crucibleShopData() {{
    crucibleBoonLevel = xsArrayCreateInt(cCrucibleBoons * cCrucibleLevels, -1, "crucibleBoonLevel");
    crucibleBoonRarity = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonRarity");
    crucibleBoonMember = xsArrayCreateInt(cCrucibleCategories * cCrucibleBoons, 0, "crucibleBoonMember");
    crucibleBoonNext = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonNext");
    crucibleBoonPending = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonPending");
    crucibleCategoryName = xsArrayCreateString(cCrucibleCategories, "", "crucibleCategoryName");
    crucibleCategoryAxis = xsArrayCreateInt(cCrucibleCategories, 0, "crucibleCategoryAxis");
    crucibleCategoryWeight = xsArrayCreateInt(cCrucibleCategories, cCrucibleCategoryWeight, "crucibleCategoryWeight");
    crucibleRarityCost = xsArrayCreateInt(cCrucibleRarities * 4, 0, "crucibleRarityCost");
    crucibleShopDiscount = xsArrayCreateInt({len(discounts) + 1}, 0, "crucibleShopDiscount");
{lines}
}}
"""
