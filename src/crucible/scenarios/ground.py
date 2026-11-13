"""The arena as edited by hand (assets/arena_edited.aoe2scenario) on even ground: every tile Dirt Mud at elevation 5.

Units, players and everything else stay as they are. It is installed as crucible_arena, in place of the edited one.
"""

from pathlib import Path

from aoe2ed.session import SESSIONS

from crucible.scenarios.arena import NAME
from crucible.scenarios.parts import EDITED, MUD

ELEVATION = 5


def build(out: Path) -> Path:
    o = SESSIONS.open(EDITED)

    try:
        for tile in o.scenario.map_manager.terrain:
            tile.terrain_id = MUD
            tile.elevation = ELEVATION

        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{NAME}.aoe2scenario"
        SESSIONS.save(o.handle, path, overwrite=True)

        return path
    finally:
        SESSIONS.close(o.handle)
