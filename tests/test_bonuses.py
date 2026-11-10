import random

import pytest

from crucible.bonuses import catalogue
from crucible.bonuses.compile import commands
from crucible.bonuses.model import Civ, Game, Icon, Kind, Modifier, Stat, Tag, flat, pct


def test_ids_are_unique():
    ids = [m.id for m in catalogue.ALL]
    assert len(ids) == len(set(ids))


def test_query_and_pick_by_tag():
    stable = catalogue.query(tag=Tag.STABLE)
    assert {m.id for m in stable} == {"carthaginians_3", "carthaginians_4"}
    picked = catalogue.pick(4, random.Random(1), tag=Tag.STABLE)
    assert len(picked) == 2 and set(picked) <= set(stable)  # only 2 exist: all of them, no repeats


def test_team_bonus_is_its_own_kind():
    assert [m.id for m in catalogue.query(kind=Kind.TEAM)] == ["carthaginians_8"]


def test_compile_hp():
    camel = catalogue.by_id("carthaginians_4")
    assert commands(camel) == [(5, 329, -1, 0, 1.15)]


def test_compile_start_resources():
    assert commands(catalogue.by_id("carthaginians_1")) == [(1, r, 1, -1, 50) for r in range(4)]


def test_unsupported_stat_says_so():
    galley = catalogue.query(stat=Stat.ATTACK)[0]
    with pytest.raises(NotImplementedError, match="doesn't compile yet"):
        commands(galley)


def test_civs_know_their_game():
    assert Civ.CARTHAGINIANS.game is Game.ROR
    assert all(m.civ.game is Game.ROR for m in catalogue.ALL)


def test_typos_are_caught():
    base = {"change": pct(0.1), "stat": Stat.HP, "civ": Civ.GREEKS, "name": "Greeks 99"}
    with pytest.raises(ValueError, match="unknown ror targets"):
        Modifier(**base, targets=("hoplight",), tags=(), icon=Icon.ACADEMY)
    with pytest.raises(ValueError):
        Modifier(**base, targets=(), tags=("stabel",), icon=Icon.STABLE)
    with pytest.raises(ValueError):
        Modifier(**base, targets=(), tags=(), icon="farmm")
    with pytest.raises(TypeError):
        Modifier(pct(0.1), Stat.HP, (), (), Civ.GREEKS, "Positional")  # keyword arguments only


def test_descriptions_come_from_the_definition():
    by = catalogue.by_id
    assert by("carthaginians_1").description == "+50 all resources"
    assert by("carthaginians_2").description == "Hoplites, Phalangites, Centurions +25% HP"
    assert by("carthaginians_7").description == "Nobility -100% cost"
    assert by("carthaginians_8").description == "Team: Academies +20% work rate"
    bigger = by("carthaginians_1").model_copy(update={"change": flat(500)})
    assert bigger.description == "+500 all resources"  # change the number, the text follows


def test_plurals():
    from crucible.bonuses.model import plural

    assert [plural(t) for t in ("academy", "fire_galley", "war_elephant", "camel_rider")] == [
        "Academies",
        "Fire Galleys",
        "War Elephants",
        "Camel Riders",
    ]
