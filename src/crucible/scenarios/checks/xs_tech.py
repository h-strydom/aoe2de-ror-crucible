"""Test: which way brings a boon button back after XS took it away? (XS placing and disabling work; XS's
cAttributeEnable doesn't bring one back.)

Three boons go on the Wonder at 5 s (buttons 1-3), are taken away at 10 s and brought back at 20 s, each a different way:
  1. XS disable, then the trigger Enable/Disable Technology (set off by a trigger variable);
  2. XS disable, then XS sets its state to Ready (cModifyTech, cAttrSetState);
  3. XS moves it to no building (cAttrSetLocation -1), then back onto the Wonder.
"""

from crucible.datamod.upgrades import WONDER

NAME = "xs_tech"
BOONS = ("carthaginians_4", "carthaginians_3", "egyptians_1")
BUTTONS: dict[str, int] = {}
REENABLE = "crucible_reenable"  # trigger variable: 1 = the trigger re-enables boon 1


def _trigger(ctx, tech: int) -> None:
    ctx.var(REENABLE)
    ctx.trigger(
        "Re-enable boon 1",
        [{"type": "variable_value", "variable": REENABLE, "comparison": "EQUAL", "quantity": 1}],
        [{"type": "enable_disable_technology", "source_player": 1, "technology": tech, "enabled": 1}],
    )


def xs_code(techs: dict[str, int], reenable: int) -> str:
    first, second, third = (techs[boon] for boon in BOONS)

    return f"""// ---- crucible check: xs_tech ----
int crucibleXsStep = 0;

void crucibleXsPlace(int tech = -1, int button = 0) {{
    xsEffectAmount(cModifyTech, tech, cAttrSetLocation, {WONDER}, 1);
    xsEffectAmount(cModifyTech, tech, cAttrSetButton, button, 1);
    xsEffectAmount(cDisableTech, tech, cAttributeEnable, 0, 1);
}}

rule crucibleXsTech
    active
    minInterval 1
{{
    if ((crucibleXsStep == 0) && (xsGetTime() >= 5)) {{
        crucibleXsPlace({first}, 1);
        crucibleXsPlace({second}, 2);
        crucibleXsPlace({third}, 3);
        xsChatData("5 s: boons on buttons 1, 2 and 3");
        crucibleXsStep = 1;
    }}

    if ((crucibleXsStep == 1) && (xsGetTime() >= 10)) {{
        xsEffectAmount(cDisableTech, {first}, cAttributeDisable, 0, 1);
        xsEffectAmount(cDisableTech, {second}, cAttributeDisable, 0, 1);
        xsEffectAmount(cModifyTech, {third}, cAttrSetLocation, -1, 1);
        xsChatData("10 s: all three should be gone");
        crucibleXsStep = 2;
    }}

    if ((crucibleXsStep == 2) && (xsGetTime() >= 20)) {{
        xsSetTriggerVariable({reenable}, 1);
        xsEffectAmount(cModifyTech, {second}, cAttrSetState, cTechStateReady, 1);
        crucibleXsPlace({third}, 3);
        xsChatData("20 s: 1 by trigger, 2 by XS state, 3 by moving back. Which came back?");
        crucibleXsStep = 3;
    }}
}}
"""


def setup(s, ctx, techs: dict[str, int], top: int) -> str:
    from crucible.scenarios.check import var_id

    _trigger(ctx, techs[BOONS[0]])
    ctx.xs(xs_code(techs, var_id(ctx, REENABLE)))

    return (
        "XS TECH on the Wonder: at 5 s three boons appear on buttons 1, 2 and 3; at 10 s all three go; at 20 s each "
        "is brought back a different way (1: trigger, 2: XS sets its state, 3: XS moves it back). Note which came "
        "back. Chat narrates."
    )
