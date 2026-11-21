"""The waves of crucible_run (docs/arena.md, docs/evolving-waves.md): staged at a City State, then sent down the road.

A wave spawns at the map edge and walks, in line formation, to a staging row inside the spawn base. Once it is in
position the "Send next wave" button on the Wonder comes on. When the difficulty's time since the last send is up (5,
3 or 2 minutes), or when the player clicks, it marches out in formation, attack-moving straight down the road to the
player's base, and the next wave spawns and walks in. Wave 0 comes at once and is sent as soon as it's staged; then
waves alternate: the Capital's two lanes, then one lane from each of the other City States. They never end: the run
ends when the Wonder falls. A sent unit standing idle (no target, not moving: the road's end, or a tower it took
down) is sent on to the Wonder.

What a wave brings evolves (wave_table): each lane's army takes a step before it spawns; the XS reads the difficulty
(xsGetDifficulty), rolls each lane's archetype, steps and spawns each group with xsCreateUnit, keeping the ids it gets
so it knows when a wave is defeated. The Legion's ages and upgrades are researched by triggers, queued by the XS.

A lane is three rows of three tiles (marked by hand in the editor, 2026-11-17): where a row spawns, where it waits,
and where it attacks to.

A timer shows the time to the next send. A sent wave is defeated when every unit in it is dead; an objective counts
them. Trigger text can't show a variable, but it can show a player's attribute (`<Relics Captured, 4>`), so XS keeps
the count in the Traders' relics, which nothing else uses (the text knows it as "Relics Captured"; "Gold Storage",
"Gold" and "Relics" stay as typed).

The XS (waves.xs) decides; triggers do: XS sets a variable, a looping trigger acts on it and sets it back to 0.
"""

from dataclasses import dataclass
from pathlib import Path

from crucible.datamod.shop import SEND_WAVE
from crucible.scenarios import wave_table as table
from crucible.scenarios.wave_table import Age, Difficulty, Slot

RUNTIME = Path(__file__).with_name("waves.xs")
PLAYER, LEGION = 1, 3
WONDER = 276
AT_WONDER = 10  # tiles: an idle wave unit this near the Wonder attacks it, further off attack-moves to it
VISIBLE = 0  # visibility state
MOVE, ATTACK_MOVE, LINE_FORMATION = 1, 17, 18
MARGIN = 2  # tiles around a row that still count as on it
DEPTH = 6  # tiles from the spawn row a group spawns in (rows of COLUMNS)
COLUMNS = 7
SPACING = 0.8  # tiles between units in a spawn row
ROW_SPACING = 0.9
SIEGE_CHOICES = 3  # siege units per age, padded with -1
SPAWN_AREAS = ((76, 0, 142, 26), (0, 84, 20, 126), (200, 94, 219, 124))  # the City States, always in sight
TRADERS, RELICS = 4, 7  # where the defeated count is kept: the Traders' relics
COUNTER = f"<Relics Captured, {TRADERS}>"
NEVER = 1_000_000  # the objective's count: it never completes
TIMER = 0  # display timer slot
NO_AGE = 99  # an age never reached

WALK_VARIABLE = "crucible_wave_walk"  # lanes walking in: 1 the Capital's, 2 the City States'
SEND_VARIABLE = "crucible_wave_send"  # lanes sent, the same
TIMER_VARIABLE = "crucible_wave_timer"  # difficulty + 1: restart the timer at its time
BUTTON_VARIABLE = "crucible_wave_button"  # 1: button on, 2: off
TECH_VARIABLE = "crucible_legion_tech"  # a tech id: the Legion researches it

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
SETS = {1: ("Capital", CAPITAL), 2: ("City States", CITY_STATES)}


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


def _timer(seconds: int) -> list[dict]:
    return [
        {"type": "clear_timer", "timer": TIMER},
        {
            "type": "display_timer",
            "timer": TIMER,
            "display_time": seconds,
            "time_unit": "SECONDS",
            "message": "Next wave: %d",
        },
    ]


def _objective(ctx) -> None:
    text = f"Waves defeated: {COUNTER}"
    ctx.trigger(
        "Waves defeated",
        [{"type": "accumulate_attribute", "source_player": TRADERS, "attribute": RELICS, "quantity": NEVER}],
        [],
        display_as_objective=True,
        display_on_screen=True,
        description=text,
        short_description=text,
    )


def legion_techs() -> dict[int, str]:
    """Every tech the Legion may research: tech -> its name."""
    ages = {tech: age.title for age, tech in table.AGE_TECHS.items()}

    return ages | {u.tech: u.name for u in table.UPGRADES}


