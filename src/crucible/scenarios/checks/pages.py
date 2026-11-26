"""Check: command panel pages (2026-11-26). RoR's villager has two build pages, but its economic and military
buildings share button numbers (House and Barracks are both 1); what differs is the building's interface kind (2 for
the economic ones, 10 for the military ones). Does the page follow it? And does a building show buttons past 15 (the
panel holds 15) on a page of its own, as AoE2's builders take 21 to 35 for their second page?

- A test building (a copy of the Government Center, none of its own techs) with a tech on each of BUTTONS, each named
  for its button.
- Test houses on the villager's panel: copies of the House, each with an interface kind and button (HOUSES), named
  for both.
"""

from crucible.bonuses.model import Icon
from crucible.datamod.icons import icon_id
from crucible.datamod.mod import DataMod

NAME = "pages"
BOONS: tuple[str, ...] = ()
BUTTONS: dict[str, int] = {}
BUILDING_KEY = "page_test_building"
BUILDING_SOURCE = 209  # the Government Center
HOUSE_SOURCE, BUILDER = 70, 118
TECH_BUTTONS = (1, 5, 15, 16, 20, 21, 25, 30, 35, 36, 40)
HOUSES = ((2, 14), (10, 14), (2, 21), (10, 21), (2, 30), (10, 35))  # (interface kind, button)
VILLAGER = 83  # a male villager


def datamod(mod: DataMod) -> None:
    building = mod.copy_unit(BUILDING_SOURCE)
    mod.manifest[BUILDING_KEY] = building
    name = mod.strings.add("Page test building")

    for civ in mod.data.civs:
        if civ.units[building] is not None:
            civ.units[building].language_dll_name = name

    icon = icon_id(Icon.TECHNOLOGY, mod.data)

    for button in TECH_BUTTONS:
        title = f"Button {button}"
        mod.new_tech(
            f"Crucible page test {button}",
            effect=mod.new_effect(f"Crucible page test {button}", []),
            title=title,
            description=title,
            tooltip=f"Research <b>{title}<b>",
            icon=icon,
            location=building,
            button=button,
            research_time=30,
        )

    for kind, button in HOUSES:
        house = mod.copy_unit(HOUSE_SOURCE)
        title = f"House, kind {kind}, button {button}"
        name, creation = mod.strings.add(title), mod.strings.add(f"Build {title}")

        for civ in mod.data.civs:
            unit = civ.units[house]

            if unit is None:
                continue

            unit.enabled, unit.interface_kind = 1, kind
            unit.language_dll_name, unit.language_dll_creation = name, creation
            location = unit.creatable.train_locations[0]
            location.unit_id, location.button_id = BUILDER, button
            unit.creatable.train_locations = [location]


def setup(session, ctx, techs: dict[str, int], top: int) -> str:
    s = session.scenario
    s.unit_manager.add_unit(player=1, unit_const=techs[BUILDING_KEY], x=12.5, y=top + 5.5)
    s.unit_manager.add_unit(player=1, unit_const=VILLAGER, x=20.5, y=top + 5.5)
    shown = ", ".join(str(b) for b in TECH_BUTTONS)
    houses = "; ".join(f"kind {k}, button {b}" for k, b in HOUSES)

    return (
        f"Pages: the Page test building has a tech on buttons {shown}, each named for its button. Which show, on "
        f"which page, and is there a page arrow? The villager's build pages hold test houses ({houses}): which page "
        "does each show on, and do the ones past 15 show at all?"
    )
