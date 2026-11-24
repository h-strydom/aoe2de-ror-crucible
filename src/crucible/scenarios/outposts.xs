// ---- crucible run: the Legion's outposts, runtime (scenarios/outposts.xs; the generated data block comes first) ----
// docs/outposts.md. Each outpost keeps its units in one list (members): its garrison, wandering round its posts or
// patrolling between two; its spot guards, wandering on their spot; at sea its ships, wandering round their spots.
// Units come out of its buildings (land units by any building, ships by its docks); a destroyed building makes none.
// Every few minutes it takes a turn (playtest 2026-11-24):
// - hit in the last cCrucibleOutpostTurtle seconds it is turtled: while the player is still near it defends (its
//   garrison hunts the player's units) and makes nothing; once the player has gone it tops up beyond its usual garrison;
// - else it tops up its garrison a little, then sends guards to the first of its spots the player is on (more the
//   longer the player stays) or that has too few guards; with all its spots guarded, it sends an attack wave (land:
//   from its marker on the south edge; sea: by transport, with escorts, to one of its landings; faked landing).
// Nothing is made while the player's units are near it. Units of lines the outpost has moved on from go out first
// (to spots and in waves), so the garrison is made anew. The player's units are known by type every few seconds
// (crucibleOutpostScan): the map hack.

int crucibleOutpostArchetype = -1;  // by outpost
int crucibleOutpostGrowth = -1;  // by outpost: 10 a level
int crucibleOutpostAlive = -1;  // by outpost: 1 while a building stands
int crucibleOutpostNextTurn = -1;  // by outpost: seconds
int crucibleOutpostHarassedAt = -1;  // by outpost: seconds, -1 never
int crucibleOutpostTurtleSpawn = -1;  // by outpost: the next turtled spawn, seconds
int crucibleOutpostHunting = -1;  // by outpost: 1 while its garrison hunts
int crucibleOutpostHuntX = -1;  // by outpost: where it last sent its garrison
int crucibleOutpostHuntY = -1;
int crucibleOutpostShipsOut = -1;  // by outpost: 1 while its ships chase something
int crucibleOutpostShipX = -1;
int crucibleOutpostShipY = -1;
int crucibleOutpostSpawned = -1;  // by outpost: units made (takes its doors in turn)
int crucibleOutpostBuildingHp = -1;  // by building: its HP last second
int crucibleOutpostMemberId = -1;  // by outpost * cCrucibleOutpostMembers: unit id, -1 a free place
int crucibleOutpostMemberType = -1;
int crucibleOutpostMemberRole = -1;  // 1 garrison, 2 spot guard, 3 ship
int crucibleOutpostMemberAnchor = -1;  // its post, spot or ship spot (index into the outpost's, or the spot)
int crucibleOutpostMemberPatrol = -1;  // 1: patrols between its post and the next
int crucibleOutpostMemberLeg = -1;  // patrolling: 0 to its post, 1 to the next
int crucibleOutpostMemberNext = -1;  // seconds: its next order
int crucibleOutpostMemberHp = -1;
int crucibleOutpostMemberX = -1;  // where it was last sent
int crucibleOutpostMemberY = -1;
int crucibleOutpostEnemyId = -1;  // the player's land units, as last scanned
int crucibleOutpostEnemyX = -1;
int crucibleOutpostEnemyY = -1;
int crucibleOutpostEnemyCount = 0;
int crucibleOutpostSeaId = -1;  // the player's ships and docks
int crucibleOutpostSeaX = -1;
int crucibleOutpostSeaY = -1;
int crucibleOutpostSeaCount = 0;
int crucibleOutpostSpotContest = -1;  // by spot: the player's units on it
int crucibleOutpostSpotPressure = -1;  // by spot: up while contested, down while clear
int crucibleOutpostTransport = -1;  // by transport: unit id, -1 free
int crucibleOutpostTransportOutpost = -1;
int crucibleOutpostTransportUnit = -1;  // the type it lands
int crucibleOutpostTransportCount = -1;  // how many it lands
int crucibleOutpostTransportState = -1;  // 1 sailing in, 2 sailing off
int crucibleOutpostTransportTime = -1;
int crucibleOutpostTransportMarker = -1;  // the sea marker (index) it came from and leaves by
int crucibleOutpostTransportLanding = -1;  // its landing (index)
int crucibleOutpostEscort = -1;  // by escort: unit id, -1 free
int crucibleOutpostEscortLead = -1;  // the transport (unit id) it escorts
int crucibleOutpostEscortMarker = -1;
int crucibleOutpostEscortLanding = -1;
int crucibleOutpostEscortState = -1;  // 1 escorting, 2 leaving
int crucibleOutpostEscortTime = -1;
int crucibleOutpostFound = -1;  // reused: xsGetPlayerUnitIds
int crucibleOutpostIds = -1;  // reused: a list of ids for xsTaskUnits
int crucibleOutpostNextScan = 0;
int crucibleOutpostNextPressure = 0;

float crucibleOutpostHp(int id = -1) {
    if (id < 0) {
        return (0.0);
    }

    float hp = xsGetUnitProperty(id, cUnitHitpoints);

    if (hp < 0.0) {
        return (0.0);
    }

    return (hp);
}

float crucibleOutpostDist2(float ax = 0.0, float ay = 0.0, float bx = 0.0, float by = 0.0) {
    float dx = ax - bx;
    float dy = ay - by;

    return (dx * dx + dy * dy);
}

vector crucibleOutpostAt(float x = 0.0, float y = 0.0) {
    return (xsVectorSet(x, y, 0.0));
}

float crucibleOutpostHomeX(int o = 0) {
    return (xsArrayGetFloat(crucibleOutpostHomesX, o));
}

float crucibleOutpostHomeY(int o = 0) {
    return (xsArrayGetFloat(crucibleOutpostHomesY, o));
}

vector crucibleOutpostWonder() {
    return (xsVectorSet(cCrucibleOutpostWonderX, cCrucibleOutpostWonderY, 0.0));
}

int crucibleOutpostLevel(int o = 0) {
    return (xsArrayGetInt(crucibleOutpostGrowth, o) / 10);
}

bool crucibleOutpostTurtled(int o = 0) {
    int at = xsArrayGetInt(crucibleOutpostHarassedAt, o);

    return ((at >= 0) && (xsGetTime() - at < cCrucibleOutpostTurtle));
}

bool crucibleOutpostSea(int o = 0) {
    return (xsArrayGetInt(crucibleOutpostIsSea, o) == 1);
}

// The difficulty's percent of a party's size (at least `least`).
int crucibleOutpostScaled(int size = 0, int least = 1) {
    int scaled = size * xsArrayGetInt(crucibleOutpostAggression, crucibleWaveDifficulty) / 100;

    if (scaled < least) {
        return (least);
    }

    return (scaled);
}

int crucibleOutpostCap(int size = 0, int most = 0) {
    if (size > most) {
        return (most);
    }

    return (size);
}

// A random offset of up to `r` either way.
float crucibleOutpostJitter(float r = 0.0) {
    int steps = xsGetRandomNumberLH(0, 201);
    float f = steps;

    return ((f - 100.0) * r / 100.0);
}

