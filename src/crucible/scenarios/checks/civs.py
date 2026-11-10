"""Test: the five bonus-less civs. The Greek player jumps to the Iron Age (free) with a building of each kind, to see
techs Greeks normally lack and full prices; players 2-5 (no AI) show the other architecture styles."""

from aoe2ed import tables
from aoe2ed.tools.world import player_set

from crucible.datamod.civs import PLAYER, SCENARIO_CIVS, Style

NAME = "civs"
BOONS: tuple[str, ...] = ()
BUTTONS: dict[str, int] = {}

AGES = ("TOOL_AGE", "BRONZE_AGE", "IRON_AGE")
PLAYER_BUILDINGS = ("barracks", "archery_range", "stable", "academy", "siege_workshop", "temple")
LOOKS = ("town_center", "house", "barracks", "temple", "villager", "villager")  # for each other style


def setup(session, ctx, techs: dict[str, int], top: int) -> str:
    from crucible.scenarios.check import SIZE, add_unit

    s = session.scenario
    others = [style for style in Style if style != PLAYER]
    s.player_manager.active_players = 1 + len(others)

    for player, style in enumerate(others, start=2):
        player_set(
            session.handle,
            player,
            {"civilization": SCENARIO_CIVS[style], "human": False, "ai": "none", "starting_age": "DARK"},
        )

        for k, unit in enumerate(LOOKS):
            add_unit(s, unit, 6 + 6 * k, SIZE - 30 + 6 * (player - 2), player=player)

    for k, unit in enumerate(PLAYER_BUILDINGS):
        add_unit(s, unit, 6 + 6 * k, top + 6)

    ages = "\n".join(f"    xsResearchTechnology({tables.tech_id(age, 'ror')}, true, false, 1);" for age in AGES)
    ctx.xs(f"""// ---- crucible check: civs ----
rule crucibleCivsAges
    active
    minInterval 1
{{
{ages}
    xsChatData("Iron Age");
    xsDisableSelf();
}}
""")

    return (
        "CIVS: you're Greek with no bonuses and every tech, jumped to the Iron Age. Greeks normally lack these, so "
        "they should now be there: Chariot and War Elephant (Stable), Chariot Archer, Horse Archer, Elephant Archer "
        "and Improved Bow (Archery Range), Broad Sword (Barracks), Monotheism (Temple). A Hoplite at the Academy "
        "should cost the full 60 food, 40 gold (Greeks normally pay 20% less). Players 2-5 down the map are "
        "Egyptian, Babylonian, Shang and Roman, in their own styles."
    )
