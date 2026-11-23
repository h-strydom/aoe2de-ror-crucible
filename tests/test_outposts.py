from aoe2ed.session import SESSIONS
from aoe2ed.tools.logic import xs_check

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


def test_every_outpost_has_spawn_tiles_and_the_xs_compiles():
    o = SESSIONS.open(asset("arena"))

    try:
        s = o.scenario
        outposts.take(s)

        for _, box in bases.BASES:
            found = bases.buildings(s, box)
            home = (sum(u.x for u in found) / len(found), sum(u.y for u in found) / len(found))
            assert len(outposts.spawn_tiles(s, home)) == outposts.SPAWN_TILES

        code = outposts.xs(s)
    finally:
        SESSIONS.close(o.handle)

    result = xs_check(code="int crucibleWaveAge = 0;\nint crucibleWaveFactor = 1;\n" + code)
    assert result["ok"] and not result["diagnostics"], result


def test_run_has_the_outposts(tmp_path, techs):
    o = SESSIONS.open(run.build(tmp_path, techs))

    try:
        code = "\n".join(e.message for t in o.scenario.trigger_manager.triggers for e in t.effects if e.message)
    finally:
        SESSIONS.close(o.handle)

    assert "rule crucibleOutposts" in code and code.index("crucibleWaveAge") < code.index("crucibleOutpostStart")