void crucibleOutpostSay(int o = 0, string what = "") {
    if (cCrucibleOutpostDebug == false) {
        return;
    }

    string name = xsArrayGetString(crucibleOutpostName, o);
    string kind = xsArrayGetString(crucibleOutpostArchetypeName, xsArrayGetInt(crucibleOutpostArchetype, o));

    xsChatData(name + " (" + kind + "): " + what + ", level %d", crucibleOutpostLevel(o));
}

void crucibleOutpostTaskOne(int id = -1, int action = -1, vector at = cInvalidVector) {
    xsArrayResizeInt(crucibleOutpostIds, 1);
    xsArraySetInt(crucibleOutpostIds, 0, id);
    xsTaskUnits(crucibleOutpostIds, action, at);
}

// ---- the map hack ----

void crucibleOutpostScanTypes(int types = -1, bool land = true) {
    int count = 0;
    int id = -1;
    int n = 0;
    vector at = cInvalidVector;

    for (t = 0; < xsArrayGetSize(types)) {
        crucibleOutpostFound = xsGetPlayerUnitIds(cCrucibleOutpostPlayer, xsArrayGetInt(types, t), crucibleOutpostFound);
        count = xsArrayGetSize(crucibleOutpostFound);

        for (k = 0; < count) {
            id = xsArrayGetInt(crucibleOutpostFound, k);

            if (crucibleOutpostHp(id) <= 0.0) {
                continue;
            }

            at = xsGetUnitPosition(id);

            if (land) {
                n = crucibleOutpostEnemyCount;

                if (n < cCrucibleOutpostEnemyMax) {
                    xsArraySetInt(crucibleOutpostEnemyId, n, id);
                    xsArraySetFloat(crucibleOutpostEnemyX, n, xsVectorGetX(at));
                    xsArraySetFloat(crucibleOutpostEnemyY, n, xsVectorGetY(at));
                    crucibleOutpostEnemyCount++;
                }
            } else {
                n = crucibleOutpostSeaCount;

                if (n < cCrucibleOutpostEnemyMax) {
                    xsArraySetInt(crucibleOutpostSeaId, n, id);
                    xsArraySetFloat(crucibleOutpostSeaX, n, xsVectorGetX(at));
                    xsArraySetFloat(crucibleOutpostSeaY, n, xsVectorGetY(at));
                    crucibleOutpostSeaCount++;
                }
            }
        }
    }
}

// The player's units and ships, and each spot's contest.
void crucibleOutpostScan() {
    int found = 0;
    float sx = 0.0;
    float sy = 0.0;
    float r2 = cCrucibleOutpostSpotRadius * cCrucibleOutpostSpotRadius;

    crucibleOutpostEnemyCount = 0;
    crucibleOutpostSeaCount = 0;
    crucibleOutpostScanTypes(crucibleOutpostLandTypes, true);
    crucibleOutpostScanTypes(crucibleOutpostSeaTypes, false);

    for (s = 0; < cCrucibleOutpostSpots) {
        sx = xsArrayGetFloat(crucibleOutpostSpotX, s);
        sy = xsArrayGetFloat(crucibleOutpostSpotY, s);
        found = 0;

        for (e = 0; < crucibleOutpostEnemyCount) {
            if (crucibleOutpostDist2(sx, sy, xsArrayGetFloat(crucibleOutpostEnemyX, e),
                    xsArrayGetFloat(crucibleOutpostEnemyY, e)) <= r2) {
                found++;
            }
        }

        xsArraySetInt(crucibleOutpostSpotContest, s, found);
    }
}

// The player's land unit nearest (x, y) within `range`; -1 if none.
int crucibleOutpostNearest(float x = 0.0, float y = 0.0, float range = 0.0) {
    int best = -1;
    float bestD = range * range;
    float d = 0.0;

    for (e = 0; < crucibleOutpostEnemyCount) {
        d = crucibleOutpostDist2(x, y, xsArrayGetFloat(crucibleOutpostEnemyX, e), xsArrayGetFloat(crucibleOutpostEnemyY, e));

        if (d <= bestD) {
            bestD = d;
            best = e;
        }
    }

    return (best);
}

int crucibleOutpostNearestSea(float x = 0.0, float y = 0.0, float range = 0.0) {
    int best = -1;
    float bestD = range * range;
    float d = 0.0;

    for (e = 0; < crucibleOutpostSeaCount) {
        d = crucibleOutpostDist2(x, y, xsArrayGetFloat(crucibleOutpostSeaX, e), xsArrayGetFloat(crucibleOutpostSeaY, e));

        if (d <= bestD) {
            bestD = d;
            best = e;
        }
    }

    return (best);
}

// The player is near outpost o (land units or ships): it makes nothing.
bool crucibleOutpostPlayerNear(int o = 0) {
    float hx = crucibleOutpostHomeX(o);
    float hy = crucibleOutpostHomeY(o);

    if (crucibleOutpostNearest(hx, hy, cCrucibleOutpostHuntRange) >= 0) {
        return (true);
    }

    return (crucibleOutpostNearestSea(hx, hy, cCrucibleOutpostHuntRange) >= 0);
}

// ---- what it fields ----

int crucibleOutpostBase(int o = 0) {
    return (cCrucibleOutpostStartDefenders + crucibleOutpostLevel(o) / cCrucibleOutpostLevelsPerDefender
        + crucibleWaveAge * cCrucibleOutpostDefendersPerAge);
}

// Its garrison: land units and ships (half, at sea), larger while turtled.
int crucibleOutpostTarget(int o = 0) {
    if (crucibleOutpostTurtled(o)) {
        return (crucibleOutpostBase(o) * xsArrayGetInt(crucibleOutpostTurtleScale, crucibleWaveDifficulty));
    }

    return (crucibleOutpostBase(o) * xsArrayGetInt(crucibleOutpostGarrisonScale, crucibleWaveDifficulty));
}

int crucibleOutpostLandTarget(int o = 0) {
    int target = crucibleOutpostTarget(o);

    if (crucibleOutpostSea(o)) {
        target = target - target / 2;
    }

    return (crucibleOutpostCap(target, cCrucibleOutpostMax));
}

int crucibleOutpostShipTarget(int o = 0) {
    if (crucibleOutpostSea(o) == false) {
        return (0);
    }

    return (crucibleOutpostCap(crucibleOutpostTarget(o) / 2, cCrucibleOutpostShipMax));
}

// Its archetype's unit for `slot` at the Legion's age: later lines with level.
int crucibleOutpostSlotUnit(int o = 0, int slot = 0) {
    int k = (xsArrayGetInt(crucibleOutpostArchetype, o) * 2 + slot) * cCrucibleOutpostAges + crucibleWaveAge;
    int start = xsArrayGetInt(crucibleOutpostPoolStart, k);
    int count = xsArrayGetInt(crucibleOutpostPoolStart, k + 1) - start;
    int pick = crucibleOutpostLevel(o) / cCrucibleOutpostLevelsPerLine + crucibleWaveAge;

    if (count <= 0) {
        return (-1);
    }

    if (pick > count - 1) {
        pick = count - 1;
    }

    return (xsArrayGetInt(crucibleOutpostPoolUnits, start + pick));
}

