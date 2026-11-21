"""The waves of crucible_run (docs/arena.md, docs/waves.md): staged at a City State, then sent down the road.

A wave spawns at the map edge and walks, in line formation, to a staging row inside the spawn base. Once it is in
position the "Send next wave" button on the Wonder comes on. At 5 minutes after the last send, or when the player
clicks, it marches out in formation, attack-moving straight down the road to the player's base, and the next wave
spawns and walks in. A sent unit standing idle (no target, not moving: the road's end, or a tower it took down) is
sent on to the Wonder. Wave 0 comes at once and is sent as soon as it's staged; then waves alternate: the Capital's two
lanes, then one lane from each of the other City States; wave 9 is all four.

What a wave brings is in wave_table: the XS reads the difficulty (xsGetDifficulty), rolls each lane's archetype and
spawns each group with xsCreateUnit, keeping the ids it gets so it knows when a wave is defeated.

A lane is three rows of three tiles (marked by hand in the editor, 2026-11-17): where a row spawns, where it waits,
and where it attacks to.

A timer shows the time to the next send. A sent wave is defeated when every unit in it is dead; an objective counts
them to 10. Trigger text can't show a variable, but it can show a player's attribute (`<Relics Captured, 4>`), so XS
keeps the count in the Traders' relics, which nothing else uses (the text knows it as "Relics Captured"; "Gold Storage",
"Gold" and "Relics" stay as typed).

The XS (waves.xs) decides; triggers do: XS sets a variable, a looping trigger acts on it and sets it back to 0.
"""

from dataclasses import dataclass
from pathlib import Path

from crucible.datamod.shop import SEND_WAVE
from crucible.scenarios import wave_table as table
from crucible.scenarios.wave_table import Age, Difficulty

RUNTIME = Path(__file__).with_name("waves.xs")
PLAYER, LEGION = 1, 3
WONDER = 276
AT_WONDER = 10  # tiles: an idle wave unit this near the Wonder attacks it, further off attack-moves to it
VISIBLE = 0  # visibility state
SEND_TIME = 300  # seconds between sends
MOVE, ATTACK_MOVE, LINE_FORMATION = 1, 17, 18
MARGIN = 2  # tiles around a row that still count as on it
DEPTH = 6  # tiles from the spawn row a group spawns in (rows of COLUMNS)
COLUMNS = 5
SPACING = 0.8  # tiles between units in a spawn row
ROW_SPACING = 0.9
CHOICES = 3  # unit choices per slot, padded with -1
SPAWN_AREAS = ((76, 0, 142, 26), (0, 84, 20, 126), (200, 94, 219, 124))  # the City States, always in sight
WAVES = table.WAVES  # to defeat
TRADERS, RELICS = 4, 7  # where the defeated count is kept: the Traders' relics
COUNTER = f"<Relics Captured, {TRADERS}>"
TIMER = 0  # display timer slot
NO_PRIESTS = 99  # an age never reached

WALK_VARIABLE = "crucible_wave_walk"  # lanes walking in: 1 the Capital's, 2 the City States', 3 all
SEND_VARIABLE = "crucible_wave_send"  # lanes sent, the same
TIMER_VARIABLE = "crucible_wave_timer"  # 1: restart the timer
BUTTON_VARIABLE = "crucible_wave_button"  # 1: button on, 2: off
WON_VARIABLE = "crucible_waves_won"  # 1: the last wave is defeated (asks whether to claim victory)

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

    @property
    def direction(self) -> Tile:
        """One step from the spawn row towards the staging row."""
        (sx, sy), (tx, ty) = self.spawn[1], self.stage[1]

        return (tx > sx) - (tx < sx), (ty > sy) - (ty < sy)

    @property
    def spawned(self) -> Box:
        """Where its groups spawn: DEPTH rows from the spawn row inwards."""
        dx, dy = self.direction
        inner = tuple((x + dx * DEPTH, y + dy * DEPTH) for x, y in self.spawn)

        return _box(self.spawn + inner, MARGIN)


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
LANES = CAPITAL + CITY_STATES
SETS = {1: ("Capital", CAPITAL), 2: ("City States", CITY_STATES), 3: ("all lanes", LANES)}


