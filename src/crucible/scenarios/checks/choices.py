"""Test: the boon category choice cycle with one reused pair of choice techs.

A click locks in (the other choice is disabled at once); when the pick finishes, both are re-enabled (a researched
tech comes back that way, confirmed) and renamed to the next round's categories.
"""

from crucible.datamod.shop import CHOICE_BUTTONS, choice_key

NAME = "choices"
BOONS: tuple[str, ...] = ()
BUTTONS: dict[str, int] = {}

ROUNDS = (("Stable", "Economy"), ("Cavalry", "Greek"), ("Stone", "Archery Range"))
DISABLE, ENABLE = "crucible_disable", "crucible_enable"  # trigger variables


def _triggers(ctx, techs: dict[str, int]) -> None:
    """Disable choice n when DISABLE is n; re-enable both when ENABLE is 1 (looping, so every round)."""
    for name in (DISABLE, ENABLE):
        ctx.var(name)

    for number in (1, 2):
        ctx.trigger(
            f"Disable choice {number}",
            [{"type": "variable_value", "variable": DISABLE, "comparison": "EQUAL", "quantity": number}],
            [
                {
                    "type": "enable_disable_technology",
                    "source_player": 1,
                    "technology": techs[choice_key(number)],
                    "enabled": 0,
                }
            ],
            looping=True,
        )

    ctx.trigger(
        "Re-enable choices",
        [{"type": "variable_value", "variable": ENABLE, "comparison": "EQUAL", "quantity": 1}],
        [
            *(
                {
                    "type": "enable_disable_technology",
                    "source_player": 1,
                    "technology": techs[choice_key(n)],
                    "enabled": 1,
                }
                for n in (1, 2)
            ),
            {"type": "change_variable", "variable": ENABLE, "operation": "SET", "quantity": 0},
            {"type": "change_variable", "variable": DISABLE, "operation": "SET", "quantity": 0},
        ],
        looping=True,
    )


def xs_code(techs: dict[str, int], disable: int, enable: int) -> str:
    """Names the choices for each round and runs the cycle; chat narrates."""
    first, second = (techs[choice_key(n)] for n in (1, 2))
    names = "".join(
        f"""    if (crucibleRound == {k}) {{
        xsSetTechName({first}, 1, "{a} boons");
        xsSetTechName({second}, 1, "{b} boons");
        xsSetTechDescription({first}, 1, "Round {k + 1}: {a} boons.");
        xsSetTechDescription({second}, 1, "Round {k + 1}: {b} boons.");
    }}
"""
        for k, (a, b) in enumerate(ROUNDS)
    )

    return f"""// ---- crucible check: choices ----
int crucibleRound = 0;
int cruciblePicked = 0;
bool crucibleNamed = false;

int crucibleChoice(int number = 0) {{
    if (number == 1) {{
        return ({first});
    }}

    return ({second});
}}

rule crucibleChoices
    active
    highFrequency
{{
    if (crucibleRound >= {len(ROUNDS)}) {{
        return;
    }}

    if (crucibleNamed == false) {{
{names}        crucibleNamed = true;
        xsChatData("Round %d: choose", crucibleRound + 1);
    }}

    if (cruciblePicked == 0) {{
        for (number = 1; < 3) {{
            int state = xsGetTechState(crucibleChoice(number), 1);

            if ((state == cTechStateResearching) || (state == cTechStateQueued)) {{
                cruciblePicked = number;
                xsSetTriggerVariable({disable}, 3 - number);
                xsChatData("Picked choice %d: the other is disabled", number);
            }}
        }}

        return;
    }}

    if (xsGetTechState(crucibleChoice(cruciblePicked), 1) == cTechStateDone) {{
        xsChatData("Round %d finished: re-enabling both", crucibleRound + 1);
        cruciblePicked = 0;
        crucibleNamed = false;
        crucibleRound = crucibleRound + 1;
        xsSetTriggerVariable({enable}, 1);
    }}
}}
"""


def setup(s, ctx, techs: dict[str, int], top: int) -> str:
    from crucible.scenarios.check import var_id

    _triggers(ctx, techs)
    ctx.xs(xs_code(techs, var_id(ctx, DISABLE), var_id(ctx, ENABLE)))
    rounds = ", then ".join(f"'{a}' or '{b}'" for a, b in ROUNDS)

    return (
        f"CHOICES on the Wonder, row 3 (buttons {CHOICE_BUTTONS[0]} and {CHOICE_BUTTONS[1]}): {rounds}. Each round: "
        "click one; the other should vanish at once (locked in, even if you cancel). When it finishes (1 s), both "
        "should come back with the next round's names, on the same buttons. Chat narrates."
    )
