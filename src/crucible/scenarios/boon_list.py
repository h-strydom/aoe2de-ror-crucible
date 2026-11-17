"""The boons researched, listed in the Objectives panel. The Scouts text can't change during a game (there's no effect
for it), so each boon has an objective line of its own, off until the boon is researched. A line's condition is never
met, so it stays a plain line rather than a ticked-off objective.
"""

from crucible.bonuses.model import Modifier

FIRST_ORDER = 10  # after the run's own objectives


def add(ctx, pool: list[Modifier], techs: dict[str, int], *, player: int = 1) -> None:
    never = {"type": "player_defeated", "source_player": 0}  # Gaia is never defeated

    for order, boon in enumerate(pool, start=FIRST_ORDER):
        line = f"Boon: {boon.id}"
        text = f"{boon.name}: {boon.description}"
        ctx.triggers(
            {
                "name": line,
                "enabled": False,
                "conditions": [never],
                "effects": [],
                "display_as_objective": True,
                "description": text,
                "short_description": text,
                "description_order": order,
            },
            {
                "name": f"Boon researched: {boon.id}",
                "conditions": [{"type": "research_technology", "source_player": player, "technology": techs[boon.id]}],
                "effects": [{"type": "activate_trigger", "trigger_id": line}],
            },
        )