def _walk_in(lane: Lane) -> list[dict]:
    area = list(lane.spawned)

    return [
        {  # the player sees the wave's units wherever they go (not the rest of the Legion)
            "type": "change_object_visibility",
            "source_player": LEGION,
            "target_player": PLAYER,
            "area": area,
            "visibility_state": VISIBLE,
        },
        {"type": "task_object", "source_player": LEGION, "area": area, "action_type": LINE_FORMATION},
        {
            "type": "task_object",
            "source_player": LEGION,
            "area": area,
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
    for variable in (WALK_VARIABLE, SEND_VARIABLE, TIMER_VARIABLE, BUTTON_VARIABLE):
        ctx.var(variable)

    ctx.trigger("Wave: no button at start", [], [_button(tech, on=False), *_timer()[1:]])
    _objective(ctx)
    ctx.triggers(
        _on(BUTTON_VARIABLE, 1, "Wave: button on", [_button(tech, on=True)]),
        _on(BUTTON_VARIABLE, 2, "Wave: button off", [_button(tech, on=False)]),
        _on(TIMER_VARIABLE, 1, "Wave: timer", _timer()),
        *(
            _on(SEND_VARIABLE, value, f"Wave: {label} sent", [e for lane in lanes for e in _send(lane)])
            for value, (label, lanes) in SETS.items()
        ),
        *(
            _on(WALK_VARIABLE, value, f"Wave: {label} walk in", [e for lane in lanes for e in _walk_in(lane)])
            for value, (label, lanes) in SETS.items()
        ),
    )


def _win(ctx, player: int = 1) -> None:
    """When the last wave is defeated: a Claim victory choice, its only button, asked once. It stays up until clicked,
    so the player fights on and claims victory whenever they like. (Asked again after every wave by a looping
    trigger, it never showed.)"""
    ctx.var(WON_VARIABLE)
    decision = ctx.next_decision_id()
    ctx.triggers(
        {
            "name": "Win: claim victory or fight on",
            "conditions": [{"type": "variable_value", "variable": WON_VARIABLE, "comparison": "EQUAL", "quantity": 1}],
            "effects": [
                {
                    "type": "create_decision",
                    "decision_id": decision,
                    "message": f"{WAVES} waves are defeated. Claim victory whenever you like: until then, keep "
                    "fighting.",
                    "message_option1": "Claim victory",
                    "message_option2": "",
                },
            ],
        },
        {
            "name": "Win: claim victory",
            "conditions": [{"type": "decision_triggered", "decision_id": decision, "decision_option": 1}],
            "effects": [{"type": "declare_victory", "source_player": player, "enabled": True}],
        },
    )


def _variable_id(ctx, name: str) -> int:
    return next(v.variable_id for v in ctx.scenario.trigger_manager.variables if v.name == name)


def _staged() -> str:
    calls = " || ".join(f"crucibleWaveIn(pos, {', '.join(map(str, lane.staged))})" for lane in LANES)

    return f"bool crucibleWaveStagedAt(vector pos = cInvalidVector) {{\n    return ({calls});\n}}\n"


def _ints(name: str, values: list[int], default: int = -1) -> list[str]:
    lines = [f'    {name} = xsArrayCreateInt({len(values)}, {default}, "{name}");']

    return lines + [f"    xsArraySetInt({name}, {i}, {v});" for i, v in enumerate(values) if v != default]


def _floats(name: str, values: list[float]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateFloat({len(values)}, 0.0, "{name}");']

    return lines + [f"    xsArraySetFloat({name}, {i}, {float(v)});" for i, v in enumerate(values) if v]


def _strings(name: str, values: list[str]) -> list[str]:
    lines = [f'    {name} = xsArrayCreateString({len(values)}, "", "{name}");']

    return lines + [f'    xsArraySetString({name}, {i}, "{v}");' for i, v in enumerate(values)]


def _choices(names: tuple[str, ...]) -> list[int]:
    assert len(names) <= CHOICES, names

    return [table.unit_id(n) for n in names] + [-1] * (CHOICES - len(names))


def data() -> list[str]:
    """The tables as XS arrays, declared and filled by crucibleWaveData(). Indexes: a wave's numbers at
    difficulty * cCrucibleWaves + wave; a unit choice at ((archetype * cCrucibleWaveAges + age) * 2 + slot) *
    cCrucibleWaveChoices + n, slot 0 main, 1 other; a siege choice at age * cCrucibleWaveChoices + n."""
    difficulties, ages = list(Difficulty), list(Age)
    keys = [(d, w) for d in difficulties for w in range(WAVES)]
    groups = [table.group(d, w) for d, w in keys]
    units = [
        unit
        for archetype in table.ARCHETYPES
        for age in ages
        for slot in table.choices(archetype, age)
        for unit in _choices(slot)
    ]
    siege = [unit for age in ages for unit in _choices(table.SIEGE.get(age, ()))]
    game_difficulties = [int(table.GAME_DIFFICULTY.get(g, table.FALLBACK)) for g in range(5)]
    arrays = [
        _ints("crucibleWaveMain", [g.main for g in groups]),
        _ints("crucibleWaveOther", [g.other for g in groups]),
        _ints("crucibleWaveSiege", [g.siege for g in groups]),
        _ints("crucibleWaveAge", [int(table.legion_age(d, w)) for d, w in keys]),
        _ints("crucibleWaveUnit", units),
        _ints("crucibleWaveSiegeUnit", siege),
        _ints("crucibleWavePriestAge", [int(table.PRIESTS.get(d, NO_PRIESTS)) for d in difficulties]),
        _ints("crucibleWaveDifficultyOf", game_difficulties),  # by xsGetDifficulty (0 to 4)
        _strings("crucibleWaveArchetypeName", [a.name for a in table.ARCHETYPES]),
        _strings("crucibleWaveAgeName", [a.title for a in ages]),
        _strings("crucibleWaveLaneName", [lane.name for lane in LANES]),
        _floats("crucibleWaveSpawnX", [lane.spawn[1][0] + 0.5 for lane in LANES]),
        _floats("crucibleWaveSpawnY", [lane.spawn[1][1] + 0.5 for lane in LANES]),
        _floats("crucibleWaveDirX", [lane.direction[0] for lane in LANES]),
        _floats("crucibleWaveDirY", [lane.direction[1] for lane in LANES]),
    ]
    names = [lines[0].split(" = ")[0].strip() for lines in arrays]

    return [
        *(f"int {name} = -1;" for name in names),
        "void crucibleWaveData() {",
        *(line for lines in arrays for line in lines),
        "}",
    ]


def xs(ctx, tech: int) -> str:
    wonder = next(u for u in ctx.scenario.unit_manager.units[PLAYER] if u.unit_const == WONDER)
    lines = [
        "// ---- crucible run: waves (data) ----",
        f"const int cCrucibleWaveLegion = {LEGION};",
        f"const int cCrucibleWaveSendTime = {SEND_TIME};",
        f"const int cCrucibleWaveButton = {tech};",
        f"const int cCrucibleWaveWalkVariable = {_variable_id(ctx, WALK_VARIABLE)};",
        f"const int cCrucibleWaveSendVariable = {_variable_id(ctx, SEND_VARIABLE)};",
        f"const int cCrucibleWaveTimerVariable = {_variable_id(ctx, TIMER_VARIABLE)};",
        f"const int cCrucibleWaveButtonVariable = {_variable_id(ctx, BUTTON_VARIABLE)};",
        f"const int cCrucibleWaves = {WAVES};",
        f"const int cCrucibleWaveAllLanesFrom = {table.ALL_LANES_FROM};",
        f"const int cCrucibleWaveLanes = {len(LANES)};",
        f"const int cCrucibleWaveCapitalLanes = {len(CAPITAL)};",
        f"const int cCrucibleWaveArchetypes = {len(table.ARCHETYPES)};",
        f"const int cCrucibleWaveAges = {len(Age)};",
        f"const int cCrucibleWaveChoices = {CHOICES};",
        f"const int cCrucibleWavePriest = {table.unit_id('priest')};",
        f"const int cCrucibleWaveColumns = {COLUMNS};",
        f"const float cCrucibleWaveSpacing = {SPACING};",
        f"const float cCrucibleWaveRowSpacing = {ROW_SPACING};",
        f"const int cCrucibleWaveCounterPlayer = {TRADERS};",
        f"const int cCrucibleWaveCounterRelics = {RELICS};",
        f"const int cCrucibleWaveWonVariable = {_variable_id(ctx, WON_VARIABLE)};",
        f"const int cCrucibleWaveWonder = {wonder.reference_id};",
        f"vector cCrucibleWaveWonderAt = vector({wonder.x}, {wonder.y}, 0.0);",
        f"const float cCrucibleWaveAtWonder = {float(AT_WONDER * AT_WONDER)};",
        *data(),
        "bool crucibleWaveIn(vector pos = cInvalidVector, int x1 = 0, int y1 = 0, int x2 = 0, int y2 = 0) {",
        "    float x = xsVectorGetX(pos);",
        "    float y = xsVectorGetY(pos);",
        "    return ((x >= x1) && (x < x2 + 1) && (y >= y1) && (y < y2 + 1));",
        "}",
        _staged(),
    ]

    return "\n".join(lines) + "\n" + RUNTIME.read_text(encoding="utf-8")


def add(ctx, techs: dict[str, int]) -> None:
    tech = techs[SEND_WAVE]
    _triggers(ctx, tech)
    _win(ctx)
    ctx.xs(xs(ctx, tech))
