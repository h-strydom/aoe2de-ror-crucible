"""The friendly fire test scenario builds, its XS checks clean, and it holds one change per lane."""
from __future__ import annotations

from aoe2ed import triggers as T
from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import firetest as ft


def test_build(tmp_path):
    path, tracked = ft.build(tmp_path)
    assert len(tracked) == 4 * len(ft.LANES) and xs.check(ft.xs_code([u for _, u in tracked]))["ok"]
    o = SESSIONS.open(path)
    try:
        start = T.trigger_to_dict(next(t for t in o.scenario.trigger_manager.triggers if t.name == "Start"))
        levels = sorted((e["type"], e.get("quantity")) for e in start["effects"]
                        if e.get("object_attributes") == ft.BLAST_ATTACK_LEVEL)
        assert levels == [("modify_attribute", 6), ("modify_attribute", 10),
                          ("modify_object_attribute", 6), ("modify_object_attribute", 10)]
        assert sum(e["type"] == "task_object" for e in start["effects"]) == len(ft.LANES)
    finally:
        SESSIONS.close(o.handle)
