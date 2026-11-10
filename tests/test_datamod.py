from aoe2ed import tables, xs
from aoe2ed.session import SESSIONS
from genieutils.datfile import DatFile

from crucible.bonuses import catalogue
from crucible.bonuses.model import Icon
from crucible.datamod import build, icons, mod, shop, strings, upgrades
from crucible.scenarios import check


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


def test_choices_sit_on_row_3(tmp_path):
    folder = build.build([], tmp_path)
    techs = build.manifest(folder)
    data = DatFile.parse(str(folder / mod.ROR_DAT / mod.DAT_FILE))

    for number, button in enumerate(shop.CHOICE_BUTTONS, start=1):
        tech = data.techs[techs[shop.choice_key(number)]]
        location = tech.research_locations[0]
        assert (location.location_id, location.button_id, tech.repeatable) == (upgrades.WONDER, button, 1)
        assert all(cost.type == -1 for cost in tech.resource_costs)  # free


def test_every_icon_has_a_source():
    data = mod.source_dat()
    assert set(icons.SOURCES) == set(Icon)
    assert all(icons.icon_id(icon, data) >= 0 for icon in Icon)


def test_check_scenario_builds(tmp_path):
    folder = build.build(check.upgrades(), tmp_path, buttons=check.PLACED)
    techs = build.manifest(folder)
    assert xs.check(check._choices_xs(techs))["ok"]

    path = check.build(tmp_path, techs)
    o = SESSIONS.open(path)

    try:
        units = [u.unit_const for u in o.scenario.unit_manager.units[1]]
        assert 276 in units  # the Wonder

        for modifier in check.upgrades():
            for target in modifier.targets:
                assert units.count(tables.object_id(target.upper(), "ror")) == 3

        move = next(t for t in o.scenario.trigger_manager.triggers if t.name == "Move a boon onto the Wonder")
        effect = move.effects[0]
        assert (effect.technology, effect.object_list_unit_id_2, effect.button_location) == (
            techs[check.MOVED[0]],
            upgrades.WONDER,
            check.MOVED[1],
        )
    finally:
        SESSIONS.close(o.handle)


def test_string_ids_count_up_and_escape_newlines():
    table = strings.Strings(first=10)
    assert (table.add("A"), table.add("B\nC")) == (10, 11)
    assert table.lines() == '10 "A"\n11 "B\\nC"\n'
