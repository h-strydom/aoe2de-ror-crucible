"""crucible_arena: the run map, made by hand in the editor and kept in the repo (assets/crucible_arena.aoe2scenario).

`crucible arena save` copies the game's copy into the repo after editing; `crucible arena install` puts the repo's copy
in the game.
"""

import shutil
from pathlib import Path

from aoe2ed.config import paths

ROOT = Path(__file__).resolve().parents[3]
NAME = "crucible_arena"
FILE = f"{NAME}.aoe2scenario"
ARENA = ROOT / "assets" / FILE


def installed() -> Path:
    return paths().user_dir("scenario", "ror") / FILE


def save() -> Path:
    shutil.copy2(installed(), ARENA)

    return ARENA


def install() -> Path:
    target = installed()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ARENA, target)

    return target
