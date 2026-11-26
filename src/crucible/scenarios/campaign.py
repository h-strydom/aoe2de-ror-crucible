"""The Crucible campaign: the hub (crucible_hub), then a run (crucible_run). The campaign bank only works inside a
campaign, so meta upgrades bought in the hub reach the run only when they're played from here. Its name scopes the bank:
renaming it starts the bank over.

Its intro slides (briefing.intro) go in the data mod's folder as `<NAME>.json`: the game reads a campaign's intro
only from a local mod, and only for a campaign whose internal name is its file's stem (engine facts).
"""

import json
from pathlib import Path

from aoe2ed.campaign import Campaign

from crucible.scenarios import briefing

NAME = "Crucible"


def build(out: Path, hub: Path, run: Path) -> Path:
    campaign = Campaign(NAME)
    campaign.add_scenario_file(hub, "The Camp")
    campaign.add_scenario_file(run, "The Crucible")

    return campaign.write(out / f"{NAME}.aoe2campaign")


def write_intro(mod: Path) -> Path:
    """The campaign's intro slides into the built mod folder `mod`."""
    path = mod / "modes" / "Pompeii" / "resources" / "_common" / "campaign" / f"{NAME}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(briefing.intro(), indent=1), encoding="utf-8")

    return path
