"""Test: the shop, with 3 boon slots. A "wave is defeated" at 5 s and again 15 s after each offer."""

from crucible.shop import pool, scenario
from crucible.shop.config import ShopConfig

NAME = "shop"
CONFIG = ShopConfig(slots=3)
BOONS = tuple(m.id for m in pool.boons(CONFIG))
BUTTONS: dict[str, int] = {}

WAVES = """// ---- crucible check: shop waves ----
int crucibleCheckNext = 5;
int crucibleCheckWave = 0;
bool crucibleCheckOpen = false;

rule crucibleCheckWaves
    active
    minInterval 1
{
    if (crucibleCheckOpen && (crucibleShopState == 0)) {
        crucibleCheckOpen = false;
        crucibleCheckNext = xsGetTime() + 15;
    }

    if ((crucibleCheckOpen == false) && (xsGetTime() >= crucibleCheckNext)) {
        crucibleCheckWave = crucibleCheckWave + 1;
        xsChatData("Wave %d defeated: choose a category", crucibleCheckWave);
        crucibleShopOpen();
        crucibleCheckOpen = true;
    }
}
"""


def setup(s, ctx, techs: dict[str, int], top: int) -> str:
    scenario.add(ctx, CONFIG, techs)
    ctx.xs(WAVES)
    categories = ", ".join(str(c).title() for c in pool.categories(CONFIG, pool.boons(CONFIG)))

    return (
        f"SHOP on the Wonder, {len(BOONS)} boons in {categories}. At 5 s, and 15 s after each offer, two categories "
        "appear on row 3 (buttons 11 and 12) named with how many boons they have left. Click one: the other goes. "
        "When it finishes, each of the 3 slots on row 1 gets one of that category's boons, priced by rarity, stacking "
        "on any boon already there: research the one on top and the next should show. Leave some unresearched: all "
        f"{len(BOONS)} should end up stacked on the 3 slots. A boon never comes up twice. Chat narrates."
    )
