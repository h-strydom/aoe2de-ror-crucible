"""The boons researched, listed in the Objectives panel. The Scouts text can't change during a game (there's no effect
for it), so each boon tier has an objective line of its own, off until that tier is researched. A line's condition is
never met, so it stays a plain line rather than a ticked-off objective.
"""

from crucible.boons.model import Boon
from crucible.datamod.boons import describe, key

FIRST_ORDER = 10  # after the run's own objectives


def add(ctx, pool: list[Boon], techs: dict[str, int], *, player: int = 1) -> None:
    never = {"type": "player_defeated", "source_player": 0}  # Gaia is never defeated
    order = FIRST_ORDER

    for boon in pool:
        for tier in boon.tiers:
            if key(boon, tier) not in techs:
                continue

            line = f"Boon: {key(boon, tier)}"
            text = describe(boon, tier)
            ctx.triggers(
                {
                    "name": line,
                    "enabled": False,
                    "conditions": [never],
                    "effects": [],
                    "display_as_objective": True,
                    # the Objectives panel only: on screen they covered it (playtest 2026-11-23); Hints can't change
                    # in a game
                    "description": text,
                    "short_description": text,
                    "description_order": order,
                },
                {
                    "name": f"Boon researched: {key(boon, tier)}",
                    "conditions": [
                        {"type": "research_technology", "source_player": player, "technology": techs[key(boon, tier)]}
                    ],
                    "effects": [{"type": "activate_trigger", "trigger_id": line}],
                },
            )
            order += 1