// Its unit: the main slot most of the time.
int crucibleOutpostUnit(int o = 0) {
    int slot = xsArrayGetInt(crucibleOutpostMain, xsArrayGetInt(crucibleOutpostArchetype, o));
    int unit = -1;

    if (xsGetRandomNumberLH(0, 100) >= cCrucibleOutpostMainShare) {
        slot = 1 - slot;
    }

    unit = crucibleOutpostSlotUnit(o, slot);

    if (unit < 0) {
        unit = crucibleOutpostSlotUnit(o, 1 - slot);
    }

    return (unit);
}

int crucibleOutpostShipUnit(int o = 0) {
    int start = xsArrayGetInt(crucibleOutpostShipPoolStart, crucibleWaveAge);
    int count = xsArrayGetInt(crucibleOutpostShipPoolStart, crucibleWaveAge + 1) - start;
    int pick = crucibleOutpostLevel(o) / cCrucibleOutpostLevelsPerLine + crucibleWaveAge;

    if (pick > count - 1) {
        pick = count - 1;
    }

    return (xsArrayGetInt(crucibleOutpostShipPoolUnits, start + pick));
}

// A unit of a line it has moved on from (neither slot's unit now).
bool crucibleOutpostOutdated(int o = 0, int unit = -1) {
    return ((unit != crucibleOutpostSlotUnit(o, 0)) && (unit != crucibleOutpostSlotUnit(o, 1)));
}

// ---- making units: out of its buildings ----

// A door of a standing building of outpost o (a dock's for ships), in turn; -1 if none.
int crucibleOutpostDoor(int o = 0, bool dock = false) {
    int start = xsArrayGetInt(crucibleOutpostDoorStart, o);
    int count = xsArrayGetInt(crucibleOutpostDoorStart, o + 1) - start;
    int n = xsArrayGetInt(crucibleOutpostSpawned, o);
    int d = 0;
    bool isDock = false;

    xsArraySetInt(crucibleOutpostSpawned, o, n + 1);

    for (k = 0; < count) {
        d = start + (n + k) % count;
        isDock = (xsArrayGetInt(crucibleOutpostDoorDock, d) == 1);

        if ((isDock == dock) && (crucibleOutpostHp(xsArrayGetInt(crucibleOutpostDoorBuilding, d)) > 0.0)) {
            return (d);
        }
    }

    return (-1);
}

// A unit of type `unit` out of one of its buildings (ships out of a dock); its id, -1 if none.
int crucibleOutpostMake(int o = 0, int unit = -1, bool ship = false) {
    int d = crucibleOutpostDoor(o, ship);

    if ((d < 0) || (unit < 0)) {
        return (-1);
    }

    return (xsCreateUnit(unit, cCrucibleOutpostLegion, crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostDoorX, d),
        xsArrayGetFloat(crucibleOutpostDoorY, d)), false, false, false));
}

// ---- members ----

int crucibleOutpostMemberCount(int o = 0, int role = 0, int anchor = -1) {
    int found = 0;
    int k = 0;

    for (m = 0; < cCrucibleOutpostMembers) {
        k = o * cCrucibleOutpostMembers + m;

        if ((xsArrayGetInt(crucibleOutpostMemberId, k) >= 0) && (xsArrayGetInt(crucibleOutpostMemberRole, k) == role)) {
            if ((anchor < 0) || (xsArrayGetInt(crucibleOutpostMemberAnchor, k) == anchor)) {
                found++;
            }
        }
    }

    return (found);
}

int crucibleOutpostCount(int o = 0) {
    return (crucibleOutpostMemberCount(o, 1, -1));
}

int crucibleOutpostShipCount(int o = 0) {
    return (crucibleOutpostMemberCount(o, 3, -1));
}

int crucibleOutpostPosts(int o = 0) {
    return (xsArrayGetInt(crucibleOutpostPostStart, o + 1) - xsArrayGetInt(crucibleOutpostPostStart, o));
}

int crucibleOutpostShipSpots(int o = 0) {
    return (xsArrayGetInt(crucibleOutpostShipSpotStart, o + 1) - xsArrayGetInt(crucibleOutpostShipSpotStart, o));
}

// Unit `id` (type `unit`) joins outpost o as `role` at `anchor` (-1: the next post or ship spot in turn); its slot.
int crucibleOutpostJoin(int o = 0, int id = -1, int unit = -1, int role = 0, int anchor = -1) {
    int k = 0;
    int a = anchor;

    for (m = 0; < cCrucibleOutpostMembers) {
        k = o * cCrucibleOutpostMembers + m;

        if (xsArrayGetInt(crucibleOutpostMemberId, k) >= 0) {
            continue;
        }

        if ((a < 0) && (role == 1)) {
            a = m % crucibleOutpostPosts(o);
        } else if ((a < 0) && (role == 3)) {
            a = m % crucibleOutpostShipSpots(o);
        }

        xsArraySetInt(crucibleOutpostMemberId, k, id);
        xsArraySetInt(crucibleOutpostMemberType, k, unit);
        xsArraySetInt(crucibleOutpostMemberRole, k, role);
        xsArraySetInt(crucibleOutpostMemberAnchor, k, a);
        xsArraySetInt(crucibleOutpostMemberPatrol, k, 0);
        xsArraySetInt(crucibleOutpostMemberLeg, k, 0);
        xsArraySetInt(crucibleOutpostMemberNext, k, 0);
        xsArraySetFloat(crucibleOutpostMemberHp, k, crucibleOutpostHp(id));
        xsArraySetFloat(crucibleOutpostMemberX, k, -100.0);
        xsArraySetFloat(crucibleOutpostMemberY, k, -100.0);

        if ((role == 1) && (crucibleOutpostPosts(o) > 1) && (m % cCrucibleOutpostPatrolEvery == 0)) {
            xsArraySetInt(crucibleOutpostMemberPatrol, k, 1);
        }

        return (k);
    }

    return (-1);
}

// Sends member k to (x, y) unless it was sent near there already (or `always`).
void crucibleOutpostSend(int k = 0, float x = 0.0, float y = 0.0, bool always = false) {
    if ((always == false) && (crucibleOutpostDist2(x, y, xsArrayGetFloat(crucibleOutpostMemberX, k),
        xsArrayGetFloat(crucibleOutpostMemberY, k)) < 9.0)) {
        return;
    }

    xsArraySetFloat(crucibleOutpostMemberX, k, x);
    xsArraySetFloat(crucibleOutpostMemberY, k, y);
    crucibleOutpostTaskOne(xsArrayGetInt(crucibleOutpostMemberId, k), cActionTypeAttackMove, crucibleOutpostAt(x, y));
}

// Makes a member of `role` (1 garrison, 3 ship) out of its buildings; false if none could be made.
bool crucibleOutpostSpawn(int o = 0, int role = 1) {
    int unit = crucibleOutpostUnit(o);
    int id = -1;

    if (role == 3) {
        unit = crucibleOutpostShipUnit(o);
    }

    id = crucibleOutpostMake(o, unit, role == 3);

    if (id < 0) {
        return (false);
    }

    if (crucibleOutpostJoin(o, id, unit, role, -1) < 0) {
        xsSetUnitProperty(id, cUnitHitpoints, 0.0);
        return (false);
    }

    return (true);
}

