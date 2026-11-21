from aoe2ed import xs
from aoe2ed.session import SESSIONS

from crucible import meta
from crucible.scenarios import campaign, hub, run


def test_hub_has_a_trigger_per_level(tmp_path, techs):
    o = SESSIONS.open(hub.build(tmp_path, techs))

    try:
        s = o.scenario
        units = s.unit_manager.units
        mine = [u.unit_const for u in units[hub.PLAYER]]
        assert hub.WONDER in mine and techs[meta.place("town_center_1").copy_key] in mine  # tier 1's TC, as its copy
        assert len([u for u in units[hub.PLAYER] if u.unit_const in hub.VILLAGERS]) == meta.START_VILLAGERS
        assert len([u for u in units[hub.PLAYER] if u.unit_const == hub.HOUSE]) == meta.STARTING_HOUSES
        assert s.player_manager.active_players == 6
        players = s.player_manager.players
        assert all(players[p].personality == "Immobile AI" for p in meta.TIER_PLAYERS.values())
        assert s.sections["FileHeader"].unknown_numbers == [11]

        for place in meta.PLACES:  # every place is its own copy, so it shows only its own buttons
            if place.copy:
                assert any(u.unit_const == techs[place.copy_key] for u in units[place.player] + units[hub.PLAYER])

        names = {t.name for t in s.trigger_manager.triggers}
        for upgrade in meta.UPGRADES:
            assert {f"Hub: {upgrade.title} bought", f"Hub: {upgrade.title} not on offer"} <= names
            assert f"Hub: {upgrade.title} on offer at {upgrade.levels - 1}" in names
        assert {
            "Hub: Villager 6",
            "Hub: House 5",
            "Hub: Axemen upgrade 1",
            "Hub: Bowmen 2",
            "Hub: Cavalry 5",
            "Hub: save and win",
            "Hub: reset refunded",
            "Hub: the stockpile is the currency",
        } <= names
        assert {f"Hub: Tier {n}" for n in range(2, 6)} <= names
        assert {"Hub: town_center_1 affordable", "Hub: granary_2 on offer", "Hub: wonder affordable"} <= names

        bought = next(t for t in s.trigger_manager.triggers if t.name == "Hub: Villager bought")
        assert set(meta.CURRENCY) <= {e.message for e in bought.effects if e.message}  # the stockpile is banked

        messages = [e.message for t in s.trigger_manager.triggers for e in t.effects if e.message]
        code = "\n".join(m for m in messages if "{" in m)
        assert "crucibleHub" in code
        result = xs.check(code)
        assert result["ok"], result["diagnostics"]
    finally:
        SESSIONS.close(o.handle)


def test_upgrades_fit_their_places():
    for place in meta.PLACES:
        buttons = [u.button for u in meta.UPGRADES if u.place == place.key]
        assert len(buttons) == len(set(buttons)) and all(1 <= b <= 15 for b in buttons), place.key

    keys = {u.key for u in meta.UPGRADES}
    for upgrade in meta.UPGRADES:
        assert all(key in keys for key, _ in upgrade.requires), upgrade.key
        assert meta.tier_of(upgrade) >= meta.place(upgrade.place).tier, upgrade.key
        place = meta.place(upgrade.place)
        assert not place.opened_by or place.opened_by in keys, place.key


def test_campaign_plays_the_hub_then_the_run(tmp_path, techs):
    path = campaign.build(tmp_path, hub.build(tmp_path, techs), run.build(tmp_path, techs))
    from aoe2ed.campaign import Campaign

    built = Campaign.read(path)
    assert built.name == campaign.NAME
    assert [s.filename for s in built.scenarios] == ["crucible_hub.aoe2scenario", "crucible_run.aoe2scenario"]
    assert built.data_sets() == [11]
