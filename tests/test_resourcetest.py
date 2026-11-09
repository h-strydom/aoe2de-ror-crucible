"""The resource test scenario builds, its XS checks clean, and its record decodes."""
from __future__ import annotations

import struct

from aoe2ed import triggers as T
from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import resourcetest as rt


def test_build_and_xs(tmp_path):
    path, tracked, labels = rt.build_mission(tmp_path)
    assert labels == rt.PILE_LABELS and len(tracked) == len(rt.PILE_LABELS)
    assert xs.check(rt.xs_code(tracked))["ok"]
    o = SESSIONS.open(path)
    try:
        names = {t.name: T.trigger_to_dict(t) for t in o.scenario.trigger_manager.triggers}
        swaps = [e for e in names["Resource settings"]["effects"] if e.get("object_attributes") == rt.STORAGE_TYPE]
        assert sorted(e["quantity"] for e in swaps) == [rt.STONE, rt.STONE, rt.GOLD, rt.GOLD]
        assert len(names["Start working"]["effects"]) == 6             # five lanes and the boat
    finally:
        SESSIONS.close(o.handle)


def test_decode():
    tracked = [11, 12, 13, 14, 15, 16]
    head = [rt.MAGIC, rt.VERSION, 6, len(tracked), *tracked]
    sample = [rt.TAG_SAMPLE, 30] + [v for p in range(6) for v in (p, p * 10, p * 100, p * 1000)] \
        + [v for k in range(6) for v in (100 - k, 3)]
    rec = rt.decode(struct.pack(f"<{len(head) + len(sample)}i", *head, *sample))
    s = rec["samples"][0]
    assert s["t"] == 30 and s["stock"][3]["stone"] == 200 and s["piles"][0] == (100, 3)
