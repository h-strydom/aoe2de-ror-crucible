"""The waves of crucible_run (docs/arena.md): staged at a City State, then sent down the road.

A wave spawns as a row at the map edge and walks, in line formation, to a staging row inside the spawn base. Once it
is in position the "Send next wave" button on the Wonder comes on. At 5 minutes after the last send, or when the
player clicks, it marches out in formation, attack-moving straight down the road to the player's base, and the next
wave spawns and walks in. Waves alternate: the Capital's two lanes, then one lane from each of the other City States.

A lane is three rows of three tiles (marked by hand in the editor, 2026-11-17): where a row spawns, where it waits,
and where it attacks to.

A timer shows the time to the next send. A sent wave is defeated when every unit in it is dead; an objective counts
them to 9. Trigger text can't show a variable, but it can show a player's attribute (`<Relics Captured, 4>`), so XS
keeps the count in the Traders' relics, which nothing else uses (the text knows it as "Relics Captured"; "Gold Storage",
"Gold" and "Relics" stay as typed).

The XS (waves.xs) decides; triggers do: XS sets a variable, a looping trigger acts on it and sets it back to 0.
"""

from dataclasses import dataclass
from pathlib import Path

from crucible.datamod.shop import END_RUN, SEND_WAVE

RUNTIME = Path(__file__).with_name("waves.xs")
PLAYER, LEGION = 1, 3
VISIBLE = 0  # visibility state
CLUBMAN = 281
WAVE_UNIT = CLUBMAN  # what a wave is made of, for now
PER_LANE = 3  # for now: one row of Clubmen
SEND_TIME = 300  # seconds between sends
MOVE, ATTACK_MOVE, LINE_FORMATION = 1, 17, 18
MARGIN = 2  # tiles around a row that still count as on it
SPAWN_AREAS = ((76, 0, 142, 26), (0, 84, 20, 126), (200, 94, 219, 124))  # the City States, always in sight
WAVES = 9  # to defeat
TRADERS, RELICS = 4, 7  # where the defeated count is kept: the Traders' relics
COUNTER = f"<Relics Captured, {TRADERS}>"
TIMER = 0  # display timer slot

ORDER_VARIABLE = "crucible_wave_order"  # 1: spawn the Capital's wave; 3: send it, spawn the city states'; 4: back
BUTTON_VARIABLE = "crucible_wave_button"  # 1: button on, 2: off
WON_VARIABLE = "crucible_waves_won"  # 1 once the last wave is defeated

Tile = tuple[int, int]
Box = tuple[int, int, int, int]  # x1, y1, x2, y2, inclusive


@dataclass(frozen=True)
class Lane:
    name: str
    spawn: tuple[Tile, Tile, Tile]
    stage: tuple[Tile, Tile, Tile]
    target: tuple[Tile, Tile, Tile]

    @property
    def corridor(self) -> Box:
        """From the spawn row to the staging row: where its wave is until sent."""
        return _box(self.spawn + self.stage, MARGIN)

    @property
    def staged(self) -> Box:
        return _box(self.stage, MARGIN)


def _row(x: int | range, y: int | range) -> tuple[Tile, Tile, Tile]:
    xs = x if isinstance(x, range) else [x] * 3
    ys = y if isinstance(y, range) else [y] * 3

    return tuple(zip(xs, ys, strict=True))


def _box(tiles, margin: int = 0) -> Box:
    xs, ys = [x for x, _ in tiles], [y for _, y in tiles]

    return max(min(xs) - margin, 0), max(min(ys) - margin, 0), max(xs) + margin, max(ys) + margin


def _middle(tiles) -> list[int]:
    return list(tiles[1])


CAPITAL = (
    Lane("Capital west", _row(range(99, 102), 0), _row(range(99, 102), 13), _row(range(99, 102), 110)),
    Lane("Capital east", _row(range(117, 120), 0), _row(range(117, 120), 13), _row(range(117, 120), 110)),
)
CITY_STATES = (
    Lane("Western City State", _row(0, range(108, 111)), _row(13, range(108, 111)), _row(101, range(108, 111))),
    Lane("Eastern City State", _row(219, range(108, 111)), _row(206, range(108, 111)), _row(117, range(108, 111))),
)


