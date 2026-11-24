"""A data mod being built: RoR's data file, the strings to ship and the manifest, with the generic helpers every
part (upgrades, and later units or buildings) builds with."""

import copy
import json
import shutil
from pathlib import Path

from aoe2ed import tables
from aoe2ed.config import find_game_dir
from genieutils.datfile import DatFile

from crucible.datamod.strings import Strings

MOD = "Crucible"
ROR_DAT = Path("modes") / "Pompeii" / "resources" / "_common" / "dat"
DAT_FILE = "empires2_x2_p1.dat"
MANIFEST = "crucible-manifest.json"
TEMPLATE_TECH = "axe"  # new techs and effects start as copies of this one
NOWHERE = -1  # a tech's location when no building offers it (a trigger can place it later)
# Tech ids the game treats as its own whatever the data says: 408 is Spies (a boon that landed on it showed as Spies,
# with Spies' text and a price per enemy villager, playtest 2026-11-24). New techs skip them.
RESERVED_TECHS = (408,)

Command = tuple[int, int, int, int, float]  # an effect command: (type, a, b, c, d)


def source_dat() -> DatFile:
    game = find_game_dir()

    if game is None:
        raise FileNotFoundError("AoE2 DE not found")

    return DatFile.parse(str(game / ROR_DAT / DAT_FILE))


class DataMod:
    def __init__(self, data: DatFile) -> None:
        self.data = data
        self.strings = Strings()
        self.manifest: dict[str, int] = {}  # what each part added, by its own key (e.g. a modifier id -> tech id)
        self.files: dict[str, bytes] = {}  # more files to ship, by their path in the mod (e.g. widgetui pictures)

    @classmethod
    def from_ror(cls) -> "DataMod":
        return cls(source_dat())

    def _template(self):
        return self.data.techs[tables.tech_id(TEMPLATE_TECH.upper(), "ror")]

    def new_effect(self, name: str, commands: list[Command]) -> int:
        """Add an effect made of `commands`; returns its id."""
        template = self.data.effects[self._template().effect_id]
        command_template = template.effect_commands[0]

        effect = copy.deepcopy(template)
        effect.name = name
        effect.effect_commands = []

        for kind, a, b, c, d in commands:
            command = copy.deepcopy(command_template)
            command.type, command.a, command.b, command.c, command.d = kind, a, b, c, d
            effect.effect_commands.append(command)

        self.data.effects.append(effect)

        return len(self.data.effects) - 1

    def new_tech(
        self,
        name: str,
        *,
        effect: int,
        title: str,
        description: str,
        tooltip: str,
        icon: int,
        location: int,
        button: int,
        research_time: int,
        costs: list[tuple[int, int]] = (),
    ) -> int:
        """Add a tech for any civ, with no prerequisites, researched at `location` (a unit id, or NOWHERE until a
        trigger places it) on `button`; `costs` are up to three (resource id, amount) pairs, free if empty. `title`
        `description` (RoR's hover text, like "Upgrade to Battle Axe") and `tooltip` (AoE2's help text) are shipped
        as strings. Returns its id."""
        title_id, description_id = self.strings.add(title), self.strings.add(description)
        tooltip_id = self.strings.add(tooltip)

        tech = copy.deepcopy(self._template())
        tech.name = name
        tech.effect_id = effect
        tech.civ, tech.type, tech.repeatable = -1, 0, 0
        tech.required_techs, tech.required_tech_count = (-1,) * 6, 0
        tech.language_dll_name, tech.language_dll_description = title_id, description_id
        tech.language_dll_help, tech.language_dll_tech_tree = tooltip_id, tooltip_id
        tech.icon_id = icon

        for slot, cost in enumerate(tech.resource_costs):
            cost.type, cost.amount, cost.flag = (*costs[slot], 1) if slot < len(costs) else (-1, 0, 0)

        research = tech.research_locations[0]
        research.location_id, research.button_id, research.research_time = location, button, research_time

        tech.research_locations = [research]
        self._skip_reserved()
        self.data.techs.append(tech)

        return len(self.data.techs) - 1

    def _skip_reserved(self) -> None:
        """Fill a reserved id (RESERVED_TECHS) with a tech nobody can research: it needs itself (at research time 0
        with nothing needed the game would research it by itself, and 408 researched may well be Spies)."""
        while len(self.data.techs) in RESERVED_TECHS:
            filler = copy.deepcopy(self._template())
            filler.name = "Crucible reserved"
            filler.effect_id = -1
            filler.civ = -1
            filler.required_techs, filler.required_tech_count = (len(self.data.techs), -1, -1, -1, -1, -1), 1
            research = filler.research_locations[0]
            research.location_id, research.button_id, research.research_time = NOWHERE, 0, 1
            filler.research_locations = [research]
            self.data.techs.append(filler)

    def copy_unit(self, source: int) -> int:
        """Add a copy of unit `source` to every civ under a new id (the next free one); returns the id. The copy looks
        and acts like the source, but techs and triggers can tell it apart."""
        new = len(self.data.civs[0].units)

        for civ in self.data.civs:
            unit = copy.deepcopy(civ.units[source]) if civ.units[source] else None

            if unit:
                unit.id = unit.copy_id = unit.base_id = new

            civ.units.append(unit)

        return new

    def write(self, out: Path) -> Path:
        """Write the mod folder under `out` (replacing an older build); returns it."""
        folder = out / MOD

        if folder.exists():
            shutil.rmtree(folder)

        dat = folder / ROR_DAT / DAT_FILE
        dat.parent.mkdir(parents=True)
        self.data.save(str(dat))

        self.strings.write(folder)

        for path, data in self.files.items():
            (folder / path).parent.mkdir(parents=True, exist_ok=True)
            (folder / path).write_bytes(data)

        (folder / MANIFEST).write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")
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
