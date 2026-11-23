import random

import pytest

from crucible.bonuses.model import Civ, Stat, flat, pct
from crucible.boons import catalogue
from crucible.boons.model import Boon, Domain, Effect, Flag, Kind, Subject, Tier, extra, ladder


def test_every_boon_is_valid_and_unique():
    ids = [b.id for b in catalogue.ALL]

    assert len(ids) == len(set(ids))
    assert all(len(b.tiers) >= 1 for b in catalogue.ALL)
    assert {Civ(c) for c in Civ} == {b.civ for b in catalogue.ALL}


def test_ladder_adds_extras_and_text_shows_them():
    tiers = ladder(Tier.LEGENDARY, pct(0.2), (pct(0.4), extra(flat(3), Stat.CARRY)))
    boon = Boon(
        civ=Civ.GREEKS,
        number=99,
        title="Test",
        stat=Stat.WORK_RATE,
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(Subject.VILLAGER,),
        tiers=tiers,
    )

    assert sorted(tiers) == [Tier.LEGENDARY, Tier.HEIRLOOM]
    assert boon.lowest is Tier.LEGENDARY
    assert boon.text(Tier.LEGENDARY) == "+20%"
    assert boon.text(Tier.HEIRLOOM) == "+20% & +3 carry capacity"  # the step over Legendary


def test_tiers_must_be_consecutive():
    with pytest.raises(ValueError, match="consecutive"):
        Boon(
            civ=Civ.GREEKS,
            number=99,
            title="Gap",
            stat=Stat.HP,
            domain=Domain.MILITARY,
            kind=Kind.DURABILITY,
            subjects=(Subject.INFANTRY,),
            tiers={Tier.POOR: (Effect(change=flat(1)),), Tier.IMPROVED: (Effect(change=flat(2)),)},
        )


def test_choson_swordsmen_are_one_boon_up_to_heirloom():
    swords = catalogue.query(Civ.CHOSON, Subject.SWORDSMAN)

    assert len(swords) == 1
    assert max(swords[0].tiers) is Tier.HEIRLOOM
    assert len(swords[0].tiers[Tier.HEIRLOOM]) == 3  # HP and 1/1 armour


def test_offer_draws_each_choice_from_a_different_axis():
    for seed in range(50):
        choices = catalogue.offer(3, random.Random(seed))
        axes = [type(category) for category, _ in choices]

        assert len(choices) == 3
        assert len(set(axes)) == 3
        assert len({b.id for _, b in choices}) == 3
        assert all(b.in_category(category) and not b.in_category(Flag.DRAWBACK) for category, b in choices)


def test_every_boon_steps_up_to_heirloom_and_stacks():
    archers = catalogue.by_id("assyrians_2")  # written 11/22/33% from Common

    assert list(archers.steps) == [Tier.COMMON, Tier.IMPROVED, Tier.MASTERCRAFTED, Tier.LEGENDARY, Tier.HEIRLOOM]
    assert all(step[0].change.amount == 0.11 for step in archers.steps.values())  # +11% a step, stacking
    assert archers.total(Tier.HEIRLOOM)[0].change.amount == 0.55
    assert all(max(b.steps) is Tier.HEIRLOOM and all(b.steps.values()) for b in catalogue.ALL)


def test_capped_cuts_overshoot_into_an_extra():
    wheel = catalogue.by_id("hittites_4")  # Wheel research cost, written -25/-50/-100%: capped at -75%
    totals = {(e.stat or wheel.stat): e.change.amount for e in wheel.total(Tier.HEIRLOOM)}
    assert totals[Stat.COST] == -0.75
    assert totals[Stat.RESEARCH_TIME] == -0.3  # three tiers past the cap: -10% research time each
    time = catalogue.by_id("hittites_5")  # Wheel research time: capped at -100% (1 s), then cheaper research
    assert {e.stat for e in time.steps[Tier.HEIRLOOM]} == {Stat.COST}
    assert all(
        e.change.amount >= -0.75
        for b in catalogue.ALL
        for t in b.steps
        for e in b.total(t)
        if (e.stat or b.stat) in (Stat.COST, Stat.FOOD_COST, Stat.WOOD_COST) and e.change.mode.value == "%"
    )

    houses = catalogue.by_id("lac_viet_4")  # build speed, written +25/+50/+100%: capped at +90%
    totals = {(e.stat or houses.stat): e.change.amount for e in houses.total(Tier.HEIRLOOM)}
    assert totals[Stat.BUILD_SPEED] == 0.9
    assert totals[Stat.COST] == -0.15  # three tiers past the cap: 5% cheaper each


def test_civs_are_never_a_choice():
    from crucible.boons.model import OFFER_AXES, CivType

    assert Civ not in OFFER_AXES and CivType not in OFFER_AXES
