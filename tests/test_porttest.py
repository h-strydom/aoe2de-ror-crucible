"""Ported units and exclusive techs: the data mod adds them, the scenario places them."""
from __future__ import annotations

from pathlib import Path

from genieutils.datfile import DatFile

from aoe2ed import xs
from aoe2ed.session import SESSIONS
from crucible import porttest, testmod


def test_data_mod_ports_and_exclusive_techs(tmp_path):
    folder = testmod.build_data_mod(tmp_path)
    d = DatFile.parse(str(folder / testmod.ROR_DAT / "empires2_x2_p1.dat"))
    ids = testmod.ported_ids()
    for src, button in testmod.PORTED.items():
        u = d.civs[2].units[ids[src]]
        assert u.enabled == 1 and (u.creatable.train_locations[0].unit_id, u.creatable.train_locations[0].button_id) \
            == (testmod.BARRACKS[0], button)
        assert d.graphics[u.standing_graphic[0]].file_name                   # its sprite reference came across
    for src, icon in testmod.PORTED_ICONS.items():
        assert d.civs[2].units[ids[src]].icon_id == icon                      # a RoR portrait, not AoE2's id
    assert d.civs[2].units[ids[2101]].nothing == ids[2174]                    # the Immortal's ranged form came too
    assert 0 not in ids                                                       # `nothing` = 0 isn't a link
    techs = testmod.exclusive_tech_ids()
    for tid in techs:
        disabled = {int(c.d) for c in d.effects[d.techs[tid].effect_id].effect_commands if c.type == 102}
        assert disabled == set(techs)                                         # each disables all three


def test_exclusive_script_checks():
    assert xs.check(porttest.xs_code(testmod.exclusive_tech_ids()))["ok"]


def test_scenario_places_ported_units(tmp_path):
    path = porttest.build(tmp_path)
    o = SESSIONS.open(path)
    try:
        mine = {u.unit_const for u in o.scenario.unit_manager.units[1]}
        assert all(testmod.ported_ids()[src] in mine for src in testmod.PORTED)
    finally:
        SESSIONS.close(o.handle)
