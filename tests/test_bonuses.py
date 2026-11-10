import random

import pytest

from crucible.bonuses import catalogue
from crucible.bonuses.civs import CIVS
from crucible.bonuses.compile import commands
from crucible.bonuses.model import RARITY_COSTS, Civ, Game, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct, plural


def test_every_civ_is_covered():
    assert {m.civ for m in catalogue.ALL} == set(Civ)
    assert len(CIVS) == len(Civ)


def test_ids_are_unique():
    ids = [m.id for m in catalogue.ALL]
    assert len(ids) == len(set(ids))


def test_names_follow_the_civ():
    for civ in CIVS:
        civs = {m.civ for m in civ.MODIFIERS}
        assert len(civs) == 1
        title = civs.pop().value.title()
        assert [m.name for m in civ.MODIFIERS] == [f"{title} {k}" for k in range(1, len(civ.MODIFIERS) + 1)]


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (Tag.CAVALRY, Civ.GREEKS),  # "a Cavalry upgrade or a Greek upgrade"
        (Tag.HOPLITE, Tag.SIEGE_WORKSHOP),
        (Tag.STONE, Tag.ARCHERY_RANGE),
        (Stat.HP, Tag.STABLE),
        (Tag.TEAM, Tag.TECHNOLOGY),
        (Tag.TECHNOLOGY, Tag.UNIT),
        (Group.ARCHERS, Tag.ECONOMY),
    ],
)
def test_example_choices_have_upgrades_to_offer(left, right):
    for category in (left, right):
        offered = catalogue.pick(4, random.Random(7), category, exclude=[Tag.DRAWBACK])
        assert offered, category
        assert all(m.in_category(category) and Tag.DRAWBACK not in m.tags for m in offered)
        assert len(set(offered)) == len(offered)  # no repeats


def test_drawbacks_are_tagged():
    assert {m.id for m in catalogue.query(Tag.DRAWBACK)} == {"shang_2", "palmyrans_1"}


def test_categories_combine():
    assert {m.id for m in catalogue.query(Tag.CAVALRY, Stat.HP)} == {"carthaginians_4"}


def test_descriptions_come_from_the_definition():
    by = catalogue.by_id
    assert by("carthaginians_1").description == "+50 all resources"
    assert by("carthaginians_2").description == "Hoplites, Phalangites, Centurions +25% HP"
    assert by("carthaginians_7").description == "Nobility -100% cost"
    assert by("carthaginians_8").description == "Academies +20% work rate"  # a team bonus, but no "Team:" text
    assert by("hittites_1").description == "Archers +1 attack"
    assert by("yamato_2").description == "Cavalry, Horse Archers, Heavy Horse Archers -15% cost"
    bigger = by("carthaginians_1").model_copy(update={"change": flat(500)})
    assert bigger.description == "+500 all resources"  # change the number, the text follows


def test_plurals():
    names = ("academy", "fire_galley", "war_elephant", "camel_rider", "axeman", "heavy_cavalry")
    assert [plural(t) for t in names] == [
        "Academies",
        "Fire Galleys",
        "War Elephants",
        "Camel Riders",
        "Axemen",
        "Heavy Cavalry",
    ]


def test_subject_shortens_long_lists():
    assert catalogue.by_id("choson_6").description == "Storage Pit technologies -40% cost"


def test_compile_hp():
    assert commands(catalogue.by_id("carthaginians_4")) == [(5, 329, -1, 0, 1.15)]


def test_compile_start_resources():
    assert commands(catalogue.by_id("carthaginians_1")) == [(1, r, 1, -1, 50) for r in range(4)]


def test_not_yet_compiled_says_so():
    with pytest.raises(NotImplementedError, match="doesn't compile yet"):
        commands(catalogue.by_id("hittites_1"))  # a group
    with pytest.raises(NotImplementedError, match="doesn't compile yet"):
        commands(catalogue.by_id("carthaginians_5"))  # attack


def test_civs_know_their_game():
    assert Civ.CARTHAGINIANS.game is Game.ROR
    assert all(m.civ.game is Game.ROR for m in catalogue.ALL)


def test_typos_are_caught():
    base = {
        "change": pct(0.1),
        "stat": Stat.HP,
        "civ": Civ.GREEKS,
        "name": "Greeks 99",
        "icon": Icon.ACADEMY,
        "rarity": Rarity.COMMON,
    }
    with pytest.raises(ValueError, match="unknown ror names"):
        Modifier(**base, targets=("hoplight",), tags=())
    with pytest.raises(ValueError, match="unknown ror names"):
        Modifier(**base, techs=("nobilty",), tags=())
    with pytest.raises(ValueError):
        Modifier(**base, tags=("stabel",))
    with pytest.raises(ValueError):
        Modifier(**base, groups=("Archerz",), tags=())
    with pytest.raises(TypeError):
        Modifier(pct(0.1), Stat.HP, (), (), Civ.GREEKS, "Positional")  # keyword arguments only


def test_every_boon_has_a_rarity_and_its_cost():
    assert {m.rarity for m in catalogue.ALL} == set(Rarity)
    assert all(m.cost == RARITY_COSTS[m.rarity] for m in catalogue.ALL)


def test_rarity_rules():
    by = catalogue.by_id
    assert all(m.rarity is Rarity.COMMON for m in catalogue.query(Tag.SHIP))  # little water on the maps
    assert by("assyrians_2").rarity is Rarity.LEGENDARY  # an age-scaled bonus, Iron Age value
    assert by("hittites_1").rarity is Rarity.LEGENDARY  # all archers
    assert by("carthaginians_4").rarity is Rarity.COMMON  # only camels
    assert by("egyptians_3").rarity is Rarity.COMMON  # +2 carry
    assert by("carthaginians_7").rarity is Rarity.COMMON  # a free tech worth 295
    assert by("yamato_4").rarity is Rarity.LEGENDARY  # all stable and range upgrades
