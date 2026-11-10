"""The tests crucible_check can hold, by name. Each module has NAME, BOONS (ids the data mod needs), BUTTONS (boons
on the Wonder from the start) and setup(session, ctx, techs, top) returning its briefing
paragraph (session.scenario, and session.handle for aoe2ed's tools).

Standing rule: delete a test's module once it's confirmed in game.
"""

from crucible.scenarios.checks import civs

TESTS = {module.NAME: module for module in (civs,)}