def _walk_in(lane: Lane) -> list[dict]:
    spawn = _box(lane.spawn)
    create = [
        {"type": "create_object", "object_list_unit_id": CLUBMAN, "source_player": LEGION, "location": list(tile)}
        for tile in lane.spawn[:PER_LANE]
    ]

    return [
        *create,
        {  # the player sees the wave's units wherever they go (not the rest of the Legion)
            "type": "change_object_visibility",
            "source_player": LEGION,
            "target_player": PLAYER,
            "area": list(spawn),
            "visibility_state": VISIBLE,
        },
        {"type": "task_object", "source_player": LEGION, "area": list(spawn), "action_type": LINE_FORMATION},
        {
            "type": "task_object",
            "source_player": LEGION,
            "area": list(spawn),
            "action_type": MOVE,
            "location": _middle(lane.stage),
            "issue_group_command": 1,
        },
    ]


def _send(lane: Lane) -> list[dict]:
    return [
        {"type": "task_object", "source_player": LEGION, "area": list(lane.corridor), "action_type": LINE_FORMATION},
        {
            "type": "task_object",
            "source_player": LEGION,
            "area": list(lane.corridor),
            "action_type": ATTACK_MOVE,
            "location": _middle(lane.target),
            "issue_group_command": 1,
        },
    ]


def _on(variable: str, value: int, name: str, effects: list[dict]) -> dict:
    return {
        "name": name,
        "conditions": [{"type": "variable_value", "variable": variable, "comparison": "EQUAL", "quantity": value}],
        "effects": [*effects, {"type": "change_variable", "variable": variable, "operation": "SET", "quantity": 0}],
        "looping": True,
    }


def _button(tech: int, on: bool) -> dict:
    return {"type": "enable_disable_technology", "source_player": 1, "technology": tech, "enabled": int(on)}


def _timer() -> list[dict]:
    return [
        {"type": "clear_timer", "timer": TIMER},
        {
            "type": "display_timer",
            "timer": TIMER,
            "display_time": SEND_TIME,
            "time_unit": "SECONDS",
            "message": "Next wave: %d",
        },
    ]


def _objective(ctx) -> None:
    text = f"Defeat {WAVES} waves ({COUNTER}/{WAVES})"
    ctx.trigger(
        "Waves defeated",
        [
            {
                "type": "accumulate_attribute",
                "source_player": TRADERS,
                "attribute": RELICS,
                "quantity": WAVES,
            }
        ],
        [],
        display_as_objective=True,
        display_on_screen=True,
        description=text,
        short_description=text,
    )



def _triggers(ctx, tech: int) -> None:
    ctx.var(ORDER_VARIABLE)
    ctx.var(BUTTON_VARIABLE)
    capital = [effect for lane in CAPITAL for effect in _walk_in(lane)]
    city_states = [effect for lane in CITY_STATES for effect in _walk_in(lane)]

    ctx.trigger("Wave: no button at start", [], [_button(tech, on=False), *_timer()[1:]])
    _objective(ctx)
    ctx.triggers(
        _on(BUTTON_VARIABLE, 1, "Wave: button on", [_button(tech, on=True)]),
        _on(BUTTON_VARIABLE, 2, "Wave: button off", [_button(tech, on=False)]),
        _on(ORDER_VARIABLE, 1, "Wave: Capital walks in", capital),
        _on(
            ORDER_VARIABLE,
            3,
            "Wave: Capital sent, city states walk in",
            [*(e for lane in CAPITAL for e in _send(lane)), *city_states, *_timer()],
        ),
        _on(
            ORDER_VARIABLE,
            4,
            "Wave: city states sent, Capital walks in",
            [*(e for lane in CITY_STATES for e in _send(lane)), *capital, *_timer()],
        ),
    )


