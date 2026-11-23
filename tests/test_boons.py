import random

import pytest

from crucible.bonuses.model import Civ, Rarity, Stat, flat, pct
from crucible.boons import catalogue
from crucible.boons.model import LEVELS, MIN_CATEGORY, Boon, Domain, Flag, Kind, Subject, extra


def _boon(**fields) -> Boon:
    base = dict(
        civ=Civ.GREEKS,
        number=99,
        title="Test",
        stat=Stat.WORK_RATE,
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(Subject.VILLAGER,),
        rarity=Rarity.COMMON,
        effects=(pct(0.2),),
    )

    return Boon(**(base | fields))


def test_every_boon_is_valid_and_unique():
    ids = [b.id for b in catalogue.ALL]

    assert len(ids) == len(set(ids))
    assert {Civ(c) for c in Civ} == {b.civ for b in catalogue.ALL}
    assert all(b.levels in (1, LEVELS) for b in catalogue.ALL)
    assert all(b.rarity is Rarity.LEGENDARY for b in catalogue.ALL if b.levels == 1)  # the big ones


def test_a_level_adds_its_effects_and_text_shows_them():
    boon = _boon(effects=(pct(0.2), extra(flat(3), Stat.CARRY)))

    assert list(boon.steps) == [1, 2, 3, 4, 5]
    assert boon.text(1) == "+20% & +3 carry capacity"
    assert {e.stat: e.change.amount for e in boon.total(5)} == {None: 1.0, Stat.CARRY: 15}


def test_levels_are_one_to_five():
    with pytest.raises(ValueError, match="levels"):
        _boon(levels=6)

    assert list(_boon(levels=1).steps) == [1]


def test_stat_boons_stack_five_times():
    archers = catalogue.by_id("assyrians_2")  # +8% attack speed a level

    assert all(step[0].change.amount == 0.08 for step in archers.steps.values())
    assert archers.total(LEVELS)[0].change.amount == 0.4


def test_capped_cuts_overshoot_into_an_extra():
    cheap = _boon(stat=Stat.COST, targets=("priest",), effects=(pct(-0.2),))  # capped at -75% on level 4

    assert [s[0].change.amount for s in cheap.steps.values()][:4] == [-0.2, -0.2, -0.2, -0.15]
    assert cheap.steps[5][0].stat is Stat.TRAINING_SPEED  # past the cap: faster training instead
    fast = _boon(stat=Stat.TRAINING_SPEED, targets=("priest",), effects=(pct(0.3),))  # capped at +90% on level 3
    totals = {(e.stat or fast.stat): e.change.amount for e in fast.total(5)}
    assert totals == {Stat.TRAINING_SPEED: 0.9, Stat.COST: -0.1}
    assert all(
        e.change.amount >= -0.75
        for b in catalogue.ALL
        for e in b.total(b.levels)
        if (e.stat or b.stat) in (Stat.COST, Stat.FOOD_COST, Stat.WOOD_COST) and e.change.mode.value == "%"
    )


def test_offer_draws_each_choice_from_a_different_axis():
    choices = catalogue.choices()

    for seed in range(50):
        offered = catalogue.offer(3, random.Random(seed))
        axes = [type(category) for category, _ in offered]

        assert len(offered) == 3
        assert len(set(axes)) == 3
        assert len({b.id for _, b in offered}) == 3
        assert all(b.in_category(c) and c in choices and not b.in_category(Flag.DRAWBACK) for c, b in offered)


def test_choices_have_enough_boons_and_reach_every_boon():
    from crucible.boons.model import CivType

    choices = catalogue.choices()

    assert all(len(catalogue.query(c)) >= MIN_CATEGORY for c in choices)
    assert not any(isinstance(c, (Civ, CivType, Flag)) for c in choices)
    assert all(any(b.in_category(c) for c in choices) for b in catalogue.ALL)
