import pytest

from crucible.bonuses import catalogue
from crucible.bonuses.compile import commands
from crucible.datamod.mod import source_dat


@pytest.fixture(scope="module")
def data():
    return source_dat()


def compiled(boon: str, data) -> list:
    return commands(catalogue.by_id(boon), data)


def test_every_boon_compiles(data):
    assert all(commands(m, data) for m in catalogue.ALL)


def test_unit_attributes(data):
    assert compiled("carthaginians_4", data) == [(5, 329, -1, 0, 1.15)]  # HP x1.15
    assert compiled("carthaginians_1", data) == [(1, r, 1, -1, 50) for r in range(4)]


# The same commands as RoR's own civ bonuses (its Tech. Tree and Team Bonus effects).


def test_villager_jobs_like_egyptians(data):
    assert compiled("egyptians_3", data) == [(4, 579, -1, 14, 2.0), (4, 581, -1, 14, 2.0)]


def test_armour_and_attack_by_class(data):
    assert compiled("macedonians_2", data) == [(4, u, -1, 8, 3 * 256 + 2) for u in (93, 358, 359)]
    assert compiled("hittites_1", data) == [(4, -1, c, 9, 3 * 256 + 1) for c in (0, 36)]
    assert compiled("carthaginians_5", data) == [(4, 1103, -1, 9, 4 * 256 + 6)]  # 25% of 24 melee


def test_buildings_cover_every_age(data):
    assert [c[1] for c in compiled("greeks_6", data)] == [84, 116, 137]  # the Market in each age


def test_tech_cost_and_time(data):
    assert compiled("hittites_5", data) == [(103, 28, 1, 1, -45)]  # Wheel research time -50%
    assert compiled("carthaginians_7", data) == [(101, 34, 0, 0, 0), (101, 34, 3, 0, 0)]  # Nobility free


def test_player_resources(data):
    assert compiled("babylonians_7", data) == [(6, 195, -1, -1, 1.1)]  # construction rate
    assert compiled("macedonians_4", data) == [(1, 77, 0, -1, 4.0)]  # conversion resistance set to 4
    assert compiled("sumerians_3", data) == [(1, 36, 1, -1, 125.0)]  # farm food


def test_research_speed_like_palmyrans(data):
    assert compiled("palmyrans_9", data) == [(1, 86, 0, -1, 0.7692)]  # research time set to 1/1.3