// Up to `most` more of its garrison, land and ships in turn; how many came.
int crucibleOutpostTopUp(int o = 0, int most = 0) {
    int land = crucibleOutpostLandTarget(o) - crucibleOutpostCount(o);
    int ships = crucibleOutpostShipTarget(o) - crucibleOutpostShipCount(o);
    int made = 0;

    while ((made < most) && ((land > 0) || (ships > 0))) {
        if (land > 0) {
            if (crucibleOutpostSpawn(o, 1) == false) {
                land = 0;
            } else {
                land--;
                made++;
            }
        }

        if ((ships > 0) && (made < most)) {
            if (crucibleOutpostSpawn(o, 3) == false) {
                ships = 0;
            } else {
                ships--;
                made++;
            }
        }
    }

    return (made);
}

// ---- orders ----

// Member k's anchor: its post, spot or ship spot (patrolling, the next post on its way back).
vector crucibleOutpostAnchor(int o = 0, int k = 0, int leg = 0) {
    int role = xsArrayGetInt(crucibleOutpostMemberRole, k);
    int a = xsArrayGetInt(crucibleOutpostMemberAnchor, k);
    int i = 0;

    if (role == 2) {
        return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostSpotX, a), xsArrayGetFloat(crucibleOutpostSpotY, a)));
    }

    if (role == 3) {
        i = xsArrayGetInt(crucibleOutpostShipSpotStart, o) + a % crucibleOutpostShipSpots(o);
        return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostShipSpotX, i), xsArrayGetFloat(crucibleOutpostShipSpotY,
            i)));
    }

    i = xsArrayGetInt(crucibleOutpostPostStart, o) + (a + leg) % crucibleOutpostPosts(o);

    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostPostX, i), xsArrayGetFloat(crucibleOutpostPostY, i)));
}

// Member k's next step when it has nothing to fight: a wander round its anchor, or the next leg of its patrol.
void crucibleOutpostIdle(int o = 0, int k = 0, int now = 0) {
    int role = xsArrayGetInt(crucibleOutpostMemberRole, k);
    int leg = 0;
    int travel = 0;
    float r = cCrucibleOutpostPostWander;
    vector at = cInvalidVector;
    vector other = cInvalidVector;

    if (now < xsArrayGetInt(crucibleOutpostMemberNext, k)) {
        return;
    }

    if (xsArrayGetInt(crucibleOutpostMemberPatrol, k) == 1) {
        leg = 1 - xsArrayGetInt(crucibleOutpostMemberLeg, k);
        xsArraySetInt(crucibleOutpostMemberLeg, k, leg);
        at = crucibleOutpostAnchor(o, k, leg);
        other = crucibleOutpostAnchor(o, k, 1 - leg);
        travel = sqrt(crucibleOutpostDist2(xsVectorGetX(at), xsVectorGetY(at), xsVectorGetX(other),
            xsVectorGetY(other)));
        xsArraySetInt(crucibleOutpostMemberNext, k, now + 6 + travel);  // about a tile a second
        crucibleOutpostSend(k, xsVectorGetX(at), xsVectorGetY(at), true);
        return;
    }

    if (role == 2) {
        r = cCrucibleOutpostSpotWander;
    } else if (role == 3) {
        r = cCrucibleOutpostShipWander;
    }

    at = crucibleOutpostAnchor(o, k, 0);
    xsArraySetInt(crucibleOutpostMemberNext, k, now + cCrucibleOutpostWanderEvery
        + xsGetRandomNumberLH(0, cCrucibleOutpostWanderSpread + 1));
    crucibleOutpostSend(k, xsVectorGetX(at) + crucibleOutpostJitter(r), xsVectorGetY(at) + crucibleOutpostJitter(r), true);
}

// Every few seconds: the garrison hunts while turtled with the player near, else wanders; spot guards go for the
// player on their spot, else wander; ships go for the player's ships and docks in reach, else wander.
void crucibleOutpostOrders(int o = 0) {
    int now = xsGetTime();
    int k = 0;
    int role = 0;
    int spot = -1;
    int e = -1;
    int hunt = -1;
    int sea = -1;
    float hx = crucibleOutpostHomeX(o);
    float hy = crucibleOutpostHomeY(o);
    float sx = 0.0;
    float sy = 0.0;
    float chase = cCrucibleOutpostSpotRadius + 4.0;

    if (crucibleOutpostTurtled(o)) {
        hunt = crucibleOutpostNearest(hx, hy, cCrucibleOutpostHuntRange);
    }

    if (crucibleOutpostSea(o)) {
        sea = crucibleOutpostNearestSea(hx, hy, cCrucibleOutpostSeaRange);
    }

    if ((hunt < 0) && (xsArrayGetInt(crucibleOutpostHunting, o) == 1)) {
        crucibleOutpostSay(o, "nobody left to hunt: back to its posts");
    } else if ((hunt >= 0) && (xsArrayGetInt(crucibleOutpostHunting, o) == 0)) {
        crucibleOutpostSay(o, "hunts the player's units near it");
    }

    if ((sea >= 0) && (xsArrayGetInt(crucibleOutpostShipsOut, o) == 0)) {
        crucibleOutpostSay(o, "ships go for the player's ships or docks");
    }

    xsArraySetInt(crucibleOutpostHunting, o, 0);
    xsArraySetInt(crucibleOutpostShipsOut, o, 0);

    if (hunt >= 0) {
        xsArraySetInt(crucibleOutpostHunting, o, 1);
    }

    if (sea >= 0) {
        xsArraySetInt(crucibleOutpostShipsOut, o, 1);
    }

    for (m = 0; < cCrucibleOutpostMembers) {
        k = o * cCrucibleOutpostMembers + m;

        if (xsArrayGetInt(crucibleOutpostMemberId, k) < 0) {
            continue;
        }

        role = xsArrayGetInt(crucibleOutpostMemberRole, k);

        if ((role == 1) && (hunt >= 0)) {
            crucibleOutpostSend(k, xsArrayGetFloat(crucibleOutpostEnemyX, hunt), xsArrayGetFloat(crucibleOutpostEnemyY,
                hunt), false);
            xsArraySetInt(crucibleOutpostMemberNext, k, 0);
            continue;
        }

        if ((role == 3) && (sea >= 0)) {
            crucibleOutpostSend(k, xsArrayGetFloat(crucibleOutpostSeaX, sea), xsArrayGetFloat(crucibleOutpostSeaY, sea),
                false);
            xsArraySetInt(crucibleOutpostMemberNext, k, 0);
            continue;
        }

        if (role == 2) {
            spot = xsArrayGetInt(crucibleOutpostMemberAnchor, k);
            e = -1;

            if (xsArrayGetInt(crucibleOutpostSpotContest, spot) > 0) {
                sx = xsArrayGetFloat(crucibleOutpostSpotX, spot);
                sy = xsArrayGetFloat(crucibleOutpostSpotY, spot);
                e = crucibleOutpostNearest(sx, sy, chase);
            }

            if (e >= 0) {
                crucibleOutpostSend(k, xsArrayGetFloat(crucibleOutpostEnemyX, e), xsArrayGetFloat(crucibleOutpostEnemyY,
                    e), false);
                xsArraySetInt(crucibleOutpostMemberNext, k, 0);
                continue;
            }
        }

        crucibleOutpostIdle(o, k, now);
    }
}

