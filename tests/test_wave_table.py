from crucible.scenarios import wave_table as table
from crucible.scenarios import waves
from crucible.scenarios.wave_table import Age, Difficulty


def test_every_wave_has_melee_and_ranged():
    for difficulty in Difficulty:
        assert len(table.GROUPS[difficulty]) == table.WAVES

        assert table.group(difficulty, 0).other == 0  # wave 0: melee only

        for wave in range(1, table.WAVES):
            group = table.group(difficulty, wave)
            assert group.main >= 1 and group.other >= 1, (difficulty, wave)


def test_proposal_numbers():
    assert table.GROUPS[Difficulty.HARD][1] == table.Group(4, 2)
    assert table.group(Difficulty.STANDARD, 9) == table.Group(8, 3, 3)
    assert table.group(Difficulty.MODERATE, 20) == table.group(Difficulty.MODERATE, 9)  # fighting on


def test_legion_ages():
    assert table.legion_age(Difficulty.STANDARD, 3) == Age.STONE
    assert table.legion_age(Difficulty.HARD, 2) == Age.TOOL
    assert table.legion_age(Difficulty.MODERATE, 9) == Age.POST_IRON


def test_siege_only_from_bronze():
    for difficulty in Difficulty:
        for wave in range(table.WAVES):
            if table.group(difficulty, wave).siege:
                assert table.legion_age(difficulty, wave) >= Age.BRONZE, (difficulty, wave)


def test_archetypes_cover_every_age_and_fit():
    assert len(table.ARCHETYPES) >= len(waves.LANES)  # no two lanes the same

    for archetype in table.ARCHETYPES:
        for age in Age:
            main, other = table.choices(archetype, age)
            assert main and other and len(main) <= waves.CHOICES and len(other) <= waves.CHOICES

            for name in main + other:
                assert table.unit_id(name) >= 0, name


def test_groups_fit_their_spawn_rows():
    biggest = max(table.group(d, w).units + 1 for d in Difficulty for w in range(table.WAVES))
    rows = -(-biggest // waves.COLUMNS)
    assert 0.5 + (rows - 1) * waves.ROW_SPACING < waves.DEPTH
