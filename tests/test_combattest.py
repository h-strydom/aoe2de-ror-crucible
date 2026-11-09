"""The combat test scenario builds, its XS checks clean, and its record decodes."""
from __future__ import annotations

import struct

from aoe2ed import triggers as T
from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import combattest as ct


def test_build_and_xs(tmp_path):
    path, tracked = ct.build(tmp_path)
    assert xs.check(ct.xs_code([u for _, u in tracked]))["ok"]
    assert [label for label, _ in tracked][:3] == ["L1 own hoplite 1", "L1 own hoplite 2", "L1 centre target"]
    o = SESSIONS.open(path)
    try:
        start = T.trigger_to_dict(next(t for t in o.scenario.trigger_manager.triggers if t.name == "Start"))
        changed = {e["object_attributes"]: e.get("quantity", 0) for e in start["effects"]    # 0 is left out
                   if e["type"] == "modify_object_attribute"}
        assert changed[ct.FRIENDLY_FIRE] == 0 and changed[ct.BLAST_WIDTH] == 3 and changed[ct.MIN_RANGE] == 0
        assert changed[ct.MAX_RANGE] == 3 and changed[ct.PROJECTILE_UNIT] in (ct.BOLT, ct.SPARE_PROJECTILE)
        trade = [e for e in start["effects"] if e["type"] == "modify_resource"]
        assert {e["tribute_list"] for e in trade} == set(ct.TRADE_SHARES)
    finally:
        SESSIONS.close(o.handle)


def test_decode():
    tracked = [7, 8]
    head = [ct.MAGIC, ct.VERSION, len(tracked), *tracked]
    sample = [ct.TAG_SAMPLE, 15, 1, 2, 3, 4, 50, 120, -1]
    rec = ct.decode(struct.pack(f"<{len(head) + len(sample)}i", *head, *sample))
    assert rec["samples"][0]["stock"]["trade"] == 50 and rec["samples"][0]["hp"] == [120, -1]
