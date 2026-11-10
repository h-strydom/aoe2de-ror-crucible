import random

import pytest

from crucible.bonuses import catalogue
from crucible.bonuses.compile import commands
from crucible.bonuses.model import Stat


def test_ids_are_unique():
    ids = [m.id for m in catalogue.ALL]
    assert len(ids) == len(set(ids))


def test_query_and_pick_by_tag():
    stable = catalogue.query(tag="stable")
    assert {m.name for m in stable} == {"Elephant HP", "Camel HP"}
    picked = catalogue.pick(4, random.Random(1), tag="stable")
    assert len(picked) == 2 and set(picked) <= set(stable)  # only 2 exist: all of them, no repeats


def test_team_bonus_is_its_own_kind():
    assert [m.name for m in catalogue.query(kind="team")] == ["Academies work faster"]


def test_compile_hp():
    camel = catalogue.by_id("carthaginians.camel_hp")
    assert commands(camel) == [(5, 329, -1, 0, 1.15)]


def test_compile_start_resources():
    assert commands(catalogue.by_id("carthaginians.start_resources")) == [(1, r, 1, -1, 50) for r in range(4)]


def test_unsupported_stat_says_so():
    galley = catalogue.query(stat=Stat.ATTACK)[0]
    with pytest.raises(NotImplementedError, match="doesn't compile yet"):
        commands(galley)


def test_every_target_resolves():
    from crucible.bonuses.compile import object_id

    for m in catalogue.ALL:
        if m.stat is not Stat.TECH_COST:
            for t in m.targets:
                assert object_id(t) >= 0, t
