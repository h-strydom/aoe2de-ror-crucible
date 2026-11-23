"""Where the outpost waves will come from: markers placed on the arena by hand (2026-11-23), the Legion's female
villagers on land and its Light Transports at sea. The run takes them off the map (they'd be Legion units) and keeps
their tiles for the outposts to come.
"""

LEGION = 3
LAND_MARKER = 293  # VFBAS, the female villager
SEA_MARKER = 545  # Light Transport


def take(s) -> dict[str, list[tuple[float, float]]]:
    """Remove the markers from scenario `s`; returns their tiles: {"land": [...], "sea": [...]}."""
    units = s.unit_manager.units[LEGION]
    found = {"land": [], "sea": []}
    markers = []

    for unit in units:
        kind = {LAND_MARKER: "land", SEA_MARKER: "sea"}.get(unit.unit_const)

        if kind:
            found[kind].append((unit.x, unit.y))
            markers.append(unit)

    for unit in markers:
        s.unit_manager.remove_unit(unit=unit)

    return found
