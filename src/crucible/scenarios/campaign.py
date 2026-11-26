"""The Crucible campaign: the hub (crucible_hub), then a run (crucible_run). The campaign bank only works inside a
campaign, so meta upgrades bought in the hub reach the run only when they're played from here. Its name scopes the bank:
renaming it starts the bank over.

It ships as its own local mod, CAMPAIGN_MOD, with its intro slides (briefing.intro) as `<NAME>.json` beside it. The
game reads a campaign's intro only from an enabled mod, and only for a campaign whose internal name is its file's stem
(engine facts); the data mod stays disabled (it's picked on the campaign screen), so the slides in it never showed
(playtest 2026-11-26). The player enables this mod once, in Mods > Installed Mods.
"""

import json
import shutil
from pathlib import Path

from aoe2ed import game
from aoe2ed.campaign import Campaign
from aoe2ed.screens import mod_dir

from crucible.scenarios import briefing

NAME = "Crucible"
CAMPAIGN_MOD = "Crucible Campaign"
FOLDER = Path("modes") / "Pompeii" / "resources" / "_common" / "campaign"  # in the mod


def build(out: Path, hub: Path, run: Path) -> Path:
    campaign = Campaign(NAME)
    campaign.add_scenario_file(hub, "The Camp")
    campaign.add_scenario_file(run, "The Crucible")

    return campaign.write(out / f"{NAME}.aoe2campaign")


def mod(out: Path, campaign: Path) -> Path:
    """The campaign mod's folder in `out`: info.json, the campaign and its intro slides."""
    folder = out / CAMPAIGN_MOD

    if folder.exists():
        shutil.rmtree(folder)

    (folder / FOLDER).mkdir(parents=True)
    info = {
        "Author": "aoe2de-ror-crucible",
        "CacheStatus": 0,
        "Description": "The Crucible campaign for Return of Rome, with its intro slides. Play it with the Crucible "
        "data mod.",
        "Title": CAMPAIGN_MOD,
    }
    (folder / "info.json").write_text(json.dumps(info), encoding="utf-8")
    shutil.copy2(campaign, folder / FOLDER / campaign.name)
    (folder / FOLDER / f"{NAME}.json").write_text(json.dumps(briefing.intro(), indent=1), encoding="utf-8")

    return folder


def install(folder: Path) -> Path:
    """The campaign mod into the profile's local mods (replacing an older copy). The campaign once went in the
    profile's own campaign folder: that copy is removed, or the campaign would be listed twice."""
    target = mod_dir(CAMPAIGN_MOD, "ror")

    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(folder, target)
    (game.paths().user_dir("campaign", "ror") / f"{NAME}.aoe2campaign").unlink(missing_ok=True)

    return target
