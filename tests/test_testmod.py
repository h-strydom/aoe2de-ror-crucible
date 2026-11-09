"""The data mod test builds: the data file carries exactly its changes, the dropsites mod adds Houses, the campaign
holds two missions."""
from __future__ import annotations

import json

import pytest
from aoe2ed.campaign import Campaign
from aoe2ed.config import find_game_dir

from crucible import testmod

pytestmark = pytest.mark.skipif(find_game_dir() is None, reason="needs Return of Rome's own data files")


def test_build(tmp_path):
    from genieutils.datfile import DatFile
    res = testmod.build(tmp_path)
    original = DatFile.parse(str(testmod._source_dat() / "empires2_x2_p1.dat"))
    modded = DatFile.parse(str(res["data_mod"] / testmod.ROR_DAT / "empires2_x2_p1.dat"))
    for uid, hp in testmod.HP.items():
        assert modded.civs[1].units[uid].hit_points == hp != original.civs[1].units[uid].hit_points
    tree = modded.effects[modded.civs[testmod.GREEK].tech_tree_id].effect_commands
    assert tree and all(c.type == 102 for c in tree)                      # Greek bonuses gone, disables kept
    egypt = original.civs[1].tech_tree_id                                 # other civs untouched
    assert len(modded.effects[egypt].effect_commands) == len(original.effects[egypt].effect_commands)
    assert json.loads((res["data_mod"] / "info.json").read_text())["Title"] == testmod.DATA_MOD

    # drop sites ship inside the data mod: a mod with its own dropsites.json counts as a separate data mod
    sites = json.loads((res["data_mod"] / testmod.ROR_DAT / "dropsites.json").read_text())["drop_site_list"]
    houses = [s for s in sites if s["building_id"] in testmod.HOUSE_IDS]
    assert len(houses) == 4 and all(t["name"] == "Trees" for s in houses for t in s["target_list"])
    for uid in testmod.LUMBERJACKS:                                      # and lumberjacks list the House to drop at
        assert testmod.HOUSE_IDS[0] in modded.civs[1].units[uid].bird.drop_sites
        assert testmod.HOUSE_IDS[0] not in original.civs[1].units[uid].bird.drop_sites

    camp = Campaign.read(res["campaign"])
    assert camp.name == testmod.CAMPAIGN and len(camp.scenarios) == 2
