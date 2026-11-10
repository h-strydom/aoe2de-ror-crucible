"""The Crucible data mod: Return of Rome's data file plus one hidden tech per upgrade.

Handing out an upgrade is researching its tech: by trigger for the player or the enemy, at the start of a run for
metaprogression, or from a button (the Wonder's, for the shop). Each tech's name and tooltip come from its
modifier, as strings shipped in the mod.
"""

import copy
import json
import shutil
from pathlib import Path

from aoe2ed import tables
from aoe2ed.config import find_game_dir
from aoe2ed.screens import mod_dir
from genieutils.datfile import DatFile

from crucible.bonuses.compile import commands
from crucible.bonuses.model import Modifier
from crucible.datamod.icons import icon_id

MOD = "Crucible"
ROR_DAT = Path("modes") / "Pompeii" / "resources" / "_common" / "dat"
DAT_FILE = "empires2_x2_p1.dat"

# The game copies this file into new mods for their strings; RoR's mode folder has none of its own, so it ships at
# both paths until a playtest shows which one RoR reads.
STRINGS_DIRS = (
    Path("resources") / "en" / "strings" / "key-value",
    Path("modes") / "Pompeii" / "resources" / "en" / "strings" / "key-value",
)

STRINGS_FILE = "key-value-modded-strings-utf8.txt"
MANIFEST = "crucible-upgrades.json"
FIRST_STRING = 7_100_000  # two strings per upgrade: name, tooltip
TEMPLATE_TECH = "axe"
WONDER, RESEARCH_TIME = 276, 10


def source_dat() -> DatFile:
    game = find_game_dir()

    if game is None:
        raise FileNotFoundError("AoE2 DE not found")

    return DatFile.parse(str(game / ROR_DAT / DAT_FILE))


def add_upgrade(data: DatFile, modifier: Modifier, index: int) -> tuple[int, dict[int, str]]:
    """Add `modifier` as a free, hidden tech researched at the Wonder (button `index + 1`). Returns the tech id
    and its strings."""
    template = data.techs[tables.tech_id(TEMPLATE_TECH.upper(), "ror")]
    command_template = data.effects[template.effect_id].effect_commands[0]

    effect = copy.deepcopy(data.effects[template.effect_id])
    effect.name = f"Crucible {modifier.id}"
    effect.effect_commands = []

    for kind, a, b, c, d in commands(modifier):
        command = copy.deepcopy(command_template)
        command.type, command.a, command.b, command.c, command.d = kind, a, b, c, d
        effect.effect_commands.append(command)

    data.effects.append(effect)

    name_id, help_id = FIRST_STRING + 2 * index, FIRST_STRING + 2 * index + 1

    tech = copy.deepcopy(template)
    tech.name = f"Crucible {modifier.id}"
    tech.effect_id = len(data.effects) - 1
    tech.civ, tech.type, tech.repeatable = -1, 0, 0
    tech.required_techs, tech.required_tech_count = (-1,) * 6, 0
    tech.language_dll_name, tech.language_dll_description = name_id, name_id
    tech.language_dll_help, tech.language_dll_tech_tree = help_id, help_id
    tech.icon_id = icon_id(modifier.icon, data)

    for cost in tech.resource_costs:
        cost.type, cost.amount, cost.flag = -1, 0, 0

    location = tech.research_locations[0]
    location.location_id, location.button_id, location.research_time = WONDER, index + 1, RESEARCH_TIME

    tech.research_locations = [location]
    data.techs.append(tech)

    strings = {name_id: modifier.name, help_id: f"Research <b>{modifier.name}<b> (<cost>)\n{modifier.description}"}

    return len(data.techs) - 1, strings


def build(modifiers: list[Modifier], out: Path) -> Path:
    """Write the mod folder under `out`; returns it. Its manifest maps each modifier id to its tech id."""
    data = source_dat()
    techs, strings = {}, {}

    for index, modifier in enumerate(modifiers):
        techs[modifier.id], new = add_upgrade(data, modifier, index)
        strings |= new

    folder = out / MOD

    if folder.exists():
        shutil.rmtree(folder)

    dat = folder / ROR_DAT / DAT_FILE
    dat.parent.mkdir(parents=True)
    data.save(str(dat))

    lines = "".join(f'{sid} "{text.replace(chr(10), "\\n")}"\n' for sid, text in strings.items())

    for strings_dir in STRINGS_DIRS:
        (folder / strings_dir).mkdir(parents=True, exist_ok=True)
        (folder / strings_dir / STRINGS_FILE).write_text(lines, encoding="utf-8")

    (folder / MANIFEST).write_text(json.dumps(techs, indent=2), encoding="utf-8")
    (folder / "info.json").write_text(
        json.dumps(
            {
                "Author": "aoe2de-ror-crucible",
                "CacheStatus": 0,
                "Title": MOD,
                "Description": "Crucible for Return of Rome: upgrades from every civ, handed out as techs.",
            }
        ),
        encoding="utf-8",
    )

    return folder


def manifest(folder: Path) -> dict[str, int]:
    return json.loads((folder / MANIFEST).read_text(encoding="utf-8"))


def install(folder: Path) -> Path:
    """Copy the built mod into the profile's local mods (replacing an older copy)."""
    target = mod_dir(MOD, "ror")

    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(folder, target)

    return target
