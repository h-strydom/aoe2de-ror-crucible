"""Wall-breaker: XS that keeps an attacker's melee units from standing stuck at walls.

An attack-move picks units and buildings it can reach; a wall in the way is never chosen, so a melee unit facing a
closed wall (or a tower walled in all round) stands there. Every INTERVAL seconds the rule looks at each melee unit
of the attacker: a unit that hasn't moved and isn't hurting its target (no target, or one whose HP didn't drop) for
two checks in a row is stuck. A stuck unit is ordered to attack the nearest wall or gate of a victim within REACH
tiles, else the nearest building or tower, else to attack-move on to where it was first headed.

Unit ids are the scenario's reference ids (`xsGetPlayerUnitIds`); orders go through `xsTaskUnits`, the editor's
Task Object.
"""

INTERVAL = 2  # seconds between checks
REACH = 4  # tiles: how far a stuck unit looks for a wall to break
MOVED = 0.3  # tiles: less than this between checks is standing still
STUCK_CHECKS = 2  # checks in a row before it acts
TRACKED = 500  # units it can follow at once
CLASS = 900  # XS class ids are 900 + the data's class
WALL_CLASSES = (27, 39)  # walls and gates
BUILDING_CLASSES = (52, 3)  # towers, other buildings
MELEE_CLASSES = (6, 12, 47)  # infantry, cavalry (with elephants and chariots), scouts


def xs(attacker: int, victims: tuple[int, ...], *, prefix: str = "crucibleBreaker", chat: bool = False) -> str:
    """The rule for `attacker`'s melee units against `victims`' walls. `chat`: say each order in the chat (checks)."""
    p = prefix
    walls = "\n".join(f"    best = {p}Nearest({v}, {CLASS + c}, x, y, best);" for v in victims for c in WALL_CLASSES)
    buildings = "\n".join(
        f"        best = {p}Nearest({v}, {CLASS + c}, x, y, best);" for v in victims for c in BUILDING_CLASSES
    )
    classes = "\n".join(f"    {p}Class({CLASS + c});" for c in MELEE_CLASSES)
    say = (lambda text: f'    xsChatData("{text}", id);') if chat else (lambda text: "")

    return f"""// ---- crucible: wall-breaker (player {attacker}) ----
int {p}Ids = -1;  // the units followed, and what was last seen of each
int {p}X = -1;
int {p}Y = -1;
int {p}Hp = -1;  // its target's HP
int {p}Stuck = -1;
int {p}Goal = -1;  // where it was first headed
int {p}Count = 0;
int {p}One = -1;  // a one-unit array for xsTaskUnits
float {p}BestDistance = 0.0;

// The nearest of `owner`'s units of `type` within REACH of (x, y), or `best` if none is nearer.
int {p}Nearest(int owner = -1, int type = -1, float x = 0.0, float y = 0.0, int best = -1) {{
    int ids = xsGetPlayerUnitIds(owner, type, -1);

    for (i = 0; < xsArrayGetSize(ids)) {{
        int id = xsArrayGetInt(ids, i);
        vector at = xsGetUnitPosition(id);
        float dx = xsVectorGetX(at) - x;
        float dy = xsVectorGetY(at) - y;
        float d = dx * dx + dy * dy;

        if ((d <= {REACH * REACH}.0) && ((best < 0) || (d < {p}BestDistance))) {{
            best = id;
            {p}BestDistance = d;
        }}
    }}

    return (best);
}}

int {p}Index(int id = -1) {{
    for (i = 0; < {p}Count) {{
        if (xsArrayGetInt({p}Ids, i) == id) {{
            return (i);
        }}
    }}

    if ({p}Count >= {TRACKED}) {{
        return (-1);
    }}

    int k = {p}Count;
    vector at = xsGetUnitPosition(id);
    vector goal = xsGetUnitMoveTarget(id);

    if (xsVectorGetX(goal) < 0.0) {{
        goal = at;
    }}

    xsArraySetInt({p}Ids, k, id);
    xsArraySetFloat({p}X, k, xsVectorGetX(at) + 100.0);  // so the first check counts as moving
    xsArraySetFloat({p}Y, k, xsVectorGetY(at));
    xsArraySetFloat({p}Hp, k, -1.0);
    xsArraySetInt({p}Stuck, k, 0);
    xsArraySetVector({p}Goal, k, goal);
    {p}Count = {p}Count + 1;

    return (k);
}}

void {p}Act(int id = -1, int k = 0, float x = 0.0, float y = 0.0) {{
    int best = -1;
    {p}BestDistance = 0.0;
{walls}
    if (best < 0) {{
{buildings}
    }}

    xsArraySetInt({p}One, 0, id);

    if (best >= 0) {{
        xsTaskUnits({p}One, cActionTypeDefault, xsGetUnitPosition(best), best);
{say("Breaker: unit %d attacks a wall")}
    }} else {{
        xsTaskUnits({p}One, cActionTypeAttackMove, xsArrayGetVector({p}Goal, k));
{say("Breaker: unit %d moves on")}
    }}
}}

void {p}Class(int type = -1) {{
    int ids = xsGetPlayerUnitIds({attacker}, type, -1);

    for (i = 0; < xsArrayGetSize(ids)) {{
        int id = xsArrayGetInt(ids, i);
        int k = {p}Index(id);

        if (k < 0) {{
            continue;
        }}

        vector at = xsGetUnitPosition(id);
        float x = xsVectorGetX(at);
        float y = xsVectorGetY(at);
        float dx = x - xsArrayGetFloat({p}X, k);
        float dy = y - xsArrayGetFloat({p}Y, k);
        int target = xsGetUnitTargetUnitId(id);
        float hp = -1.0;

        if (target >= 0) {{
            hp = xsGetUnitHitpoints(target);
        }}

        bool moving = (dx * dx + dy * dy) > {MOVED * MOVED};
        bool hurting = (target >= 0) && (hp < xsArrayGetFloat({p}Hp, k));
        int stuck = 0;

        if ((moving == false) && (hurting == false)) {{
            stuck = xsArrayGetInt({p}Stuck, k) + 1;
        }}

        if (stuck >= {STUCK_CHECKS}) {{
            {p}Act(id, k, x, y);
            stuck = 0;
        }}

        xsArraySetFloat({p}X, k, x);
        xsArraySetFloat({p}Y, k, y);
        xsArraySetFloat({p}Hp, k, hp);
        xsArraySetInt({p}Stuck, k, stuck);
    }}
}}

rule {p}Rule
    active
    minInterval {INTERVAL}
{{
    if ({p}Ids < 0) {{
        {p}Ids = xsArrayCreateInt({TRACKED}, -1, "{p}Ids");
        {p}X = xsArrayCreateFloat({TRACKED}, 0.0, "{p}X");
        {p}Y = xsArrayCreateFloat({TRACKED}, 0.0, "{p}Y");
        {p}Hp = xsArrayCreateFloat({TRACKED}, -1.0, "{p}Hp");
        {p}Stuck = xsArrayCreateInt({TRACKED}, 0, "{p}Stuck");
        {p}Goal = xsArrayCreateVector({TRACKED}, vector(-1.0, -1.0, -1.0), "{p}Goal");
        {p}One = xsArrayCreateInt(1, -1, "{p}One");
    }}

{classes}
}}
"""
