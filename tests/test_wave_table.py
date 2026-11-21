from crucible.datamod.mod import source_dat
from crucible.scenarios import wave_table as table
from crucible.scenarios import waves
from crucible.scenarios.wave_table import Age, Slot, Step


def test_every_unit_is_real():
    for unit in table.units():
        assert table.unit_id(unit) >= 0, unit


def test_families_climb_in_age():
    for family in table.FAMILIES:
        ages = [line.age for line in family.lines]
        assert ages == sorted(ages), family.name
        assert len(family.lines) <= waves.LINES, family.name


def test_paths_start_the_same_and_stay_in_their_slot():
    assert len(table.ARCHETYPES) >= len(waves.LANES)  # no two lanes the same

    for archetype in table.ARCHETYPES:
        for slot in (Slot.MELEE, Slot.RANGED):
            paths = archetype.paths[slot]
            assert 1 <= len(paths) <= waves.PATHS, archetype.name

            for path in paths:
                assert path[0] == (("Clubmen",) if slot == Slot.MELEE else ("Slingers",)), archetype.name
                assert len(path) <= waves.STAGES and all(len(stage) <= waves.OPTIONS for stage in path)

                for stage in path:
                    for name in stage:
                        assert name is None or table.BY_NAME[name].slot == slot, (archetype.name, name)


def test_post_iron_lines_are_main_only():
    swordsmen = table.BY_NAME["Swordsmen"]
    support = [line for line in swordsmen.lines if line.age < table.MAIN_ONLY]
    assert support[-1].unit == "long_swordsman"
    assert swordsmen.lines[-1].unit == "legionary" and swordsmen.lines[-1].age == Age.POST_IRON


def test_new_steps_start_at_zero():
    assert table.STEPS[Step.NOTHING] == 0 and table.STEPS[Step.AGAIN] == 0
    assert sum(table.STEPS.values()) > 0


def test_every_upgrade_improves_something():
    data = source_dat()
    techs = {u.tech for u in table.UPGRADES}

    for upgrade in table.UPGRADES:
        assert any(table.improves(data, upgrade, unit) for unit in table.units()), upgrade.name
        assert upgrade.requires < 0 or upgrade.requires in techs, upgrade.name


def test_only_what_applies():
    data = source_dat()
    by_name = {u.name: u for u in table.UPGRADES}
    assert table.improves(data, by_name["Bronze Shield"], "slinger")
    assert not table.improves(data, by_name["Leather Armor (archers)"], "slinger")  # Slingers aren't archers
    assert not table.improves(data, by_name["Nobility"], "axeman")


def test_cadence_and_scales():
    assert table.SEND_TIMES == {
        table.Difficulty.STANDARD: 300,
        table.Difficulty.MODERATE: 180,
        table.Difficulty.HARD: 120,
    }
    assert table.GROW_SCALE == table.UPGRADE_SCALE == table.SWAP_SCALE == 1  # curses raise these later


def test_big_groups_fit_their_spawn_area():
    biggest = 70  # units in one lane's group, siege and Priest included
    rows = -(-biggest // waves.COLUMNS)
    assert 0.5 + (rows - 1) * waves.ROW_SPACING < waves.DEPTH + waves.MARGIN + 3
    assert (waves.COLUMNS - 1) / 2 * waves.SPACING < 1 + waves.MARGIN  # within a row's width and its margin
