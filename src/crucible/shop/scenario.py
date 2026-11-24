"""Adding the shop to a scenario: the two triggers that re-enable the choices, then the XS (data block + runtime).

The scenario calls crucibleShopOpen() from its own XS when a wave is defeated (and a base's objective does).
"""

from pathlib import Path

from crucible.datamod.shop import REROLL_FREE, REROLL_PAID, SPIES, choice_key
from crucible.shop import pool as shop_pool
from crucible.shop.config import ShopConfig
from crucible.shop.data import xs_data

RUNTIME = Path(__file__).with_name("shop.xs")
CHOICES_VARIABLE = "crucible_shop_choices"  # 1: re-enable choice 1, 2: re-enable both (XS sets it, triggers reset)
REROLL_VARIABLE = "crucible_shop_reroll"  # 1: show the free reroll, 2: the paid one (XS sets it, triggers reset)
REVEAL_MAP = 203  # resource: 2 = the whole map visible, no fog
PLAYER = 1


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


def _extras(ctx, techs: dict[str, int], spies: str) -> None:
    """The reroll's two techs, shown when XS says; Spies shown with its upgrade, and once researched the map."""
    ctx.var(REROLL_VARIABLE)
    reset = {"type": "change_variable", "variable": REROLL_VARIABLE, "operation": "SET", "quantity": 0}

    for value, key in ((1, REROLL_FREE), (2, REROLL_PAID)):
        ctx.trigger(
            f"Shop: show the {key.replace('_', ' ')}",
            [{"type": "variable_value", "variable": REROLL_VARIABLE, "comparison": "EQUAL", "quantity": value}],
            [_enable(techs[key]), reset],
            looping=True,
        )

    ctx.var(spies)
    ctx.trigger(
        "Shop: Spies on offer",
        [
            {"type": "timer", "timer": 2},  # after the bank's load and the XS hiding it
            {"type": "variable_value", "variable": spies, "comparison": "LARGER_OR_EQUAL", "quantity": 1},
        ],
        [_enable(techs[SPIES])],
    )
    ctx.trigger(
        "Shop: Spies",
        [{"type": "research_technology", "source_player": PLAYER, "technology": techs[SPIES]}],
        [
            {
                "type": "modify_resource",
                "tribute_list": REVEAL_MAP,
                "source_player": PLAYER,
                "quantity": 2,
                "operation": "SET",
            }
        ],
    )


def variable_id(ctx, name: str) -> int:
    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def xs(config: ShopConfig, techs: dict[str, int], choices_variable: int, **meta) -> str:
    """`meta`: the meta upgrades' trigger variables (see xs_data)."""
    boons = shop_pool.boons(config, techs)
    data = xs_data(config, techs, boons, shop_pool.categories(boons), choices_variable, **meta)

    return data + "\n" + RUNTIME.read_text(encoding="utf-8")


def add(
    ctx,
    config: ShopConfig,
    techs: dict[str, int],
    *,
    slots: str | None = None,
    speed: str | None = None,
    discount: str | None = None,
    discounts: tuple[int, ...] = (),
    rerolls: str | None = None,
    spies: str | None = None,
) -> None:
    """`slots`, `speed` and `discount`: the names of the meta upgrades' trigger variables (more boons, faster boons,
    cheaper boons), if any; `discounts`: the percent off each discount level adds."""
    _triggers(ctx, techs)

    if rerolls and spies:
        _extras(ctx, techs, spies)

    meta = {
        "slots_variable": variable_id(ctx, ctx.var(slots)) if slots else -1,
        "speed_variable": variable_id(ctx, ctx.var(speed)) if speed else -1,
        "discount_variable": variable_id(ctx, ctx.var(discount)) if discount else -1,
        "discounts": discounts,
        "rerolls_variable": variable_id(ctx, ctx.var(rerolls)) if rerolls else -1,
        "reroll_signal": variable_id(ctx, REROLL_VARIABLE) if rerolls and spies else -1,
    }
    ctx.xs(xs(config, techs, variable_id(ctx, CHOICES_VARIABLE), **meta))
