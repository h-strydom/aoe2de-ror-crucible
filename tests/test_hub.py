from aoe2ed import xs
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
        assert s.player_manager.active_players == 4  # no empty players: they'd get a starting town
        players = s.player_manager.players
        assert all(players[p].personality == "Immobile AI" for p in (2, 3, 4))  # "None AI" explores
        assert s.sections["FileHeader"].unknown_numbers == [11]

        names = {t.name for t in s.trigger_manager.triggers}
        for upgrade in meta.UPGRADES:
            assert {f"Hub: {upgrade.title} bought", f"Hub: {upgrade.title} not on offer"} <= names
            assert f"Hub: {upgrade.title} on offer at {upgrade.levels - 1}" in names
        assert {
            "Hub: Villager 6",
            "Hub: House 7",
            "Hub: Axemen upgrade 1",
            "Hub: Axemen 1",
            "Hub: Bowmen 2",
            "Hub: begin the Crucible",
        } <= names
        assert {"No data mod", "Hub: reset progress", "Hub: Tier 2", "Hub: Tier 3", "Hub: wonder on offer"} <= names
        assert {"Hub: town_center on offer", "Hub: granary on offer"} <= names

        messages = [e.message for t in s.trigger_manager.triggers for e in t.effects if e.message]
        code = "\n".join(m for m in messages if "{" in m)
        assert "crucibleHub" in code
        result = xs.check(code)
        assert result["ok"], result["diagnostics"]
    finally:
        SESSIONS.close(o.handle)


def test_campaign_plays_the_hub_then_the_run(tmp_path, techs):
    path = campaign.build(tmp_path, hub.build(tmp_path, techs), run.build(tmp_path, techs))
    from aoe2ed.campaign import Campaign

    built = Campaign.read(path)
    assert built.name == campaign.NAME
    assert [s.filename for s in built.scenarios] == ["crucible_hub.aoe2scenario", "crucible_run.aoe2scenario"]
    assert built.data_sets() == [11]
