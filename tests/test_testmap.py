"""The engine test map builds, reloads, and holds every test it promises."""
from __future__ import annotations

from aoe2ed import tables
from aoe2ed import triggers as T
from aoe2ed.session import SESSIONS

from crucible import testmap
from crucible.cli import main


def test_cli_runs():
    assert main([]) == 0


def test_test_map(tmp_path):
    path = testmap.build(tmp_path)
    o = SESSIONS.open(path)
    try:
        s = o.scenario
        for name, (x1, y1, x2, y2) in testmap.strips().items():
            tile = s.map_manager.get_tile(x=(x1 + x2) // 2, y=(y1 + y2) // 2)
            assert tile.terrain_id == testmap.NO_BUILD[name], name
        names = {t.name: T.trigger_to_dict(t) for t in s.trigger_manager.triggers}
        safe = names["Safe zone"]
        assert safe["looping"] and [e["type"] for e in safe["effects"]] == ["enable_unit_attackable",
                                                                          "disable_unit_attackable"]
        amounts = names["Resource amounts"]["effects"]
        assert [e["quantity"] for e in amounts] == [testmap.FOOD_A, testmap.GOLD_ALL, testmap.STONE_EACH]
        assert names["Formation out"]["effects"][0]["action_type"] == testmap.LINE_FORMATION
        assert "Enemy attack" in names and "Reveal map" in names
        bush = tables.object_id("FORAGE_BUSH", "ror")
        assert sum(u.unit_const == bush for u in s.unit_manager.units[0]) == 8
    finally:
        SESSIONS.close(o.handle)
