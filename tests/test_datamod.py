from aoe2ed.session import SESSIONS
from genieutils.datfile import DatFile

from crucible.bonuses import catalogue
from crucible.bonuses.model import Icon
from crucible.datamod import build, icons
from crucible.scenarios import upgrade_check


def test_one_upgrade_becomes_a_wonder_tech(tmp_path):
    camel = catalogue.by_id("carthaginians_4")
    folder = build.build([camel], tmp_path)
    tech_id = build.manifest(folder)[camel.id]
    data = DatFile.parse(str(folder / build.ROR_DAT / build.DAT_FILE))
    tech = data.techs[tech_id]
    location = tech.research_locations[0]
    assert (location.location_id, location.button_id) == (build.WONDER, 1)
    assert all(cost.type == -1 for cost in tech.resource_costs)  # free
    effect = [(c.type, c.a, c.c, round(c.d, 3)) for c in data.effects[tech.effect_id].effect_commands]
    assert effect == [(5, 329, 0, 1.15)]  # Camel Rider HP x1.15
    for strings_dir in build.STRINGS_DIRS:
        text = (folder / strings_dir / build.STRINGS_FILE).read_text(encoding="utf-8")
        assert f'{tech.language_dll_name} "Carthaginians 4"' in text
        assert "Camel Riders +15% HP" in text


def test_every_icon_has_a_source():
    data = build.source_dat()
    assert set(icons.SOURCES) == set(Icon)
    assert all(icons.icon_id(icon, data) >= 0 for icon in Icon)


def test_check_scenario_builds(tmp_path):
    path = upgrade_check.build(catalogue.by_id("carthaginians_4"), tmp_path)
    o = SESSIONS.open(path)
    try:
        units = [u.unit_const for u in o.scenario.unit_manager.units[1]]
        assert 276 in units and units.count(329) == 3  # the Wonder, three Camel Riders
    finally:
        SESSIONS.close(o.handle)
