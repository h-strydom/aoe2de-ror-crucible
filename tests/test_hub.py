from aoe2ed.session import SESSIONS

from crucible import meta
from crucible.scenarios import campaign, hub, run


def test_hub_has_a_trigger_per_level(tmp_path, techs):
    o = SESSIONS.open(hub.build(tmp_path, techs))

    try:
        s = o.scenario
        units = s.unit_manager.units
        assert {u.unit_const for u in units[hub.PLAYER]} == {meta.TOWN_CENTER, hub.WONDER}
        assert len([u for u in units[hub.PURPLE] if u.unit_const in hub.VILLAGERS]) == 4  # at the berries
        assert s.player_manager.active_players == 3  # no empty players: they'd get a starting town
        players = s.player_manager.players
        assert all(players[p].personality == "Immobile AI" for p in (2, 3))  # "None AI" explores
        assert s.sections["FileHeader"].unknown_numbers == [11]

        names = {t.name for t in s.trigger_manager.triggers}
        for upgrade in meta.UPGRADES:
            assert {f"Hub: {upgrade.title} bought", f"Hub: {upgrade.title} sold out"} <= names
        assert {"Hub: Villager 6", "Hub: House 7", "Hub: Clubmen 2", "Hub: begin the Crucible", "No data mod"} <= names
    finally:
        SESSIONS.close(o.handle)


def test_campaign_plays_the_hub_then_the_run(tmp_path, techs):
    path = campaign.build(tmp_path, hub.build(tmp_path, techs), run.build(tmp_path, techs))
    from aoe2ed.campaign import Campaign

    built = Campaign.read(path)
    assert built.name == campaign.NAME
    assert [s.filename for s in built.scenarios] == ["crucible_hub.aoe2scenario", "crucible_run.aoe2scenario"]
    assert built.data_sets() == [11]
