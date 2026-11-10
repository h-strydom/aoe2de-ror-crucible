"""Test: the shop, with 3 boon slots and 4 choices a wave. A "wave is defeated" at 5 s, and again 15 s after the
shop closes."""

from crucible.shop import pool, scenario
from crucible.shop.config import ShopConfig

NAME = "shop"
CONFIG = ShopConfig(slots=3, choices=4)
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
        xsChatData("Wave %d defeated", crucibleCheckWave);
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
        f"SHOP on the Wonder, {len(BOONS)} boons in {categories}. Each wave (at 5 s, then 15 s after the shop "
        f"closes) gives {CONFIG.choices} choices. A choice shows two categories on row 3 (buttons 11 and 12), named "
        "with how many boons they have left; the hover text says how many choices are left. Click one: the other "
        "goes. When it finishes, each of the 3 slots on row 1 gets one of that category's boons, stacking on any "
        "already there, and the next choice shows on the same buttons. A boon never comes up twice. Chat narrates."
    )