// Up to `size` of its garrison of lines it has moved on from leave it (into `ids` from `n`); how many.
int crucibleOutpostTakeOutdated(int o = 0, int size = 0, int n = 0) {
    int k = 0;
    int taken = 0;

    for (m = 0; < cCrucibleOutpostMembers) {
        k = o * cCrucibleOutpostMembers + m;

        if (taken >= size) {
            break;
        }

        if ((xsArrayGetInt(crucibleOutpostMemberId, k) < 0) || (xsArrayGetInt(crucibleOutpostMemberRole, k) != 1)) {
            continue;
        }

        if (crucibleOutpostOutdated(o, xsArrayGetInt(crucibleOutpostMemberType, k))) {
            xsArraySetInt(crucibleOutpostIds, n + taken, xsArrayGetInt(crucibleOutpostMemberId, k));
            xsArraySetInt(crucibleOutpostMemberId, k, -1);
            taken++;
        }
    }

    return (taken);
}

// `size` guards for `spot`: the garrison's outdated units first, then new ones out of its buildings; how many went.
int crucibleOutpostGuard(int o = 0, int spot = 0, int size = 0) {
    int unit = -1;
    int id = -1;
    int made = 0;
    int k = 0;

    xsArrayResizeInt(crucibleOutpostIds, size + 1);
    made = crucibleOutpostTakeOutdated(o, size, 0);

    for (n = 0; < made) {
        id = xsArrayGetInt(crucibleOutpostIds, n);
        unit = -1;
        k = crucibleOutpostJoin(o, id, unit, 2, spot);

        if (k >= 0) {
            crucibleOutpostSend(k, xsArrayGetFloat(crucibleOutpostSpotX, spot), xsArrayGetFloat(crucibleOutpostSpotY,
                spot), true);
            xsArraySetInt(crucibleOutpostMemberNext, k, xsGetTime() + 30);
        }
    }

    while (made < size) {
        unit = crucibleOutpostUnit(o);
        id = crucibleOutpostMake(o, unit, false);

        if (id < 0) {
            break;
        }

        k = crucibleOutpostJoin(o, id, unit, 2, spot);

        if (k < 0) {
            xsSetUnitProperty(id, cUnitHitpoints, 0.0);
            break;
        }

        crucibleOutpostSend(k, xsArrayGetFloat(crucibleOutpostSpotX, spot), xsArrayGetFloat(crucibleOutpostSpotY, spot),
            true);
        xsArraySetInt(crucibleOutpostMemberNext, k, xsGetTime() + 30);  // walks there before it wanders
        made++;
    }

    return (made);
}

// ---- attack waves ----

int crucibleOutpostWaveSize(int o = 0) {
    int size = cCrucibleOutpostWaveBase + crucibleOutpostLevel(o) / 2 + crucibleWaveAge * 2;

    return (crucibleOutpostCap(crucibleOutpostScaled(size, 2), cCrucibleOutpostWaveMax));
}

// Land: the garrison's outdated units and new ones at its marker on the south edge attack-move the Wonder.
void crucibleOutpostLandWave(int o = 0, int size = 0) {
    int id = -1;
    int n = 0;
    int old = 0;

    xsArrayResizeInt(crucibleOutpostIds, size + 1);
    old = crucibleOutpostTakeOutdated(o, size, 0);
    n = old;

    for (k = old; < size) {
        id = xsCreateUnit(crucibleOutpostUnit(o), cCrucibleOutpostLegion, crucibleOutpostAt(xsArrayGetFloat(
            crucibleOutpostMarkerX, o), xsArrayGetFloat(crucibleOutpostMarkerY, o)), false, false, false);

        if (id >= 0) {
            xsArraySetInt(crucibleOutpostIds, n, id);
            n++;
        }
    }

    if (n > 0) {
        xsArrayResizeInt(crucibleOutpostIds, n);
        xsTaskUnits(crucibleOutpostIds, cActionTypeAttackMove, crucibleOutpostWonder());
    }

    crucibleOutpostSay(o, "attack wave of " + n + " (" + old + " from its garrison)");
}

vector crucibleOutpostSeaSpawn(int m = 0) {
    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostSeaSpawnX, m), xsArrayGetFloat(crucibleOutpostSeaSpawnY, m)));
}

vector crucibleOutpostSeaExit(int m = 0) {
    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostSeaExitX, m), xsArrayGetFloat(crucibleOutpostSeaExitY, m)));
}

vector crucibleOutpostLandingWater(int l = 0) {
    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostLandingWaterX, l),
        xsArrayGetFloat(crucibleOutpostLandingWaterY, l)));
}

// Sea: transports (light ones while two can carry it, else heavy) and their escorts from its sea markers sail to one
// of its landings, at random.
void crucibleOutpostSeaWave(int o = 0, int size = 0) {
    int capacity = cCrucibleOutpostLightCapacity;
    int ship = cCrucibleOutpostLightTransport;
    int left = size;
    int carry = 0;
    int id = -1;
    int lead = -1;
    int sent = 0;
    int escorts = crucibleOutpostCap(1 + size / cCrucibleOutpostEscortPer, cCrucibleOutpostEscortMax);
    int made = 0;
    int markerStart = xsArrayGetInt(crucibleOutpostSeaMarkerStart, o);
    int markers = xsArrayGetInt(crucibleOutpostSeaMarkerStart, o + 1) - markerStart;
    int landingStart = xsArrayGetInt(crucibleOutpostLandingStart, o);
    int landings = xsArrayGetInt(crucibleOutpostLandingStart, o + 1) - landingStart;
    int marker = markerStart + xsGetRandomNumberLH(0, markers);
    int landing = landingStart + xsGetRandomNumberLH(0, landings);

    if ((markers <= 0) || (landings <= 0)) {
        return;
    }

    if (size > 2 * cCrucibleOutpostLightCapacity) {
        capacity = cCrucibleOutpostHeavyCapacity;
        ship = cCrucibleOutpostHeavyTransport;
    }

    for (t = 0; < cCrucibleOutpostTransportMax) {
        if ((left <= 0) || (xsArrayGetInt(crucibleOutpostTransport, t) >= 0)) {
            continue;
        }

        carry = crucibleOutpostCap(capacity, left);
        id = xsCreateUnit(ship, cCrucibleOutpostLegion, crucibleOutpostSeaSpawn(marker), false, false, false);

        if (id < 0) {
            continue;
        }

        if (lead < 0) {
            lead = id;
        }

        xsArraySetInt(crucibleOutpostTransport, t, id);
        xsArraySetInt(crucibleOutpostTransportOutpost, t, o);
        xsArraySetInt(crucibleOutpostTransportUnit, t, crucibleOutpostUnit(o));
        xsArraySetInt(crucibleOutpostTransportCount, t, carry);
        xsArraySetInt(crucibleOutpostTransportState, t, 1);
        xsArraySetInt(crucibleOutpostTransportTime, t, xsGetTime());
        xsArraySetInt(crucibleOutpostTransportMarker, t, marker);
        xsArraySetInt(crucibleOutpostTransportLanding, t, landing);
        crucibleOutpostTaskOne(id, cActionTypeMove, crucibleOutpostLandingWater(landing));
        left = left - carry;
        sent++;
    }

    for (e = 0; < cCrucibleOutpostEscorts) {
        if ((lead < 0) || (made >= escorts) || (xsArrayGetInt(crucibleOutpostEscort, e) >= 0)) {
            continue;
        }

        id = xsCreateUnit(crucibleOutpostShipUnit(o), cCrucibleOutpostLegion, crucibleOutpostSeaSpawn(marker), false,
            false, false);

        if (id < 0) {
            continue;
        }

        xsArraySetInt(crucibleOutpostEscort, e, id);
        xsArraySetInt(crucibleOutpostEscortLead, e, lead);
        xsArraySetInt(crucibleOutpostEscortMarker, e, marker);
        xsArraySetInt(crucibleOutpostEscortLanding, e, landing);
        xsArraySetInt(crucibleOutpostEscortState, e, 1);
        xsArraySetInt(crucibleOutpostEscortTime, e, xsGetTime());
        crucibleOutpostTaskOne(id, cActionTypeAttackMove, crucibleOutpostLandingWater(landing));
        made++;
    }

    crucibleOutpostSay(o, "attack wave of " + (size - left) + " in " + sent + " transports, " + made + " escorts, to "
        + "the landing at " + xsArrayGetFloat(crucibleOutpostLandingX, landing) + ", "
        + xsArrayGetFloat(crucibleOutpostLandingY, landing));
}

