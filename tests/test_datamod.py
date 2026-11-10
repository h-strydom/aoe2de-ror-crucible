from aoe2ed import xs
from aoe2ed.session import SESSIONS
from genieutils.datfile import DatFile

from crucible.bonuses import catalogue
from crucible.bonuses.model import Icon
from crucible.datamod import build, icons, mod, shop, strings, upgrades
from crucible.scenarios import check
from crucible.scenarios.checks import TESTS, choices


def test_boons_become_techs_placed_or_not(tmp_path):
    camel, elephants = catalogue.by_id("carthaginians_4"), catalogue.by_id("carthaginians_3")
    folder = build.build([camel, elephants], tmp_path, buttons={camel.id: 1})
    techs = build.manifest(folder)
    data = DatFile.parse(str(folder / mod.ROR_DAT / mod.DAT_FILE))

    tech = data.techs[techs[camel.id]]
    location = tech.research_locations[0]
    assert (location.location_id, location.button_id) == (upgrades.WONDER, 1)
    costs = [(cost.type, cost.amount) for cost in tech.resource_costs if cost.type >= 0]
    assert costs == camel.cost.items() == [(0, 250)]  # common: 250 food
    assert location.research_time == upgrades.RESEARCH_TIME
    effect = [(c.type, c.a, c.c, round(c.d, 3)) for c in data.effects[tech.effect_id].effect_commands]
    assert effect == [(5, 329, 0, 1.15)]  # Camel Rider HP x1.15

    unplaced = data.techs[techs[elephants.id]].research_locations[0]
    assert unplaced.location_id == mod.NOWHERE

    for strings_dir in strings.STRINGS_DIRS:
        text = (folder / strings_dir / strings.STRINGS_FILE).read_text(encoding="utf-8")
        assert f'{tech.language_dll_name} "Carthaginians 4"' in text
        assert "Camel Riders +15% HP" in text


def test_one_choice_pair_on_the_wonder(tmp_path):
    folder = build.build([], tmp_path)
    techs = build.manifest(folder)
    data = DatFile.parse(str(folder / mod.ROR_DAT / mod.DAT_FILE))

    for number, button in enumerate(shop.CHOICE_BUTTONS, start=1):
        choice = data.techs[techs[shop.choice_key(number)]]
        location = choice.research_locations[0]
        assert (location.location_id, location.button_id) == (upgrades.WONDER, button)
        assert all(cost.type == -1 for cost in choice.resource_costs)  # free


def test_every_icon_has_a_source():
    data = mod.source_dat()
    assert set(icons.SOURCES) == set(Icon)
    assert all(icons.icon_id(icon, data) >= 0 for icon in Icon)


def test_check_scenario_builds_every_test(tmp_path):
    tests = list(TESTS)
    folder = build.build(check.boons(tests), tmp_path, buttons=check.buttons(tests))
    techs = build.manifest(folder)
    assert xs.check(choices.xs_code(techs, disable=0, enable=1))["ok"]

    path = check.build(tmp_path, techs, tests)
    o = SESSIONS.open(path)

    try:
        units = [u.unit_const for u in o.scenario.unit_manager.units[1]]
        assert 276 in units  # the Wonder
        names = {t.name for t in o.scenario.trigger_manager.triggers}
        assert {"Disable choice 1", "Disable choice 2", "Re-enable choices"} <= names
    finally:
        SESSIONS.close(o.handle)


def test_string_ids_count_up_and_escape_newlines():
    table = strings.Strings(first=10)
    assert (table.add("A"), table.add("B\nC")) == (10, 11)
    assert table.lines() == '10 "A"\n11 "B\\nC"\n'
