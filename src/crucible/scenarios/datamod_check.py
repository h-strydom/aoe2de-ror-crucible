"""Losing at once without the Crucible data mod: a scenario doesn't record its data mod (engine facts), so the player
must pick it on the campaign screen. Without it Crucible's techs don't exist (xsGetTechState gives cTechStateInvalid):
a message says to pick it, then everything of the player's is killed, which loses the mission (there's no "declare
defeat" effect, and declaring an ally the winner would win it for the player too).
"""

VARIABLE = "crucible_no_data_mod"
DELAY = 5  # seconds to read the message
START = 2  # seconds before checking
ALWAYS = 101  # Tool Age: a tech every game has, to tell when tech states are ready


def _variable_id(ctx) -> int:
    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == VARIABLE)


def add(ctx, tech: int, *, player: int = 1) -> None:
    """`tech`: any of the data mod's techs."""
    ctx.var(VARIABLE)
    size = ctx.scenario.map_manager.map_size
    defeat = "No data mod: defeat"
    ctx.triggers(
        {
            "name": "No data mod",
            "conditions": [{"type": "variable_value", "variable": VARIABLE, "comparison": "EQUAL", "quantity": 1}],
            "effects": [
                {
                    "type": "display_instructions",
                    "source_player": player,
                    "display_time": DELAY + 5,
                    "instruction_panel_position": 0,
                    "message": "Crucible needs its data mod: pick Crucible as the Data Mod on the campaign screen.",
                },
                {"type": "activate_trigger", "trigger_id": defeat},
            ],
        },
        {
            "name": defeat,
            "enabled": False,
            "conditions": [{"type": "timer", "timer": DELAY}],
            "effects": [{"type": "kill_object", "source_player": player, "area": [0, 0, size - 1, size - 1]}],
        },
    )
    ctx.xs(
        f"""// ---- crucible: lose without the data mod ----
rule crucibleDataModCheck
    active
    minInterval 1
{{
    // on the first tick every tech reads invalid: wait for one RoR always has
    if ((xsGetTime() < {START}) || (xsGetTechState({ALWAYS}, {player}) == cTechStateInvalid)) {{
        return;
    }}

    if (xsGetTechState({tech}, {player}) == cTechStateInvalid) {{
        xsSetTriggerVariable({_variable_id(ctx)}, 1);
    }}

    xsDisableSelf();
}}
"""
    )
