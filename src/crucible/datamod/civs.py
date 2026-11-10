"""Bonus-less civs: one per architecture style. The player is Greek; the others are for looks (the map, the waves).

RoR keeps a civ's bonuses in two places only: its tech-tree effect (every command that isn't a tech disable) and
its team-bonus effect. Units and starting resources are the same for every civ apart from their graphics.
"""

from enum import IntEnum

from crucible.datamod.mod import DataMod

DISABLE_TECH = 102  # effect command type: what a tech tree is made of


class Style(IntEnum):
    """RoR's architecture styles, by the civ that represents each (its index in the data file)."""

    EGYPTIAN = 1  # Egyptians (also Assyrians, Hittites)
    GREEK = 2  # Greeks (also Minoans, Phoenicians)
    BABYLONIAN = 3  # Babylonians (also Sumerians, Persians)
    ASIAN = 10  # Shang (also Yamato, Choson, Lac Viet)
    ROMAN = 13  # Romans (also Carthaginians, Palmyrans, Macedonians)


PLAYER = Style.GREEK


def strip_bonuses(mod: DataMod) -> None:
    """Take every style's civ bonuses out, keeping its tech tree."""
    for style in Style:
        civ = mod.data.civs[style]
        tree = mod.data.effects[civ.tech_tree_id]
        tree.effect_commands = [c for c in tree.effect_commands if c.type == DISABLE_TECH]
        civ.team_bonus_id = -1
