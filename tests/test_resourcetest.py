"""The resource test scenario builds, its XS checks clean, and its record decodes."""
from __future__ import annotations

import struct

from aoe2ed import triggers as T
from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import resourcetest as rt


def test_build_and_xs(tmp_path):
    path, tracked, labels = rt.build_mission(tmp_path)
    assert labels == rt.PILE_LABELS and len(tracked) == 5
    assert xs.check(rt.xs_code(tracked))["ok"]
    o = SESSIONS.open(path)
    try:
        names = {t.name: T.trigger_to_dict(t) for t in o.scenario.trigger_manager.triggers}
        settings = names["Resource settings"]["effects"]
        assert {(e.get("source_player"), e.get("tribute_list")) for e in settings if e["type"] == "modify_resource"} \
            >= {(3, rt.STONE_BONUS), (4, rt.STONE_BONUS), (6, rt.FOOD_GEN), (7, rt.MILITARY_FOOD), (8, rt.CHOPPING_GOLD)}
        assert len(names["Start working"]["effects"]) == 5            # four miner crews and the lumberjacks
    finally:
        SESSIONS.close(o.handle)


def test_decode():
    tracked = [11, 12, 13, 14, 15]
    head = [rt.MAGIC, rt.VERSION, 8, len(tracked), *tracked]
    sample = [rt.TAG_SAMPLE, 30] + [v for p in range(8) for v in (p, p * 10, p * 100, p * 1000)] + [750, 760, 770, 780, 5]
    rec = rt.decode(struct.pack(f"<{len(head) + len(sample)}i", *head, *sample))
    assert rec["samples"][0]["t"] == 30 and rec["samples"][0]["stock"][3]["stone"] == 200
    assert rec["samples"][0]["piles"] == [750, 760, 770, 780, 5]
