import math

from aoe2ed.session import SESSIONS
from aoe2ed.tools.logic import xs_check

from crucible.datamod.mod import source_dat
from crucible.scenarios import bases, outposts, run
from crucible.scenarios import wave_table as table
from crucible.scenarios.maps import asset


def test_pools_follow_the_path_and_the_age():
    found = outposts.pools()
    legion = table.ARCHETYPES.index(next(a for a in table.ARCHETYPES if a.name == "Legion"))

    def names(slot: table.Slot, age: table.Age) -> list[int]:
        return found[(legion * 2 + slot) * outposts.AGES + age]

    assert names(table.Slot.MELEE, table.Age.STONE) == [table.unit_id("clubman")]
    assert names(table.Slot.MELEE, table.Age.TOOL) == [table.unit_id("clubman"), table.unit_id("axeman")]
    assert table.unit_id("short_swordsman") in names(table.Slot.MELEE, table.Age.BRONZE)
    assert len(found) == len(table.ARCHETYPES) * 2 * outposts.AGES
    assert all(pool for pool in found[:: outposts.AGES])  # every slot fields something from the Stone Age
    assert all(outposts.ship_pools())  # ships from the Stone Age too


def test_the_player_types_include_villagers_soldiers_ships_and_docks():
    land, sea = outposts.player_types(source_dat())
    types = dict(land)

    assert types[83] and types[293]  # villagers
    assert not types[281]  # the Clubman is no villager
    assert 539 in sea and set(outposts.DOCKS) <= set(sea)


def test_the_plan_reads_the_markers_and_finds_doors_landings_and_spots():
    o = SESSIONS.open(asset("arena"))

    try:
        s = o.scenario
        markers = outposts.take(s)
        left = [u for u in s.unit_manager.units[outposts.MARKERS] if u.unit_const in outposts.MARKER_TYPES]
        p = outposts.plan(s, markers)
        code = outposts.xs(s, markers)
        exits = outposts.exits(s, markers["sea"])
    finally:
        SESSIONS.close(o.handle)

    assert not left  # the markers are off the map
    assert len(p["home"]) == len(bases.BASES)
    assert p["sea"] == [name in outposts.SEA_OUTPOSTS for name, _ in bases.BASES]

    for n, home in enumerate(p["home"]):
        docks = [at for _, at, dock in p["doors"][n] if dock]
        assert any(not dock for _, _, dock in p["doors"][n])  # land units come out of a building
        assert all(math.dist(post, home) < 40 for post in p["posts"][n]) and len(p["posts"][n]) >= 3

        if p["sea"][n]:
            assert docks and len(p["ship_spots"][n]) == 3
            assert len(p["landings"][n]) == outposts.KINGS_PER_SIDE
            assert all(math.dist(king, water) <= 6 for king, water in p["landings"][n])
            assert len(p["sea_markers"][n]) == 2
        else:
            assert not docks

    owners = [owner for _, owner, _ in p["spots"]]
    assert len(p["spots"]) == len(markers["spots"]) and min(owners) >= 0
    assert all(outposts.SPOT_GUARDS[0] <= guards <= outposts.SPOT_GUARDS[1] for _, _, guards in p["spots"])
    assert len(exits) == len(markers["sea"])

    prelude = "int crucibleWaveAge = 0;\nint crucibleWaveFactor = 1;\nint crucibleWaveDifficulty = 0;\n"
    result = xs_check(code=prelude + code)
    errors = [d for d in result["diagnostics"] if d["severity"] == "error"]
    assert result["ok"] and not errors, errors


def test_run_has_the_outposts(tmp_path, techs):
    o = SESSIONS.open(run.build(tmp_path, techs))

    try:
        code = "\n".join(e.message for t in o.scenario.trigger_manager.triggers for e in t.effects if e.message)
    finally:
        SESSIONS.close(o.handle)

    names = [tr.name for tr in o.scenario.trigger_manager.triggers]

    assert "rule crucibleOutposts" in code and code.index("crucibleWaveAge") < code.index("crucibleOutpostStart")
    assert sum(name.startswith("Outposts: ship") for name in names) == 4 * len(outposts.ship_types())