// 1 sailing in, 2 gone or sailing off (landed or sunk), for the transport with id `lead`.
int crucibleOutpostLeadState(int lead = -1) {
    for (t = 0; < cCrucibleOutpostTransportMax) {
        if (xsArrayGetInt(crucibleOutpostTransport, t) == lead) {
            return (xsArrayGetInt(crucibleOutpostTransportState, t));
        }
    }

    return (2);
}

// Transports at their landing land their party (made there: no real unload works) and sail back to their sea marker,
// where a trigger removes them; their escorts go back with them. Sunk, the party's lost.
void crucibleOutpostTransports() {
    int id = -1;
    int o = 0;
    int now = xsGetTime();
    int count = 0;
    int unit = -1;
    int n = 0;
    int made = -1;
    int landing = 0;
    vector at = cInvalidVector;
    vector water = cInvalidVector;
    vector ground = cInvalidVector;
    float r2 = cCrucibleOutpostLanded * cCrucibleOutpostLanded;

    for (t = 0; < cCrucibleOutpostTransportMax) {
        id = xsArrayGetInt(crucibleOutpostTransport, t);

        if (id < 0) {
            continue;
        }

        if (crucibleOutpostHp(id) <= 0.0) {
            xsArraySetInt(crucibleOutpostTransport, t, -1);
            continue;
        }

        o = xsArrayGetInt(crucibleOutpostTransportOutpost, t);
        landing = xsArrayGetInt(crucibleOutpostTransportLanding, t);

        if (xsArrayGetInt(crucibleOutpostTransportState, t) == 2) {
            if (now - xsArrayGetInt(crucibleOutpostTransportTime, t) >= cCrucibleOutpostLandTimeout) {
                xsArraySetInt(crucibleOutpostTransport, t, -1);  // the trigger at its marker takes it off the map
            }

            continue;
        }

        at = xsGetUnitPosition(id);
        water = crucibleOutpostLandingWater(landing);

        if ((crucibleOutpostDist2(xsVectorGetX(at), xsVectorGetY(at), xsVectorGetX(water), xsVectorGetY(water)) > r2)
            && (now - xsArrayGetInt(crucibleOutpostTransportTime, t) < cCrucibleOutpostLandTimeout)) {
            continue;
        }

        count = xsArrayGetInt(crucibleOutpostTransportCount, t);
        unit = xsArrayGetInt(crucibleOutpostTransportUnit, t);
        ground = crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostLandingX, landing),
            xsArrayGetFloat(crucibleOutpostLandingY, landing));
        xsArrayResizeInt(crucibleOutpostFound, count + 1);
        n = 0;

        for (k = 0; < count) {
            made = xsCreateUnit(unit, cCrucibleOutpostLegion, ground, false, false, false);

            if (made >= 0) {
                xsArraySetInt(crucibleOutpostFound, n, made);
                n++;
            }
        }

        if (n > 0) {
            xsArrayResizeInt(crucibleOutpostFound, n);
            xsTaskUnits(crucibleOutpostFound, cActionTypeAttackMove, crucibleOutpostWonder());
        }

        crucibleOutpostSay(o, "a transport lands " + n);
        xsArraySetInt(crucibleOutpostTransportState, t, 2);
        xsArraySetInt(crucibleOutpostTransportTime, t, now);
        crucibleOutpostTaskOne(id, cActionTypeMove, crucibleOutpostSeaExit(xsArrayGetInt(crucibleOutpostTransportMarker,
            t)));
    }

    for (e = 0; < cCrucibleOutpostEscorts) {
        id = xsArrayGetInt(crucibleOutpostEscort, e);

        if (id < 0) {
            continue;
        }

        if (crucibleOutpostHp(id) <= 0.0) {
            xsArraySetInt(crucibleOutpostEscort, e, -1);
            continue;
        }

        if (xsArrayGetInt(crucibleOutpostEscortState, e) == 2) {
            if (now - xsArrayGetInt(crucibleOutpostEscortTime, e) >= cCrucibleOutpostLandTimeout) {
                xsArraySetInt(crucibleOutpostEscort, e, -1);
            }

            continue;
        }

        if ((crucibleOutpostLeadState(xsArrayGetInt(crucibleOutpostEscortLead, e)) == 2)
            || (now - xsArrayGetInt(crucibleOutpostEscortTime, e) >= cCrucibleOutpostLandTimeout)) {
            xsArraySetInt(crucibleOutpostEscortState, e, 2);
            xsArraySetInt(crucibleOutpostEscortTime, e, now);
            crucibleOutpostTaskOne(id, cActionTypeMove, crucibleOutpostSeaExit(xsArrayGetInt(crucibleOutpostEscortMarker,
                e)));
        }
    }
}

// ---- turns ----

int crucibleOutpostSpotWanted(int spot = 0) {
    return (crucibleOutpostScaled(xsArrayGetInt(crucibleOutpostSpotGuards, spot) + crucibleWaveAge, 1));
}

// Its spot with the player on it, the most pressured; -1 if none.
int crucibleOutpostContested(int o = 0) {
    int best = -1;

    for (s = 0; < cCrucibleOutpostSpots) {
        if ((xsArrayGetInt(crucibleOutpostSpotOwner, s) != o) || (xsArrayGetInt(crucibleOutpostSpotContest, s) <= 0)) {
            continue;
        }

        if ((best < 0) || (xsArrayGetInt(crucibleOutpostSpotPressure, s) > xsArrayGetInt(crucibleOutpostSpotPressure,
            best))) {
            best = s;
        }
    }

    return (best);
}

