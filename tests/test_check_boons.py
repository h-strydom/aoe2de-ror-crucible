import struct

from aoe2ed import xs as xs_check

from crucible.boons import catalogue
from crucible.boons.model import TIER_COSTS, Tier
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
    assert {step.player for step in steps} <= set(boons.TIER_PLAYERS)
    assert boons.places(steps)  # the shown rows fit the map
    assert xs_check.check(boons.xs(steps, techs))["ok"]


def test_report_flags_what_came_out_wrong(tmp_path):
    techs = _techs()
    dat = source_dat()
    steps = boons.plan(dat, techs)
    data = b""

    for k, step in enumerate(steps):
        before = [(boons.base(dat, r) if r.kind == "object" else None) for r in step.reads]
        before = [10.0 if b is None else float(b) for b in before]  # the labels' own values where there are any
        after = [r.expected(b) for r, b in zip(step.reads, before, strict=True)]

        if k == 0:
            after[0] += 5  # one wrong value

        data += struct.pack("<ii", boons.BEFORE, k) + struct.pack(f"<{len(before)}f", *before)
        data += struct.pack("<ii", boons.AFTER, k) + struct.pack(f"<{len(after)}f", *after)

    path = tmp_path / boons.FILE
    path.write_bytes(data + struct.pack("<i", boons.DONE))
    lines = boons.report(techs, path)

    assert len(lines) == 1
    assert lines[0].startswith(steps[0].key)


def test_labels_show_the_line_and_the_numbers():
    techs = _techs()
    data = source_dat()
    steps = boons.plan(data, techs)
    swords = next(s for s in steps if s.key == "boon choson_2 heirloom")
    axemen = next(s for s in steps if s.key == "boon choson_1 poor")
    units = data.civs[2].units

    assert {units[u].name for u in axemen.shown} == {"Axeman", "Clubman"}  # the line's earlier unit too
    assert boons.label(axemen, next(u for u in axemen.shown if units[u].name == "Clubman"), data) == "HP 40 -> 45"
    assert "melee armour 1 -> 2" in boons.label(swords, swords.shown[0], data)


def test_every_tier_costs_its_own_price():
    mod = DataMod.from_ror()
    boon_techs.add(mod)

    for boon in catalogue.ALL:
        for tier in boon.tiers:
            key = boon_techs.key(boon, tier)

            if key in mod.manifest:
                costs = [(c.type, c.amount) for c in mod.data.techs[mod.manifest[key]].resource_costs if c.amount]
                assert costs == list(TIER_COSTS[tier].items()), key

    assert not TIER_COSTS[Tier.POOR].items()  # free
    assert TIER_COSTS[Tier.HEIRLOOM].items() == [(0, 300), (3, 300)]
