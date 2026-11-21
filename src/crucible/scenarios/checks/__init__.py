"""The tests crucible_check can hold, by name. Each module has NAME, BOONS (ids the data mod needs), BUTTONS (boons on
the Wonder from the start) and setup(session, ctx, techs, top) returning its briefing paragraph (session.scenario, and
session.handle for aoe2ed's tools); optionally datamod(mod), adding to the data mod, and PLAYERS and SIZE, how many
players and how big a map it needs.

Standing rule: delete a test's module once it's confirmed in game.
"""

from crucible.scenarios.checks import boons

TESTS = {module.NAME: module for module in (boons,)}
