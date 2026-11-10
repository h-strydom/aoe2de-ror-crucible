"""Adding the shop to a scenario: the two triggers that re-enable the choices, then the XS (data block + runtime).

The scenario calls crucibleShopOpen() from its own XS when a wave is defeated.
"""

from pathlib import Path

from crucible.datamod.shop import choice_key
from crucible.shop import pool as shop_pool
from crucible.shop.config import ShopConfig
from crucible.shop.data import xs_data

RUNTIME = Path(__file__).with_name("shop.xs")
CHOICES_VARIABLE = "crucible_shop_choices"  # 1: re-enable choice 1, 2: re-enable both (XS sets it, triggers reset)


def _enable(tech: int) -> dict:
    return {"type": "enable_disable_technology", "source_player": 1, "technology": tech, "enabled": 1}


def _triggers(ctx, techs: dict[str, int]) -> None:
    ctx.var(CHOICES_VARIABLE)
    reset = {"type": "change_variable", "variable": CHOICES_VARIABLE, "operation": "SET", "quantity": 0}

    for value, numbers in ((1, (1,)), (2, (1, 2))):
        ctx.trigger(
            f"Shop: re-enable {'both choices' if value == 2 else 'choice 1'}",
            [{"type": "variable_value", "variable": CHOICES_VARIABLE, "comparison": "EQUAL", "quantity": value}],
            [*(_enable(techs[choice_key(n)]) for n in numbers), reset],
            looping=True,
        )


def variable_id(ctx, name: str) -> int:
    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def xs(config: ShopConfig, techs: dict[str, int], choices_variable: int) -> str:
    boons = shop_pool.boons(config)
    data = xs_data(config, techs, boons, shop_pool.categories(config, boons), choices_variable)

    return data + "\n" + RUNTIME.read_text(encoding="utf-8")


def add(ctx, config: ShopConfig, techs: dict[str, int]) -> None:
    _triggers(ctx, techs)
    ctx.xs(xs(config, techs, variable_id(ctx, CHOICES_VARIABLE)))
