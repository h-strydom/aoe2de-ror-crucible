import struct

from aoe2ed import xs as xs_check

from crucible.boons import catalogue
from crucible.datamod import boons as boon_techs
from crucible.datamod.mod import DataMod, source_dat
from crucible.scenarios.checks import boons


def _techs() -> dict[str, int]:
    mod = DataMod.from_ror()
    boon_techs.add(mod)

    return mod.manifest


def test_every_tier_but_the_new_stats_compiles():
    mod = DataMod.from_ror()
    skipped = boon_techs.add(mod)
    tiers = sum(len(b.tiers) for b in catalogue.ALL)

    assert all("HP regeneration" in why or "conversion speed" in why for why in skipped.values())
    assert len([k for k in mod.manifest if k.startswith("boon ")]) == tiers - len(skipped)


def test_every_tier_tech_is_read_and_the_xs_checks():
    techs = _techs()
    steps = boons.plan(source_dat(), techs)

    assert len(steps) == len([k for k in techs if k.startswith("boon ")])
    assert all(step.reads for step in steps)
    assert {step.player for step in steps} == set(range(1, boons.PLAYERS + 1))
    assert xs_check.check(boons.xs(steps, techs))["ok"]


def test_report_flags_what_came_out_wrong(tmp_path):
    techs = _techs()
    steps = boons.plan(source_dat(), techs)
    data = b""

    for k, step in enumerate(steps):
        before = [10.0] * len(step.reads)
        after = [r.expected(10.0) for r in step.reads]

        if k == 0:
            after[0] += 5  # one wrong value

        data += struct.pack("<ii", boons.BEFORE, k) + struct.pack(f"<{len(before)}f", *before)
        data += struct.pack("<ii", boons.AFTER, k) + struct.pack(f"<{len(after)}f", *after)

    path = tmp_path / boons.FILE
    path.write_bytes(data + struct.pack("<i", boons.DONE))
    lines = boons.report(techs, path)

    assert len(lines) == 1
    assert lines[0].startswith(steps[0].key)
