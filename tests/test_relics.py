from aoe2ed.session import SESSIONS

from crucible import meta
from crucible.datamod import artifacts
from crucible.datamod.mod import DataMod, source_dat
from crucible.scenarios import outposts, relics, run
from crucible.scenarios.maps import asset


def test_the_arena_has_the_spots_and_the_markers():
    o = SESSIONS.open(asset("arena"))

    try:
        s = o.scenario
        gaia = [u.unit_const for u in s.unit_manager.units[relics.GAIA]]
        assert gaia.count(relics.RUIN) == meta.RUIN_SPOTS and gaia.count(relics.ARTIFACT) == meta.ARTIFACT_SPOTS
        spawns = outposts.take(s)
        assert len(spawns["land"]) == 3 and len(spawns["sea"]) == 4
        legion = [u.unit_const for u in s.unit_manager.units[outposts.LEGION]]
        assert outposts.LAND_MARKER not in legion and outposts.SEA_MARKER not in legion
    finally:
        SESSIONS.close(o.handle)


def test_run_keeps_ruins_and_artifacts_by_level(tmp_path, techs):
    o = SESSIONS.open(run.build(tmp_path, techs))

    try:
        s = o.scenario
        gaia = s.unit_manager.units[relics.GAIA]
        placed = [u for u in gaia if u.unit_const == techs[relics.ARTIFACT_KEY]]
        assert len(placed) == meta.ARTIFACT_SPOTS and all(u.capture_flag == relics.CAPTURE_MULTIPLE for u in placed)
        assert not any(u.unit_const == relics.ARTIFACT for u in gaia)
        names = {t.name for t in s.trigger_manager.triggers}
        assert {f"Relics: ruin {n} not this run" for n in range(meta.RUIN_SPOTS)} <= names
        assert {f"Relics: artifact {n} not this run" for n in range(meta.ARTIFACT_SPOTS)} <= names
        legion = [u.unit_const for u in s.unit_manager.units[outposts.LEGION]]
        assert outposts.LAND_MARKER not in legion and outposts.SEA_MARKER not in legion
        code = "\n".join(e.message for t in s.trigger_manager.triggers for e in t.effects if e.message)
        assert "crucibleRelicPick" in code and "xsGetGarrisonedInUnitId" in code
    finally:
        SESSIONS.close(o.handle)


def test_every_building_type_takes_an_artifact():
    mod = DataMod.from_ror()
    artifacts.add(mod)
    units = mod.data.civs[1].units
    copy = units[mod.manifest[relics.ARTIFACT_KEY]]

    assert copy.class_ == artifacts.PRIEST_CLASS and copy.speed > 0
    for name, ids in relics.groups(source_dat()).items():
        for i in ids:
            assert units[i].building.garrison_type & artifacts.PRIEST_CATEGORY, (name, i)
            assert units[i].garrison_capacity >= 1, (name, i)


def test_towers_are_places_for_the_stages():
    for key in ("tower_2", "tower_3", "tower_4"):
        assert meta.place(key).opened_by

    stages = [u for u in meta.UPGRADES if u.place.startswith("tower_")]
    assert len(stages) == 6 and all(u.requires for u in stages)
