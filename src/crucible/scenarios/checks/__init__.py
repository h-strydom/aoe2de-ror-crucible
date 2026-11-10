"""The tests crucible_check can hold, by name. Each module has NAME, BOONS (ids the data mod needs), BUTTONS (boons
on the Wonder from the start) and setup(s, ctx, techs, top) returning its briefing paragraph.

Standing rule: delete a test's module once it's confirmed in game.
"""

from crucible.scenarios.checks import compiled

TESTS = {module.NAME: module for module in (compiled,)}
