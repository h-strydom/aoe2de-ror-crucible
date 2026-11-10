"""Test: can XS alone place, disable and re-enable boon techs on the Wonder (no triggers per boon)?

If so, the shop runs entirely in XS: `xsEffectAmount(cModifyTech, tech, cAttrSetLocation / cAttrSetButton, ...)` and
`xsEffectAmount(cDisableTech, tech, cAttributeEnable / cAttributeDisable, 0, p)`.
"""

from crucible.bonuses import catalogue
from crucible.datamod.upgrades import WONDER

NAME = "xs_tech"
FIRST, SECOND = "carthaginians_4", "carthaginians_3"  # unplaced boons: camel and elephant HP
BOONS = (FIRST, SECOND)
BUTTONS: dict[str, int] = {}

STEPS = (  # (seconds, chat line, XS)
    (10, "placed boon 1 on button 3", "{place}({first}, 3);"),
    (15, "placed boon 2 on button 4", "{place}({second}, 4);"),
    (
        25,
        "disabled boon 2: button 4 should be empty",
        "xsEffectAmount(cDisableTech, {second}, cAttributeDisable, 0, 1);",
    ),
    (
        35,
        "re-enabled boon 2: button 4 should be back",
        "xsEffectAmount(cDisableTech, {second}, cAttributeEnable, 0, 1);",
    ),
)


def xs_code(techs: dict[str, int]) -> str:
    first, second = techs[FIRST], techs[SECOND]
    steps = "".join(
        f"""    if ((crucibleXsStep == {k}) && (xsGetTime() >= {seconds})) {{
        {xs.format(place="crucibleXsPlace", first=first, second=second)}
        xsChatData("{seconds} s: {line}");
        crucibleXsStep = {k + 1};
    }}
"""
        for k, (seconds, line, xs) in enumerate(STEPS)
    )

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
{steps}}}
"""


def setup(s, ctx, techs: dict[str, int], top: int) -> str:
    ctx.xs(xs_code(techs))
    first, second = catalogue.by_id(FIRST), catalogue.by_id(SECOND)
    timeline = "; ".join(f"{seconds} s: {line}" for seconds, line, _ in STEPS)

    return (
        f"XS TECH on the Wonder, no triggers: boon 1 is '{first.name}' ({first.description}), boon 2 is "
        f"'{second.name}' ({second.description}). {timeline}. Research boon 1 to see it apply. Chat narrates."
    )