def _triggers(ctx, tech: int) -> None:
    for variable in (WALK_VARIABLE, SEND_VARIABLE, TIMER_VARIABLE, BUTTON_VARIABLE, TECH_VARIABLE):
        ctx.var(variable)

    ctx.trigger("Wave: no button at start", [], [_button(tech, on=False)])
    _objective(ctx)
    research = (
        _on(
            TECH_VARIABLE,
            tech_id,
            f"Legion: {name}",
            [
                {
                    "type": "research_technology",
                    "source_player": LEGION,
                    "technology": tech_id,
                    "force_research_technology": 1,
                }
            ],
        )
        for tech_id, name in legion_techs().items()
    )
    ctx.triggers(
        _on(BUTTON_VARIABLE, 1, "Wave: button on", [_button(tech, on=True)]),
        _on(BUTTON_VARIABLE, 2, "Wave: button off", [_button(tech, on=False)]),
        *(
            _on(TIMER_VARIABLE, d + 1, f"Wave: timer ({d.name.title()})", _timer(table.SEND_TIMES[d]))
            for d in Difficulty
        ),
        *(
            _on(SEND_VARIABLE, value, f"Wave: {label} sent", [e for lane in lanes for e in _send(lane)])
            for value, (label, lanes) in SETS.items()
        ),
        *(
            _on(WALK_VARIABLE, value, f"Wave: {label} walk in", [e for lane in lanes for e in _walk_in(lane)])
            for value, (label, lanes) in SETS.items()
        ),
        *research,
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


def units() -> list[str]:
    """Every unit a wave can bring, in index order: the lines, then siege and the Priest."""
    return [line.unit for line in table.LINES] + table.specials()


def data(game) -> list[str]:
    """The tables as XS arrays, declared and filled by crucibleWaveData(). `game`: the RoR data (what each upgrade
    improves). Indexes: a line at its place in wave_table.LINES (slots hold line indexes); whether archetype a may hold
    line l at a * lines + l; whether upgrade u improves unit k (units()) at u * units + k; a siege unit at
    age * SIEGE_CHOICES + n."""
    lines, everyone, ages = table.LINES, units(), list(Age)
    index = {unit: k for k, unit in enumerate(everyone)}
    allowed = [int(line.unit in a.lines) for a in table.ARCHETYPES for line in lines]
    siege = [
        table.SIEGE.get(age, ())[n] if n < len(table.SIEGE.get(age, ())) else None
        for age in ages
        for n in range(SIEGE_CHOICES)
    ]
    upgrade_index = {u.tech: n for n, u in enumerate(table.UPGRADES)}
    arrays = [
        _ints("crucibleWaveLineUnit", [table.unit_id(line.unit) for line in lines]),
        _ints("crucibleWaveLineSlot", [int(line.slot) for line in lines]),
        _ints("crucibleWaveLineAge", [int(line.age) for line in lines]),
        _strings("crucibleWaveLineName", [line.title for line in lines]),
        _ints("crucibleWaveAllowed", allowed, default=0),
        _ints("crucibleWaveArchetypeMain", [int(a.main) for a in table.ARCHETYPES]),
        _strings("crucibleWaveArchetypeName", [a.name for a in table.ARCHETYPES]),
        _ints("crucibleWaveStepWeight", [table.STEPS[s] for s in table.Step], default=0),
        _ints("crucibleWaveUpgradeTech", [u.tech for u in table.UPGRADES]),
        _ints("crucibleWaveUpgradeAge", [int(u.age) for u in table.UPGRADES]),
        _ints("crucibleWaveUpgradeRequires", [upgrade_index.get(u.requires, -1) for u in table.UPGRADES]),
        _strings("crucibleWaveUpgradeName", [u.name for u in table.UPGRADES]),
        _ints(
            "crucibleWaveImproves",
            [int(table.improves(game, u, unit)) for u in table.UPGRADES for unit in everyone],
            default=0,
        ),
        _ints("crucibleWaveSiegeUnit", [table.unit_id(u) if u else -1 for u in siege]),
        _ints("crucibleWaveSiegeIndex", [index[u] if u else -1 for u in siege]),
        _ints("crucibleWaveSiegeChance", [table.SIEGE_CHANCE.get(age, 0) for age in ages], default=0),
        _ints("crucibleWavePriestChance", [table.PRIEST_CHANCE.get(age, 0) for age in ages], default=0),
        _ints("crucibleWaveAgeTech", [table.AGE_TECHS.get(age, -1) for age in ages]),
        _strings("crucibleWaveAgeName", [a.title for a in ages]),
        _ints("crucibleWaveDifficultyOf", [int(table.GAME_DIFFICULTY.get(g, table.FALLBACK)) for g in range(5)]),
        _ints("crucibleWaveSendTime", [table.SEND_TIMES[d] for d in Difficulty]),
        _strings("crucibleWaveLaneName", [lane.name for lane in LANES]),
        _floats("crucibleWaveSpawnX", [lane.spawn[1][0] + 0.5 for lane in LANES]),
        _floats("crucibleWaveSpawnY", [lane.spawn[1][1] + 0.5 for lane in LANES]),
        _floats("crucibleWaveDirX", [lane.direction[0] for lane in LANES]),
        _floats("crucibleWaveDirY", [lane.direction[1] for lane in LANES]),
    ]
    names = [lines_[0].split(" = ")[0].strip() for lines_ in arrays]

    return [
        *(f"int {name} = -1;" for name in names),
        "void crucibleWaveData() {",
        *(line for lines_ in arrays for line in lines_),
        "}",
    ]


def xs(ctx, tech: int, game) -> str:
    wonder = next(u for u in ctx.scenario.unit_manager.units[PLAYER] if u.unit_const == WONDER)
    start = table.START
    lines = [
        "// ---- crucible run: waves (data) ----",
        f"const int cCrucibleWaveLegion = {LEGION};",
        f"const int cCrucibleWaveButton = {tech};",
        f"const int cCrucibleWaveWalkVariable = {_variable_id(ctx, WALK_VARIABLE)};",
        f"const int cCrucibleWaveSendVariable = {_variable_id(ctx, SEND_VARIABLE)};",
        f"const int cCrucibleWaveTimerVariable = {_variable_id(ctx, TIMER_VARIABLE)};",
        f"const int cCrucibleWaveButtonVariable = {_variable_id(ctx, BUTTON_VARIABLE)};",
        f"const int cCrucibleWaveTechVariable = {_variable_id(ctx, TECH_VARIABLE)};",
        f"const int cCrucibleWaveLanes = {len(LANES)};",
        f"const int cCrucibleWaveCapitalLanes = {len(CAPITAL)};",
        f"const int cCrucibleWaveLines = {len(table.LINES)};",
        f"const int cCrucibleWaveUnits = {len(units())};",
        f"const int cCrucibleWaveArchetypes = {len(table.ARCHETYPES)};",
        f"const int cCrucibleWaveUpgrades = {len(table.UPGRADES)};",
        f"const int cCrucibleWaveSteps = {len(table.Step)};",
        f"const int cCrucibleWaveLastAge = {int(Age.POST_IRON)};",
        f"const int cCrucibleWaveSiegeAge = {int(min(table.SIEGE))};",
        f"const int cCrucibleWaveSiegeChoices = {SIEGE_CHOICES};",
        f"const int cCrucibleWavePriest = {table.unit_id(table.PRIEST)};",
        f"const int cCrucibleWavePriestIndex = {len(units()) - 1};",
        f"const int cCrucibleWaveAgeUpStart = {table.AGE_UP_START};",
        f"const int cCrucibleWaveAgeUpStep = {table.AGE_UP_STEP};",
        f"const int cCrucibleWaveMaxSteps = {table.MAX_STEPS};",
        f"const int cCrucibleWaveMainShare = {table.MAIN_SHARE};",
        f"const int cCrucibleWaveGrowPer = {table.GROW_PER};",
        f"const int cCrucibleWaveStartMelee = {table.LINES.index(table.BY_UNIT[start[Slot.MELEE][0]])};",
        f"const int cCrucibleWaveStartMeleeCount = {start[Slot.MELEE][1]};",
        f"const int cCrucibleWaveStartRanged = {table.LINES.index(table.BY_UNIT[start[Slot.RANGED][0]])};",
        f"const int cCrucibleWaveStartRangedCount = {start[Slot.RANGED][1]};",
        f"const int cCrucibleWaveTierUpPerWave = {table.TIER_UP_PER_WAVE};",
        f"const int cCrucibleWaveDoubleEvery = {table.DOUBLE_EVERY};",
        f"const int cCrucibleWaveColumns = {COLUMNS};",
        f"const float cCrucibleWaveSpacing = {SPACING};",
        f"const float cCrucibleWaveRowSpacing = {ROW_SPACING};",
        f"const int cCrucibleWaveCounterPlayer = {TRADERS};",
        f"const int cCrucibleWaveCounterRelics = {RELICS};",
        f"const int cCrucibleWaveWonder = {wonder.reference_id};",
        f"vector cCrucibleWaveWonderAt = vector({wonder.x}, {wonder.y}, 0.0);",
        f"const float cCrucibleWaveAtWonder = {float(AT_WONDER * AT_WONDER)};",
        *data(game),
        "bool crucibleWaveIn(vector pos = cInvalidVector, int x1 = 0, int y1 = 0, int x2 = 0, int y2 = 0) {",
        "    float x = xsVectorGetX(pos);",
        "    float y = xsVectorGetY(pos);",
        "    return ((x >= x1) && (x < x2 + 1) && (y >= y1) && (y < y2 + 1));",
        "}",
        _staged(),
    ]

    return "\n".join(lines) + "\n" + RUNTIME.read_text(encoding="utf-8")


def add(ctx, techs: dict[str, int], game) -> None:
    """`game`: the RoR data (source_dat)."""
    tech = techs[SEND_WAVE]
    _triggers(ctx, tech)
    ctx.xs(xs(ctx, tech, game))