def _win(ctx, end_tech: int, player: int = 1) -> None:
    """When the last wave is defeated: a choice to win now or fight on, and an "End the run" button on the Wonder
    from then on."""
    ctx.var(WON_VARIABLE)
    decision = ctx.next_decision_id()
    end = {"type": "enable_disable_technology", "source_player": player, "technology": end_tech}
    victory = {"type": "declare_victory", "source_player": player, "enabled": True}
    ctx.trigger("Win: no End the run button yet", [], [end | {"enabled": 0}])
    ctx.triggers(
        {
            "name": "Win: waves defeated",
            "conditions": [{"type": "variable_value", "variable": WON_VARIABLE, "comparison": "EQUAL", "quantity": 1}],
            "effects": [
                end | {"enabled": 1},
                {
                    "type": "create_decision",
                    "decision_id": decision,
                    "message": f"All {WAVES} waves are defeated. End the run now, or fight on and end it later with "
                    "End the run on the Wonder?",
                    "message_option1": "Claim victory",
                    "message_option2": "Keep fighting",
                },
            ],
        },
        {
            "name": "Win: claim victory",
            "conditions": [{"type": "decision_triggered", "decision_id": decision, "decision_option": 1}],
            "effects": [victory],
        },
        {
            "name": "Win: End the run",
            "conditions": [{"type": "research_technology", "source_player": player, "technology": end_tech}],
            "effects": [victory],
        },
    )


def _variable_id(ctx, name: str) -> int:
    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def _boxes(name: str, lanes: tuple[Lane, Lane], which: str) -> str:
    calls = " || ".join(f"crucibleWaveIn(pos, {', '.join(map(str, getattr(lane, which)))})" for lane in lanes)

    return f"bool {name}(vector pos = cInvalidVector) {{\n    return ({calls});\n}}\n"


def xs(ctx, tech: int) -> str:
    data = "\n".join(
        [
            "// ---- crucible run: waves (data) ----",
            f"const int cCrucibleWaveLegion = {LEGION};",
            f"const int cCrucibleWaveSendTime = {SEND_TIME};",
            f"const int cCrucibleWaveButton = {tech};",
            f"const int cCrucibleWaveOrderVariable = {_variable_id(ctx, ORDER_VARIABLE)};",
            f"const int cCrucibleWaveButtonVariable = {_variable_id(ctx, BUTTON_VARIABLE)};",
            f"const int cCrucibleWaveUnit = {WAVE_UNIT};",
            f"const int cCrucibleWaves = {WAVES};",
            f"const int cCrucibleWaveCounterPlayer = {TRADERS};",
            f"const int cCrucibleWaveCounterRelics = {RELICS};",
            f"const int cCrucibleWaveWonVariable = {_variable_id(ctx, WON_VARIABLE)};",
            "bool crucibleWaveIn(vector pos = cInvalidVector, int x1 = 0, int y1 = 0, int x2 = 0, int y2 = 0) {",
            "    float x = xsVectorGetX(pos);",
            "    float y = xsVectorGetY(pos);",
            "    return ((x >= x1) && (x < x2 + 1) && (y >= y1) && (y < y2 + 1));",
            "}",
            _boxes("crucibleWaveCapitalCorridor", CAPITAL, "corridor"),
            _boxes("crucibleWaveCapitalStaged", CAPITAL, "staged"),
            _boxes("crucibleWaveCityStatesCorridor", CITY_STATES, "corridor"),
            _boxes("crucibleWaveCityStatesStaged", CITY_STATES, "staged"),
        ]
    )

    return data + "\n" + RUNTIME.read_text(encoding="utf-8")


def add(ctx, techs: dict[str, int]) -> None:
    tech = techs[SEND_WAVE]
    _triggers(ctx, tech)
    _win(ctx, techs[END_RUN])
    ctx.xs(xs(ctx, tech))
