import random

import pytest

from crucible.bonuses import catalogue
from crucible.bonuses.compile import commands
from crucible.bonuses.model import Civ, Game, Kind, Modifier, Stat, Tag, pct


def test_ids_are_unique():
    ids = [m.id for m in catalogue.ALL]
    assert len(ids) == len(set(ids))


def test_query_and_pick_by_tag():
    stable = catalogue.query(tag=Tag.STABLE)
    assert {m.name for m in stable} == {"Elephant HP", "Camel HP"}
    picked = catalogue.pick(4, random.Random(1), tag=Tag.STABLE)
    assert len(picked) == 2 and set(picked) <= set(stable)  # only 2 exist: all of them, no repeats


def test_team_bonus_is_its_own_kind():
    assert [m.name for m in catalogue.query(kind=Kind.TEAM)] == ["Academies work faster"]


def test_compile_hp():
    camel = catalogue.by_id("carthaginians.camel_hp")
    assert commands(camel) == [(5, 329, -1, 0, 1.15)]


def test_compile_start_resources():
    assert commands(catalogue.by_id("carthaginians.start_resources")) == [(1, r, 1, -1, 50) for r in range(4)]


def test_unsupported_stat_says_so():
    galley = catalogue.query(stat=Stat.ATTACK)[0]
    with pytest.raises(NotImplementedError, match="doesn't compile yet"):
        commands(galley)


def test_civs_know_their_game():
    assert Civ.CARTHAGINIANS.game is Game.ROR
    assert all(m.civ.game is Game.ROR for m in catalogue.ALL)


def test_typos_are_caught():
    with pytest.raises(ValueError, match="unknown ror targets"):
        Modifier(change=pct(0.1), stat=Stat.HP, targets=("hoplight",), tags=(), civ=Civ.GREEKS, name="Typo")
    with pytest.raises(ValueError):
        Modifier(change=pct(0.1), stat=Stat.HP, targets=(), tags=("stabel",), civ=Civ.GREEKS, name="Typo")
    with pytest.raises(TypeError):
        Modifier(pct(0.1), Stat.HP, (), (), Civ.GREEKS, "Positional")  # keyword arguments only