// Its spot with fewer guards than it wants; -1 if none.
int crucibleOutpostUnguarded(int o = 0) {
    for (s = 0; < cCrucibleOutpostSpots) {
        if (xsArrayGetInt(crucibleOutpostSpotOwner, s) != o) {
            continue;
        }

        if (crucibleOutpostMemberCount(o, 2, s) < crucibleOutpostSpotWanted(s)) {
            return (s);
        }
    }

    return (-1);
}

void crucibleOutpostTurn(int o = 0) {
    int spot = -1;
    int size = 0;
    int made = 0;
    string where = "";

    if (crucibleOutpostTurtled(o)) {
        xsArraySetInt(crucibleOutpostGrowth, o, xsArrayGetInt(crucibleOutpostGrowth, o) + cCrucibleOutpostGrowHarassed);

        if (crucibleOutpostPlayerNear(o)) {
            crucibleOutpostSay(o, "turtled, defends: " + crucibleOutpostCount(o) + " defenders, "
                + crucibleOutpostShipCount(o) + " ships");
        } else {
            crucibleOutpostSay(o, "turtled, bolsters: " + crucibleOutpostCount(o) + " defenders, "
                + crucibleOutpostShipCount(o) + " ships, of " + crucibleOutpostLandTarget(o) + " and "
                + crucibleOutpostShipTarget(o));
        }

        return;
    }

    xsArraySetInt(crucibleOutpostGrowth, o, xsArrayGetInt(crucibleOutpostGrowth, o) + cCrucibleOutpostGrow);

    if (crucibleOutpostPlayerNear(o)) {
        crucibleOutpostSay(o, "the player is near: makes nothing");
        return;
    }

    made = crucibleOutpostTopUp(o, cCrucibleOutpostSpawnPerTick);
    crucibleOutpostSay(o, "+" + made + ": " + crucibleOutpostCount(o) + " defenders, " + crucibleOutpostShipCount(o)
        + " ships");
    spot = crucibleOutpostContested(o);

    if (spot >= 0) {
        size = cCrucibleOutpostBullyBase + xsArrayGetInt(crucibleOutpostSpotPressure, spot) * cCrucibleOutpostBullyPer
            + crucibleWaveAge;
        size = crucibleOutpostCap(crucibleOutpostScaled(size, 1), cCrucibleOutpostBullyMax);
        size = crucibleOutpostCap(size, cCrucibleOutpostSpotMax - crucibleOutpostMemberCount(o, 2, spot));
        made = crucibleOutpostGuard(o, spot, size);
        where = xsArrayGetString(crucibleOutpostSpotName, spot);
        crucibleOutpostSay(o, "the player is on " + where + ": sends " + made);
        return;
    }

    spot = crucibleOutpostUnguarded(o);

    if (spot >= 0) {
        size = crucibleOutpostSpotWanted(spot) - crucibleOutpostMemberCount(o, 2, spot);
        made = crucibleOutpostGuard(o, spot, size);
        where = xsArrayGetString(crucibleOutpostSpotName, spot);
        crucibleOutpostSay(o, "guards " + where + " with " + made + " more");
        return;
    }

    if (crucibleOutpostSea(o)) {
        crucibleOutpostSeaWave(o, crucibleOutpostWaveSize(o));
        return;
    }

    crucibleOutpostLandWave(o, crucibleOutpostWaveSize(o));
}

// ---- every second ----

// Outpost o's buildings, garrison and ships: hit? destroyed? Its turn, its turtled top-ups.
void crucibleOutpostWatch(int o = 0) {
    int now = xsGetTime();
    float total = 0.0;
    float hp = 0.0;
    int id = -1;
    int k = 0;
    int role = 0;
    bool hit = false;

    for (b = xsArrayGetInt(crucibleOutpostBuildingStart, o); < xsArrayGetInt(crucibleOutpostBuildingStart, o + 1)) {
        id = xsArrayGetInt(crucibleOutpostBuildings, b);
        hp = crucibleOutpostHp(id);
        total = total + hp;

        if (hp < xsArrayGetFloat(crucibleOutpostBuildingHp, b) - 0.5) {
            hit = true;
        }

        xsArraySetFloat(crucibleOutpostBuildingHp, b, hp);
    }

    if (total <= 0.0) {
        xsArraySetInt(crucibleOutpostAlive, o, 0);
        crucibleOutpostSay(o, "destroyed, no more turns");
        return;
    }

    for (m = 0; < cCrucibleOutpostMembers) {
        k = o * cCrucibleOutpostMembers + m;
        id = xsArrayGetInt(crucibleOutpostMemberId, k);

        if (id < 0) {
            continue;
        }

        hp = crucibleOutpostHp(id);
        role = xsArrayGetInt(crucibleOutpostMemberRole, k);

        if ((role != 2) && (hp < xsArrayGetFloat(crucibleOutpostMemberHp, k) - 0.5)) {
            hit = true;  // spot guards fight away from home
        }

        if (hp <= 0.0) {
            xsArraySetInt(crucibleOutpostMemberId, k, -1);
        }

        xsArraySetFloat(crucibleOutpostMemberHp, k, hp);
    }

    if (hit) {
        if (crucibleOutpostTurtled(o) == false) {
            crucibleOutpostSay(o, "harassed: turtles");
            xsArraySetInt(crucibleOutpostTurtleSpawn, o, now + cCrucibleOutpostTurtleSpawnEvery);
        }

        xsArraySetInt(crucibleOutpostHarassedAt, o, now);
    }

    if (crucibleOutpostTurtled(o) && (now >= xsArrayGetInt(crucibleOutpostTurtleSpawn, o))) {
        xsArraySetInt(crucibleOutpostTurtleSpawn, o, now + cCrucibleOutpostTurtleSpawnEvery);

        if (crucibleOutpostPlayerNear(o) == false) {
            crucibleOutpostTopUp(o, cCrucibleOutpostTurtleSpawn);
        }
    }

    if (now >= xsArrayGetInt(crucibleOutpostNextTurn, o)) {
        xsArraySetInt(crucibleOutpostNextTurn, o, now + (cCrucibleOutpostTick
            + xsGetRandomNumberLH(0, cCrucibleOutpostTickSpread)) * 100
            / xsArrayGetInt(crucibleOutpostAggression, crucibleWaveDifficulty));
        crucibleOutpostTurn(o);
    }
}

