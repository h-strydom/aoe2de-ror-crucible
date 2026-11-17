"""The Crucible campaign: the hub (crucible_hub), then a run (crucible_run). The campaign bank only works inside a
campaign, so meta upgrades bought in the hub reach the run only when they're played from here. Its name scopes the bank:
renaming it starts the bank over.
"""

from pathlib import Path

from aoe2ed.campaign import Campaign

NAME = "Crucible"


def build(out: Path, hub: Path, run: Path) -> Path:
    campaign = Campaign(NAME)
    campaign.add_scenario_file(hub, "The Camp")
    campaign.add_scenario_file(run, "The Crucible")

    return campaign.write(out / f"{NAME}.aoe2campaign")
