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
        kinds = [(e["type"], e.get("object_attributes")) for e in start["effects"] if "modify" in e["type"]]
        assert kinds.count(("modify_attribute", ft.FRIENDLY_FIRE)) == 3       # lanes 3, 4 and the projectile
        assert ("modify_object_attribute", ft.FRIENDLY_FIRE) in kinds        # lane 2
        assert ("modify_object_attribute", ft.PROJECTILE_UNIT) in kinds      # lane 5
        assert sum(e["type"] == "task_object" for e in start["effects"]) == len(ft.LANES)
    finally:
        SESSIONS.close(o.handle)
