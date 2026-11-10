"""The XS data block the shop runtime (shop.xs) reads: constants, and crucibleShopData() filling the arrays."""

from crucible.bonuses.model import Category, Modifier, Rarity
from crucible.datamod.shop import BOON_BUTTONS, choice_key
from crucible.datamod.upgrades import WONDER
from crucible.shop.config import ShopConfig

RARITIES = tuple(Rarity)  # a boon's rarity in XS is its index here


def label(category: Category) -> str:
    """How a choice names its category: "Archery Range"."""
    return str(category).title()


def xs_data(
    config: ShopConfig,
    techs: dict[str, int],
    pool: list[Modifier],
    categories: list[Category],
    choices_variable: int,
) -> str:
    """`techs` is the data mod's manifest; `choices_variable` is the trigger variable that re-enables the choices."""
    sets = [
        *(f"    xsArraySetInt(crucibleBoonTech, {b}, {techs[m.id]});" for b, m in enumerate(pool)),
        *(f"    xsArraySetInt(crucibleBoonRarity, {b}, {RARITIES.index(m.rarity)});" for b, m in enumerate(pool)),
        *(
            f"    xsArraySetInt(crucibleBoonMember, {c * len(pool) + b}, 1);"
            for c, category in enumerate(categories)
            for b, m in enumerate(pool)
            if m.in_category(category)
        ),
        *(f'    xsArraySetString(crucibleCategoryName, {c}, "{label(cat)}");' for c, cat in enumerate(categories)),
        *(
            f"    xsArraySetInt(crucibleRarityPoints, {r}, {config.rarity_points.get(rarity, 0)});"
            for r, rarity in enumerate(RARITIES)
        ),
    ]
    lines = "\n".join(sets)

    return f"""// ---- Crucible shop: data (generated) ----
const int cCrucibleBoons = {len(pool)};
const int cCrucibleCategories = {len(categories)};
const int cCrucibleRarities = {len(RARITIES)};
const int cCrucibleSlots = {min(config.slots, len(BOON_BUTTONS))};
const int cCrucibleWonder = {WONDER};
const int cCrucibleChoice1 = {techs[choice_key(1)]};
const int cCrucibleChoice2 = {techs[choice_key(2)]};
const int cCrucibleChoicesVariable = {choices_variable};

int crucibleBoonTech = -1;
int crucibleBoonRarity = -1;
int crucibleBoonMember = -1;  // category * cCrucibleBoons + boon -> 1 if the boon is in the category
int crucibleBoonTaken = -1;  // 1 once offered
int crucibleCategoryName = -1;
int crucibleRarityPoints = -1;

void crucibleShopData() {{
    crucibleBoonTech = xsArrayCreateInt(cCrucibleBoons, -1, "crucibleBoonTech");
    crucibleBoonRarity = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonRarity");
    crucibleBoonMember = xsArrayCreateInt(cCrucibleCategories * cCrucibleBoons, 0, "crucibleBoonMember");
    crucibleBoonTaken = xsArrayCreateInt(cCrucibleBoons, 0, "crucibleBoonTaken");
    crucibleCategoryName = xsArrayCreateString(cCrucibleCategories, "", "crucibleCategoryName");
    crucibleRarityPoints = xsArrayCreateInt(cCrucibleRarities, 0, "crucibleRarityPoints");
{lines}
}}
"""
