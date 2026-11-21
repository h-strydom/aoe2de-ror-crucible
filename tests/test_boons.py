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
    assert boon.text(Tier.HEIRLOOM) == "+40% & +3 carry capacity"


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
