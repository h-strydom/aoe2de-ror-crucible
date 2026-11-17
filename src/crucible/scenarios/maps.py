"""The hand-made maps, kept in the repo (assets/) as made in the editor: the arena (the run map) and meta (the hub).

`crucible map save <map>` copies the game's copy into the repo after editing; `crucible map install <map>` puts the
repo's copy in the game. The builds (crucible_run, crucible_hub) read them from assets/.
"""

import shutil
from pathlib import Path

from aoe2ed.config import paths

ROOT = Path(__file__).resolve().parents[3]
MAPS = {  # map -> its scenario's name, in the game and in assets/
    "arena": "crucible_arena",
    "meta": "meta",
}


def asset(name: str) -> Path:
    return ROOT / "assets" / f"{MAPS[name]}.aoe2scenario"


def installed(name: str) -> Path:
    return paths().user_dir("scenario", "ror") / f"{MAPS[name]}.aoe2scenario"


def save(name: str) -> Path:
    shutil.copy2(installed(name), asset(name))

    return asset(name)


def install(name: str) -> Path:
    target = installed(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(asset(name), target)

    return target
