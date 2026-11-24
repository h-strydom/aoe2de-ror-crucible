"""The Legion's bases (docs/arena.md) as optional objectives: destroying one gives a boon choice in the shop, as a
defeated wave does.

Destroying one also gives a free reroll more, with the Trade Workshop's Rerolls (playtest 2026-11-24).

A base is destroyed when every building of it is, but its walls and farms (a base is its working buildings and towers;
nobody should have to clear every wall segment). The four walled posts of watch towers aren't bases: no objective.
"""

from crucible.datamod.mod import source_dat

LEGION = 3
WALL_CLASSES, FARM_CLASS = (27, 39), 49  # walls and gates; farms
BUILDING = 80
PAD = 2  # tiles around a base's box: a few buildings stand on its edge
BASES = (  # objective name, (x0, x1, y0, y1) as in docs/arena.md
    ("Western Outpost", (18, 28, 40, 54)),  # the north-west island outpost
    ("Eastern Outpost", (184, 218, 2, 46)),  # the north-east island outpost
    ("Southern Farming District", (94, 116, 160, 182)),
    ("Southern Mining District", (69, 90, 205, 212)),
    ("Western Military District", (6, 26, 198, 220)),  # the south-west one (stables)
    ("Southern Military District", (131, 157, 198, 215)),  # the south-south-east one (archery ranges)
)


def buildings(s, box: tuple[int, int, int, int]) -> list:
    """The Legion buildings that make up the base in `box`."""
    units = source_dat().civs[1].units
    x0, x1, y0, y1 = box

    def counts(u) -> bool:
        data = units[u.unit_const]
        inside = x0 - PAD <= u.x <= x1 + 1 + PAD and y0 - PAD <= u.y <= y1 + 1 + PAD

        return inside and data.type == BUILDING and data.class_ not in (*WALL_CLASSES, FARM_CLASS)

    return [u for u in s.unit_manager.units[LEGION] if counts(u)]


def add(ctx, s) -> None:
    """An objective per base; its completion calls crucibleShopOpen() (the shop's XS)."""
    for n, (name, box) in enumerate(BASES):
        found = buildings(s, box)

        if not found:
            raise ValueError(f"no Legion buildings in {name}")

        text = f"Destroy {name}"
        ctx.trigger(
            f"Base: {name}",
            [{"type": "destroy_object", "unit_object": u.reference_id} for u in found],
            [
                {
                    "type": "script_call",
                    "message": f"void crucibleBaseDestroyed{n}() {{ crucibleShopOpen(); crucibleShopRerollGift(); }}",
                },
                {"type": "send_chat", "source_player": 1, "message": f"{name} destroyed: a boon choice."},
            ],
            display_as_objective=True,
            display_on_screen=True,
            description=text,
            short_description=text,
        )
