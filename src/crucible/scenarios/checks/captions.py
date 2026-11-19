"""Captions: can the text over a building break into lines, and show a live value like an objective does
(`<Relics Captured, 4>` works there)? If so, the hub's counts can go over its buildings, kept live by XS.

A row of houses, each captioned differently at the start by Change Object Caption (A to F); G has its caption in the
map instead; H and I are flags (Gaia's with the caption in the map, the player's by trigger), to tell why the hub's
flags showed nothing. XS raises the player's relics and food by 1 every 5 seconds (relics from 0, food from 1000):
a live tag should count up with them. F has its caption set again every 5 seconds, in case a tag is only read when
it's set.
"""

NAME = "captions"
BOONS = ()
BUTTONS = {}
PLAYER, GAIA = 1, 0
INTERVAL = 5  # seconds
CAPTIONS = {  # label -> caption set by trigger
    "A": "(!)\n4/10 villagers\n0/7 houses",  # a real line break
    "B": "(!)\\n4/10 villagers",  # a written backslash-n
    "C": "Relics <Relics Captured, 1>",
    "D": "Food <Food Storage, 1>",
    "E": "Food <Food, 1>",
    "F": "Again <Relics Captured, 1>",
}
IN_MAP = "G line 1\nG line 2"


def setup(o, ctx, techs: dict[str, int], top: int) -> str:
    from crucible.scenarios.check import add_unit  # check imports the tests

    s = o.scenario
    houses = {label: add_unit(s, "house", 4 + 4 * k, top + 2) for k, label in enumerate(CAPTIONS)}
    g = add_unit(s, "house", 4 + 4 * len(CAPTIONS), top + 2)
    next(u for u in s.unit_manager.units[PLAYER] if u.reference_id == g).caption_string = IN_MAP
    h = add_unit(s, "flag_a", 4, top + 7, player=GAIA)
    next(u for u in s.unit_manager.units[GAIA] if u.reference_id == h).caption_string = "H: Gaia flag, in the map"
    i = add_unit(s, "flag_a", 8, top + 7)

    def caption(ref: int, text: str, player: int = PLAYER) -> dict:
        return {"type": "change_object_caption", "source_player": player, "selected_object_ids": [ref], "message": text}

    ctx.trigger(
        "Captions: set",
        [],
        [*(caption(houses[label], text) for label, text in CAPTIONS.items()), caption(i, "I: player's flag, trigger")],
    )
    ctx.triggers(
        {
            "name": "Captions: F again",
            "conditions": [{"type": "timer", "timer": INTERVAL}],
            "effects": [caption(houses["F"], CAPTIONS["F"])],
            "looping": True,
        }
    )
    ctx.xs(
        f"""// ---- check: captions ----
int checkCaptionsCount = 0;

rule checkCaptions
    active
    minInterval {INTERVAL}
{{
    xsSetPlayerAttribute({PLAYER}, 7, checkCaptionsCount);  // relics
    xsSetPlayerAttribute({PLAYER}, 0, 1000 + checkCaptionsCount);  // food
    checkCaptionsCount++;
}}
"""
    )

    lines = "\n".join(f"{label}: {text!r}" for label, text in CAPTIONS.items())

    return f"""CAPTIONS. Houses left to right, captioned at the start:
{lines}
G: two lines written in the map. H: a Gaia flag, caption in the map. I: your flag, caption by trigger.
Relics and food rise by 1 every 5 s. Look at each: does A or B show lines? Does C, D, E or F show a number, and does
it count up? Do H and I show text?"""