rule crucibleOutpostStart
    active
    minInterval 1
{
    int size = 0;

    if (xsGetTime() < cCrucibleOutpostStart) {
        return;
    }

    crucibleOutpostData();
    size = cCrucibleOutposts * cCrucibleOutpostMembers;
    crucibleOutpostBuildingHp = xsArrayCreateFloat(xsArrayGetSize(crucibleOutpostBuildings), 0.0,
        "crucibleOutpostBuildingHp");
    crucibleOutpostArchetype = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostArchetype");
    crucibleOutpostGrowth = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostGrowth");
    crucibleOutpostAlive = xsArrayCreateInt(cCrucibleOutposts, 1, "crucibleOutpostAlive");
    crucibleOutpostNextTurn = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostNextTurn");
    crucibleOutpostHarassedAt = xsArrayCreateInt(cCrucibleOutposts, -1, "crucibleOutpostHarassedAt");
    crucibleOutpostTurtleSpawn = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostTurtleSpawn");
    crucibleOutpostHunting = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostHunting");
    crucibleOutpostHuntX = xsArrayCreateFloat(cCrucibleOutposts, 0.0, "crucibleOutpostHuntX");
    crucibleOutpostHuntY = xsArrayCreateFloat(cCrucibleOutposts, 0.0, "crucibleOutpostHuntY");
    crucibleOutpostShipsOut = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostShipsOut");
    crucibleOutpostShipX = xsArrayCreateFloat(cCrucibleOutposts, 0.0, "crucibleOutpostShipX");
    crucibleOutpostShipY = xsArrayCreateFloat(cCrucibleOutposts, 0.0, "crucibleOutpostShipY");
    crucibleOutpostSpawned = xsArrayCreateInt(cCrucibleOutposts, 0, "crucibleOutpostSpawned");
    crucibleOutpostMemberId = xsArrayCreateInt(size, -1, "crucibleOutpostMemberId");
    crucibleOutpostMemberType = xsArrayCreateInt(size, -1, "crucibleOutpostMemberType");
    crucibleOutpostMemberRole = xsArrayCreateInt(size, 0, "crucibleOutpostMemberRole");
    crucibleOutpostMemberAnchor = xsArrayCreateInt(size, 0, "crucibleOutpostMemberAnchor");
    crucibleOutpostMemberPatrol = xsArrayCreateInt(size, 0, "crucibleOutpostMemberPatrol");
    crucibleOutpostMemberLeg = xsArrayCreateInt(size, 0, "crucibleOutpostMemberLeg");
    crucibleOutpostMemberNext = xsArrayCreateInt(size, 0, "crucibleOutpostMemberNext");
    crucibleOutpostMemberHp = xsArrayCreateFloat(size, 0.0, "crucibleOutpostMemberHp");
    crucibleOutpostMemberX = xsArrayCreateFloat(size, 0.0, "crucibleOutpostMemberX");
    crucibleOutpostMemberY = xsArrayCreateFloat(size, 0.0, "crucibleOutpostMemberY");
    crucibleOutpostEnemyId = xsArrayCreateInt(cCrucibleOutpostEnemyMax, -1, "crucibleOutpostEnemyId");
    crucibleOutpostEnemyX = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostEnemyX");
    crucibleOutpostEnemyY = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostEnemyY");
    crucibleOutpostSeaId = xsArrayCreateInt(cCrucibleOutpostEnemyMax, -1, "crucibleOutpostSeaId");
    crucibleOutpostSeaX = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostSeaX");
    crucibleOutpostSeaY = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostSeaY");
    crucibleOutpostSpotContest = xsArrayCreateInt(cCrucibleOutpostSpots + 1, 0, "crucibleOutpostSpotContest");
    crucibleOutpostSpotPressure = xsArrayCreateInt(cCrucibleOutpostSpots + 1, 0, "crucibleOutpostSpotPressure");
    crucibleOutpostTransport = xsArrayCreateInt(cCrucibleOutpostTransportMax, -1, "crucibleOutpostTransport");
    crucibleOutpostTransportOutpost = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportOutpost");
    crucibleOutpostTransportUnit = xsArrayCreateInt(cCrucibleOutpostTransportMax, -1, "crucibleOutpostTransportUnit");
    crucibleOutpostTransportCount = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportCount");
    crucibleOutpostTransportState = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportState");
    crucibleOutpostTransportTime = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportTime");
    crucibleOutpostTransportMarker = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportMarker");
    crucibleOutpostTransportLanding = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0,
        "crucibleOutpostTransportLanding");
    crucibleOutpostEscort = xsArrayCreateInt(cCrucibleOutpostEscorts, -1, "crucibleOutpostEscort");
    crucibleOutpostEscortLead = xsArrayCreateInt(cCrucibleOutpostEscorts, -1, "crucibleOutpostEscortLead");
    crucibleOutpostEscortMarker = xsArrayCreateInt(cCrucibleOutpostEscorts, 0, "crucibleOutpostEscortMarker");
    crucibleOutpostEscortLanding = xsArrayCreateInt(cCrucibleOutpostEscorts, 0, "crucibleOutpostEscortLanding");
    crucibleOutpostEscortState = xsArrayCreateInt(cCrucibleOutpostEscorts, 0, "crucibleOutpostEscortState");
    crucibleOutpostEscortTime = xsArrayCreateInt(cCrucibleOutpostEscorts, 0, "crucibleOutpostEscortTime");
    crucibleOutpostFound = xsArrayCreateInt(1, -1, "crucibleOutpostFound");
    crucibleOutpostIds = xsArrayCreateInt(1, -1, "crucibleOutpostIds");

    for (b = 0; < xsArrayGetSize(crucibleOutpostBuildings)) {
        xsArraySetFloat(crucibleOutpostBuildingHp, b, crucibleOutpostHp(xsArrayGetInt(crucibleOutpostBuildings, b)));
    }

    for (o = 0; < cCrucibleOutposts) {
        xsArraySetInt(crucibleOutpostArchetype, o, xsGetRandomNumberLH(0, cCrucibleOutpostArchetypes));
        xsArraySetInt(crucibleOutpostNextTurn, o, cCrucibleOutpostFirstTick
            + xsGetRandomNumberLH(0, cCrucibleOutpostTickSpread / 2));
        crucibleOutpostTopUp(o, cCrucibleOutpostMax + cCrucibleOutpostShipMax);
        crucibleOutpostSay(o, "starts with " + crucibleOutpostCount(o) + " defenders, " + crucibleOutpostShipCount(o)
            + " ships");
    }

    xsEnableRule("crucibleOutposts");
    xsDisableSelf();
}

rule crucibleOutposts
    inactive
    minInterval 1
{
    int now = xsGetTime();
    bool scan = false;

    if (now >= crucibleOutpostNextScan) {
        crucibleOutpostNextScan = now + cCrucibleOutpostScanEvery;
        crucibleOutpostScan();
        scan = true;
    }

    if (now >= crucibleOutpostNextPressure) {
        crucibleOutpostNextPressure = now + cCrucibleOutpostPressureEvery;

        for (s = 0; < cCrucibleOutpostSpots) {
            if (xsArrayGetInt(crucibleOutpostSpotContest, s) > 0) {
                if (xsArrayGetInt(crucibleOutpostSpotPressure, s) < cCrucibleOutpostPressureMax) {
                    xsArraySetInt(crucibleOutpostSpotPressure, s, xsArrayGetInt(crucibleOutpostSpotPressure, s) + 1);
                }
            } else if (xsArrayGetInt(crucibleOutpostSpotPressure, s) > 0) {
                xsArraySetInt(crucibleOutpostSpotPressure, s, xsArrayGetInt(crucibleOutpostSpotPressure, s) - 1);
            }
        }
    }

    for (o = 0; < cCrucibleOutposts) {
        if (xsArrayGetInt(crucibleOutpostAlive, o) != 1) {
            continue;
        }

        crucibleOutpostWatch(o);

        if (scan && (xsArrayGetInt(crucibleOutpostAlive, o) == 1)) {
            crucibleOutpostOrders(o);
        }
    }

    crucibleOutpostTransports();
}
