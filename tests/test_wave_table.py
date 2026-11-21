from crucible.datamod.mod import source_dat
from crucible.scenarios import wave_table as table
from crucible.scenarios import waves
from crucible.scenarios.wave_table import Age, Slot, Step


def test_every_line_is_a_real_unit():
    for line in table.LINES:
        assert table.unit_id(line.unit) >= 0, line.unit

    for unit in table.specials():
        assert table.unit_id(unit) >= 0, unit


def test_archetypes_start_and_climb():
    assert len(table.ARCHETYPES) >= len(waves.LANES)  # no two lanes the same
    start = {slot: table.BY_UNIT[unit] for slot, (unit, _) in table.START.items()}

    for archetype in table.ARCHETYPES:
        for slot in Slot:
            held = [table.BY_UNIT[u] for u in archetype.lines if table.BY_UNIT[u].slot == slot]
            assert start[slot] in held, (archetype.name, slot)
            assert max(line.age for line in held) >= Age.BRONZE, (archetype.name, slot)  # something to swap to


def test_new_steps_start_at_zero():
    assert table.STEPS[Step.NOTHING] == 0 and table.STEPS[Step.AGAIN] == 0
    assert sum(table.STEPS.values()) > 0


def test_every_upgrade_improves_something():
    data = source_dat()
    everyone = waves.units()
    techs = {u.tech for u in table.UPGRADES}

    for upgrade in table.UPGRADES:
        assert any(table.improves(data, upgrade, unit) for unit in everyone), upgrade.name
        assert upgrade.requires < 0 or upgrade.requires in techs, upgrade.name


def test_only_what_applies():
    data = source_dat()
    by_name = {u.name: u for u in table.UPGRADES}
    assert table.improves(data, by_name["Bronze Shield"], "slinger")
    assert not table.improves(data, by_name["Leather Armor (archers)"], "slinger")  # Slingers aren't archers
    assert not table.improves(data, by_name["Nobility"], "axeman")


def test_cadence():
    assert table.SEND_TIMES == {
        table.Difficulty.STANDARD: 300,
        table.Difficulty.MODERATE: 180,
        table.Difficulty.HARD: 120,
    }


def test_big_groups_fit_their_spawn_area():
    biggest = 60  # units in one lane's group, siege and Priest included
    rows = -(-biggest // waves.COLUMNS)
    assert 0.5 + (rows - 1) * waves.ROW_SPACING < waves.DEPTH + waves.MARGIN
    assert (waves.COLUMNS - 1) / 2 * waves.SPACING < 1 + waves.MARGIN  # within a row's width and its margin
