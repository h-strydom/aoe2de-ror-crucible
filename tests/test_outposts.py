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


def test_the_plan_spreads_posts_and_finds_beaches_and_spots():
    o = SESSIONS.open(asset("arena"))

    try:
        s = o.scenario
        markers = outposts.take(s)
        p = outposts.plan(s, markers)
        code = outposts.xs(s, markers)
    finally:
        SESSIONS.close(o.handle)

    assert len(p["home"]) == len(bases.BASES)
    assert all(len(found) == outposts.POSTS for found in p["posts"])
    assert p["sea"] == [name in outposts.SEA_OUTPOSTS for name, _ in bases.BASES]

    for n, home in enumerate(p["home"]):
        spread = max(math.dist(a, b) for a in p["posts"][n] for b in p["posts"][n])
        assert spread > 6, (n, spread)  # through the base, not in one corner

        if p["sea"][n]:
            land, water = p["beach"][n]
            assert 10 <= math.dist(land, home) <= 31 and math.dist(land, water) == 1
            assert all(m in markers["sea"] for m in p["markers"][n])
        else:
            assert p["markers"][n][0] in markers["land"]

    assert {kind for kind, _, _ in p["every_spot"]} == {"gold", "stone", "hunt"}
    assert sum(map(len, p["spots"])) > len(bases.BASES)

    result = xs_check(code="int crucibleWaveAge = 0;\nint crucibleWaveFactor = 1;\n" + code)
    errors = [d for d in result["diagnostics"] if d["severity"] == "error"]
    assert result["ok"] and not errors, errors


def test_run_has_the_outposts(tmp_path, techs):
    o = SESSIONS.open(run.build(tmp_path, techs))

    try:
        code = "\n".join(e.message for t in o.scenario.trigger_manager.triggers for e in t.effects if e.message)
    finally:
        SESSIONS.close(o.handle)

    assert "rule crucibleOutposts" in code and code.index("crucibleWaveAge") < code.index("crucibleOutpostStart")
