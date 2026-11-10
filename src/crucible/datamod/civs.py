"""Bonus-less civs with every tech: one per architecture style. The player is Greek; the others are for looks (the
map, the waves), so no civ has anything another lacks.

RoR keeps a civ's bonuses in two places only: its tech-tree effect (every command that isn't a tech disable) and
its team-bonus effect. Its tech tree is the disables in that same effect. Units and starting resources are the
same for every civ apart from their graphics.
"""

from enum import IntEnum

from crucible.datamod.mod import DataMod


class Style(IntEnum):
    """RoR's architecture styles, by the civ that represents each (its index in the data file)."""

    EGYPTIAN = 1  # Egyptians (also Assyrians, Hittites)
    GREEK = 2  # Greeks (also Minoans, Phoenicians)
    BABYLONIAN = 3  # Babylonians (also Sumerians, Persians)
    ASIAN = 10  # Shang (also Yamato, Choson, Lac Viet)
    ROMAN = 13  # Romans (also Carthaginians, Palmyrans, Macedonians)


PLAYER = Style.GREEK
SCENARIO_CIVS = {  # each style's civ as a scenario names it
    Style.EGYPTIAN: "EGYPTIAN",
    Style.GREEK: "GREEK",
    Style.BABYLONIAN: "BABYLONIAN",
    Style.ASIAN: "SHANG",
    Style.ROMAN: "ROMAN",
}


def strip_bonuses(mod: DataMod) -> None:
    """Empty every style's tech-tree effect (no bonuses, nothing disabled) and drop its team bonus."""
    for style in Style:
        civ = mod.data.civs[style]
        mod.data.effects[civ.tech_tree_id].effect_commands = []
        civ.team_bonus_id = -1
