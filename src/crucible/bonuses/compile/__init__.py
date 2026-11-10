"""Modifiers to game effect commands: (type, a, b, c, d) as in the data file's effects.

Each modifier becomes a hidden tech in the data mod whose effect is these commands, so handing a bonus to anyone
is one thing: research its tech. Percent changes to attacks and tech costs need the base values, so compiling reads
RoR's data file.
"""

from genieutils.datfile import DatFile

from crucible.bonuses.compile.stats import COMPILERS, Command
from crucible.bonuses.model import Modifier

__all__ = ["Command", "commands"]


def commands(m: Modifier, data: DatFile) -> list[Command]:
    if m.stat not in COMPILERS:
        raise NotImplementedError(f"{m.id}: {m.stat} doesn't compile yet")

    return COMPILERS[m.stat](m, data)
