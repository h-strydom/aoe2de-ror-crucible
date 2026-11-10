"""Building and installing the Crucible data mod: RoR's data file, then each part, then the files."""

import json
import shutil
from pathlib import Path

from aoe2ed.screens import mod_dir

from crucible.bonuses.model import Modifier
from crucible.datamod import upgrades
from crucible.datamod.mod import MANIFEST, MOD, DataMod


def build(modifiers: list[Modifier], out: Path) -> Path:
    """Write the mod folder under `out`; returns it."""
    mod = DataMod.from_ror()
    upgrades.add(mod, modifiers)

    return mod.write(out)


def manifest(folder: Path) -> dict[str, int]:
    return json.loads((folder / MANIFEST).read_text(encoding="utf-8"))


def install(folder: Path) -> Path:
    """Copy the built mod into the profile's local mods (replacing an older copy)."""
    target = mod_dir(MOD, "ror")

    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(folder, target)

    return target
