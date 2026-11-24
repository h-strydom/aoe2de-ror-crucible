// ---- crucible run: the Legion's outposts, runtime (scenarios/outposts.xs; the generated data block comes first) ----
// docs/outposts.md. Each outpost keeps a garrison spread over posts through its base (sea outposts: half of it ships
// round the island) and takes a turn every few minutes: it grows, tops up its garrison, then bullies a contested spot,
// guards one of its own, helps at another's, raids the player's gatherers outside the base, or sends an attack wave
// (land: from its marker on the south edge; sea: by transport from its markers to a beach, faked landing). Hit, it
// turtles: its parties come home, its garrison hunts the player's units near the base and swells while turtled.
// The player's units are known by type every few seconds (crucibleOutpostScan): the map hack.

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
int crucibleOutpostSpawned = -1;  // by outpost: units spawned (spreads them over the posts)
int crucibleOutpostBuildingHp = -1;  // by building: its HP last second
int crucibleOutpostDefenders = -1;  // by outpost * cCrucibleOutpostMax: unit ids, -1 a free place
int crucibleOutpostDefenderHp = -1;
int crucibleOutpostShips = -1;  // by outpost * cCrucibleOutpostShipMax
int crucibleOutpostShipHp = -1;
int crucibleOutpostOut = -1;  // by outpost * cCrucibleOutpostOutMax: units out (guards, bullies, raiders)
int crucibleOutpostOutKind = -1;  // 1 guard, 2 bully, 3 raider, 4 coming home
int crucibleOutpostOutSpot = -1;
int crucibleOutpostOutX = -1;  // where it was last sent
int crucibleOutpostOutY = -1;
int crucibleOutpostEnemyId = -1;  // the player's land units, as last scanned
int crucibleOutpostEnemyX = -1;
int crucibleOutpostEnemyY = -1;
int crucibleOutpostEnemyVillager = -1;
int crucibleOutpostEnemyCount = 0;
int crucibleOutpostSeaId = -1;  // the player's ships and docks
int crucibleOutpostSeaX = -1;
int crucibleOutpostSeaY = -1;
int crucibleOutpostSeaCount = 0;
int crucibleOutpostSpotContest = -1;  // by spot: the player's units on it
int crucibleOutpostSpotPressure = -1;  // by spot: up while contested, down while clear
int crucibleOutpostSpotGuards = -1;  // by spot: outpost units guarding or bullying it
int crucibleOutpostTransport = -1;  // by transport: unit id, -1 free
int crucibleOutpostTransportOutpost = -1;
int crucibleOutpostTransportUnit = -1;  // the type it lands
int crucibleOutpostTransportCount = -1;  // how many it lands
int crucibleOutpostTransportState = -1;  // 1 sailing in, 2 sailing off
int crucibleOutpostTransportTime = -1;
int crucibleOutpostTransportMarker = -1;  // 0 or 1: which of its outpost's markers it came from
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
                    xsArraySetInt(crucibleOutpostEnemyVillager, n, xsArrayGetInt(crucibleOutpostLandVillager, t));
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

// The player's units and ships, each spot's contest and guards.
void crucibleOutpostScan() {
    int k = 0;
    int spot = -1;
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
        xsArraySetInt(crucibleOutpostSpotGuards, s, 0);
    }

    for (o = 0; < cCrucibleOutposts) {
        for (d = 0; < cCrucibleOutpostOutMax) {
            k = o * cCrucibleOutpostOutMax + d;

            if (xsArrayGetInt(crucibleOutpostOut, k) < 0) {
                continue;
            }

            if (xsArrayGetInt(crucibleOutpostOutKind, k) <= 2) {
                spot = xsArrayGetInt(crucibleOutpostOutSpot, k);
                xsArraySetInt(crucibleOutpostSpotGuards, spot, xsArrayGetInt(crucibleOutpostSpotGuards, spot) + 1);
            }
        }
    }
}

// The player's land unit nearest (x, y) within `range` (villagers only, outside the player's base only); -1 if none.
int crucibleOutpostNearest(float x = 0.0, float y = 0.0, float range = 0.0, bool villagers = false,
    bool outside = false) {
    int best = -1;
    float bestD = range * range;
    float base2 = cCrucibleOutpostBaseRadius * cCrucibleOutpostBaseRadius;
    float ex = 0.0;
    float ey = 0.0;
    float d = 0.0;

    for (e = 0; < crucibleOutpostEnemyCount) {
        if (villagers && (xsArrayGetInt(crucibleOutpostEnemyVillager, e) == 0)) {
            continue;
        }

        ex = xsArrayGetFloat(crucibleOutpostEnemyX, e);
        ey = xsArrayGetFloat(crucibleOutpostEnemyY, e);

        if (outside && (crucibleOutpostDist2(ex, ey, cCrucibleOutpostWonderX, cCrucibleOutpostWonderY) < base2)) {
            continue;
        }

        d = crucibleOutpostDist2(x, y, ex, ey);

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

// ---- units ----

int crucibleOutpostBase(int o = 0) {
    int base = cCrucibleOutpostStartDefenders + crucibleOutpostLevel(o) / cCrucibleOutpostLevelsPerDefender;

    return (base + crucibleWaveAge * cCrucibleOutpostDefendersPerAge
        + (crucibleWaveFactor - 1) * cCrucibleOutpostDifficultyDefenders);
}

// Its garrison: land units and ships (half, at sea), larger while turtled.
int crucibleOutpostTarget(int o = 0) {
    int target = crucibleOutpostBase(o) * cCrucibleOutpostGarrisonScale;

    if (crucibleOutpostTurtled(o)) {
        target = crucibleOutpostBase(o) * cCrucibleOutpostTurtleScale;
    }

    return (target);
}

int crucibleOutpostLandTarget(int o = 0) {
    int target = crucibleOutpostTarget(o);

    if (crucibleOutpostSea(o)) {
        target = target - target / 2;
    }

    if (target > cCrucibleOutpostMax) {
        return (cCrucibleOutpostMax);
    }

    return (target);
}

int crucibleOutpostShipTarget(int o = 0) {
    int target = 0;

    if (crucibleOutpostSea(o)) {
        target = crucibleOutpostTarget(o) / 2;
    }

    if (target > cCrucibleOutpostShipMax) {
        return (cCrucibleOutpostShipMax);
    }

    return (target);
}

int crucibleOutpostCountIn(int ids = -1, int o = 0, int size = 0) {
    int found = 0;

    for (d = 0; < size) {
        if (xsArrayGetInt(ids, o * size + d) >= 0) {
            found++;
        }
    }

    return (found);
}

int crucibleOutpostCount(int o = 0) {
    return (crucibleOutpostCountIn(crucibleOutpostDefenders, o, cCrucibleOutpostMax));
}

int crucibleOutpostShipCount(int o = 0) {
    return (crucibleOutpostCountIn(crucibleOutpostShips, o, cCrucibleOutpostShipMax));
}

// Its archetype's unit at the Legion's age: later lines with level; the main slot most of the time.
int crucibleOutpostUnit(int o = 0) {
    int slot = xsArrayGetInt(crucibleOutpostMain, xsArrayGetInt(crucibleOutpostArchetype, o));
    int k = 0;
    int start = 0;
    int count = 0;
    int pick = crucibleOutpostLevel(o) / cCrucibleOutpostLevelsPerLine + crucibleWaveAge;

    if (xsGetRandomNumberLH(0, 100) >= cCrucibleOutpostMainShare) {
        slot = 1 - slot;
    }

    for (tries = 0; < 2) {
        k = (xsArrayGetInt(crucibleOutpostArchetype, o) * 2 + slot) * cCrucibleOutpostAges + crucibleWaveAge;
        start = xsArrayGetInt(crucibleOutpostPoolStart, k);
        count = xsArrayGetInt(crucibleOutpostPoolStart, k + 1) - start;

        if (count > 0) {
            if (pick > count - 1) {
                pick = count - 1;
            }

            return (xsArrayGetInt(crucibleOutpostPoolUnits, start + pick));
        }

        slot = 1 - slot;
    }

    return (-1);
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

vector crucibleOutpostPost(int o = 0, int p = 0) {
    int k = o * cCrucibleOutpostPosts + p % cCrucibleOutpostPosts;

    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostPostX, k), xsArrayGetFloat(crucibleOutpostPostY, k)));
}

vector crucibleOutpostSeaPost(int o = 0, int p = 0) {
    int k = o * cCrucibleOutpostSeaPosts + p % cCrucibleOutpostSeaPosts;

    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostSeaPostX, k), xsArrayGetFloat(crucibleOutpostSeaPostY, k)));
}

// A unit at the next post (spread through the base); its id.
int crucibleOutpostCreate(int o = 0, int unit = -1) {
    int n = xsArrayGetInt(crucibleOutpostSpawned, o);

    xsArraySetInt(crucibleOutpostSpawned, o, n + 1);

    if (unit < 0) {
        return (-1);
    }

    return (xsCreateUnit(unit, cCrucibleOutpostLegion, crucibleOutpostPost(o, n), false, false, false));
}

bool crucibleOutpostSpawnDefender(int o = 0) {
    int k = 0;
    int id = -1;

    for (d = 0; < cCrucibleOutpostMax) {
        k = o * cCrucibleOutpostMax + d;

        if (xsArrayGetInt(crucibleOutpostDefenders, k) < 0) {
            id = xsCreateUnit(crucibleOutpostUnit(o), cCrucibleOutpostLegion, crucibleOutpostPost(o, d), false, false,
                false);

            if (id < 0) {
                return (false);
            }

            xsArraySetInt(crucibleOutpostDefenders, k, id);
            xsArraySetFloat(crucibleOutpostDefenderHp, k, crucibleOutpostHp(id));
            return (true);
        }
    }

    return (false);
}

bool crucibleOutpostSpawnShip(int o = 0) {
    int k = 0;
    int id = -1;

    for (d = 0; < cCrucibleOutpostShipMax) {
        k = o * cCrucibleOutpostShipMax + d;

        if (xsArrayGetInt(crucibleOutpostShips, k) < 0) {
            id = xsCreateUnit(crucibleOutpostShipUnit(o), cCrucibleOutpostLegion, crucibleOutpostSeaPost(o, d), false,
                false, false);

            if (id < 0) {
                return (false);
            }

            xsArraySetInt(crucibleOutpostShips, k, id);
            xsArraySetFloat(crucibleOutpostShipHp, k, crucibleOutpostHp(id));
            return (true);
        }
    }

    return (false);
}

// Up to `most` more of its garrison, land and ships in turn; how many came.
int crucibleOutpostTopUp(int o = 0, int most = 0) {
    int land = crucibleOutpostLandTarget(o) - crucibleOutpostCount(o);
    int ships = crucibleOutpostShipTarget(o) - crucibleOutpostShipCount(o);
    int made = 0;

    while ((made < most) && ((land > 0) || (ships > 0))) {
        if (land > 0) {
            if (crucibleOutpostSpawnDefender(o) == false) {
                land = 0;
            } else {
                land--;
                made++;
            }
        }

        if ((ships > 0) && (made < most)) {
            if (crucibleOutpostSpawnShip(o) == false) {
                ships = 0;
            } else {
                ships--;
                made++;
            }
        }
    }

    return (made);
}

// Every unit of `ids` (outpost o's part) attack-moves to `at`.
void crucibleOutpostSendAll(int ids = -1, int o = 0, int size = 0, vector at = cInvalidVector) {
    int n = 0;
    int id = -1;

    for (d = 0; < size) {
        if (xsArrayGetInt(ids, o * size + d) >= 0) {
            n++;
        }
    }

    if (n == 0) {
        return;
    }

    xsArrayResizeInt(crucibleOutpostIds, n);
    n = 0;

    for (d = 0; < size) {
        id = xsArrayGetInt(ids, o * size + d);

        if (id >= 0) {
            xsArraySetInt(crucibleOutpostIds, n, id);
            n++;
        }
    }

    xsTaskUnits(crucibleOutpostIds, cActionTypeAttackMove, at);
}

// Its garrison back to its posts, its ships to theirs.
void crucibleOutpostToPosts(int o = 0) {
    int id = -1;

    for (d = 0; < cCrucibleOutpostMax) {
        id = xsArrayGetInt(crucibleOutpostDefenders, o * cCrucibleOutpostMax + d);

        if (id >= 0) {
            crucibleOutpostTaskOne(id, cActionTypeAttackMove, crucibleOutpostPost(o, d));
        }
    }

    for (d = 0; < cCrucibleOutpostShipMax) {
        id = xsArrayGetInt(crucibleOutpostShips, o * cCrucibleOutpostShipMax + d);

        if (id >= 0) {
            crucibleOutpostTaskOne(id, cActionTypeAttackMove, crucibleOutpostSeaPost(o, d));
        }
    }
}

// ---- parties: guards, bullies, raiders ----

int crucibleOutpostOutAdd(int o = 0, int id = -1, int kind = 0, int spot = -1) {
    int k = 0;

    for (d = 0; < cCrucibleOutpostOutMax) {
        k = o * cCrucibleOutpostOutMax + d;

        if (xsArrayGetInt(crucibleOutpostOut, k) < 0) {
            xsArraySetInt(crucibleOutpostOut, k, id);
            xsArraySetInt(crucibleOutpostOutKind, k, kind);
            xsArraySetInt(crucibleOutpostOutSpot, k, spot);
            xsArraySetFloat(crucibleOutpostOutX, k, -100.0);
            xsArraySetFloat(crucibleOutpostOutY, k, -100.0);
            return (k);
        }
    }

    return (-1);
}

int crucibleOutpostOutCount(int o = 0) {
    return (crucibleOutpostCountIn(crucibleOutpostOut, o, cCrucibleOutpostOutMax));
}

// `size` new units at its posts, out as `kind` for `spot`, attack-moving to `to`; how many went.
int crucibleOutpostParty(int o = 0, int size = 0, int kind = 0, int spot = -1, vector to = cInvalidVector) {
    int id = -1;
    int made = 0;

    for (n = 0; < size) {
        id = crucibleOutpostCreate(o, crucibleOutpostUnit(o));

        if (id >= 0) {
            if (crucibleOutpostOutAdd(o, id, kind, spot) >= 0) {
                crucibleOutpostTaskOne(id, cActionTypeAttackMove, to);
                made++;
            } else {
                xsSetUnitProperty(id, cUnitHitpoints, 0.0);
            }
        }
    }

    return (made);
}

// Harassed: everyone out comes home and joins the garrison (if there's room).
void crucibleOutpostRecall(int o = 0) {
    int k = 0;
    int id = -1;
    int slot = -1;

    for (d = 0; < cCrucibleOutpostOutMax) {
        k = o * cCrucibleOutpostOutMax + d;
        id = xsArrayGetInt(crucibleOutpostOut, k);

        if (id < 0) {
            continue;
        }

        xsArraySetInt(crucibleOutpostOut, k, -1);

        if (crucibleOutpostHp(id) <= 0.0) {
            continue;
        }

        slot = -1;

        for (g = 0; < cCrucibleOutpostMax) {
            if ((slot < 0) && (xsArrayGetInt(crucibleOutpostDefenders, o * cCrucibleOutpostMax + g) < 0)) {
                slot = o * cCrucibleOutpostMax + g;
            }
        }

        if (slot >= 0) {
            xsArraySetInt(crucibleOutpostDefenders, slot, id);
            xsArraySetFloat(crucibleOutpostDefenderHp, slot, crucibleOutpostHp(id));
        }

        crucibleOutpostTaskOne(id, cActionTypeAttackMove, crucibleOutpostAt(crucibleOutpostHomeX(o),
            crucibleOutpostHomeY(o)));
    }
}

// Sends `id` (out entry k) to (x, y) unless it was sent near there already.
void crucibleOutpostOutSend(int k = 0, int id = -1, float x = 0.0, float y = 0.0) {
    if (crucibleOutpostDist2(x, y, xsArrayGetFloat(crucibleOutpostOutX, k), xsArrayGetFloat(crucibleOutpostOutY, k))
        < 9.0) {
        return;
    }

    xsArraySetFloat(crucibleOutpostOutX, k, x);
    xsArraySetFloat(crucibleOutpostOutY, k, y);
    crucibleOutpostTaskOne(id, cActionTypeAttackMove, crucibleOutpostAt(x, y));
}

// Its parties: guards stand on their spot and fight whoever comes; bullies chase the player off it, then guard it;
// raiders chase gatherers outside the player's base, then come home.
void crucibleOutpostManageOut(int o = 0) {
    int k = 0;
    int id = -1;
    int kind = 0;
    int spot = -1;
    int e = -1;
    float sx = 0.0;
    float sy = 0.0;
    float hx = crucibleOutpostHomeX(o);
    float hy = crucibleOutpostHomeY(o);
    float leash = cCrucibleOutpostHelpRange * cCrucibleOutpostHelpRange * 2.25;
    float chase = cCrucibleOutpostSpotRadius + 4.0;
    vector at = cInvalidVector;

    for (d = 0; < cCrucibleOutpostOutMax) {
        k = o * cCrucibleOutpostOutMax + d;
        id = xsArrayGetInt(crucibleOutpostOut, k);

        if (id < 0) {
            continue;
        }

        if (crucibleOutpostHp(id) <= 0.0) {
            xsArraySetInt(crucibleOutpostOut, k, -1);
            continue;
        }

        kind = xsArrayGetInt(crucibleOutpostOutKind, k);
        spot = xsArrayGetInt(crucibleOutpostOutSpot, k);
        at = xsGetUnitPosition(id);

        if (kind <= 2) {
            sx = xsArrayGetFloat(crucibleOutpostSpotX, spot);
            sy = xsArrayGetFloat(crucibleOutpostSpotY, spot);
            e = -1;

            if (xsArrayGetInt(crucibleOutpostSpotContest, spot) > 0) {
                e = crucibleOutpostNearest(sx, sy, chase, false, false);
            }

            if (e >= 0) {
                crucibleOutpostOutSend(k, id, xsArrayGetFloat(crucibleOutpostEnemyX, e),
                    xsArrayGetFloat(crucibleOutpostEnemyY, e));
            } else {
                xsArraySetInt(crucibleOutpostOutKind, k, 1);  // a bully with nobody left to chase guards the spot
                crucibleOutpostOutSend(k, id, sx, sy);
            }
        } else if (kind == 3) {
            e = -1;

            if (crucibleOutpostDist2(xsVectorGetX(at), xsVectorGetY(at), hx, hy) < leash) {
                e = crucibleOutpostNearest(xsVectorGetX(at), xsVectorGetY(at), cCrucibleOutpostHelpRange, true, true);
            }

            if (e >= 0) {
                crucibleOutpostOutSend(k, id, xsArrayGetFloat(crucibleOutpostEnemyX, e),
                    xsArrayGetFloat(crucibleOutpostEnemyY, e));
            } else {
                xsArraySetInt(crucibleOutpostOutKind, k, 4);
                crucibleOutpostOutSend(k, id, hx, hy);
            }
        } else if (crucibleOutpostDist2(xsVectorGetX(at), xsVectorGetY(at), hx, hy) < 64.0) {
            xsArraySetInt(crucibleOutpostOut, k, -1);  // home: idle in the base

            for (g = 0; < cCrucibleOutpostMax) {
                if ((id >= 0) && (xsArrayGetInt(crucibleOutpostDefenders, o * cCrucibleOutpostMax + g) < 0)) {
                    xsArraySetInt(crucibleOutpostDefenders, o * cCrucibleOutpostMax + g, id);
                    xsArraySetFloat(crucibleOutpostDefenderHp, o * cCrucibleOutpostMax + g, crucibleOutpostHp(id));
                    id = -1;
                }
            }
        }
    }
}

// ---- hunting: turtled, the garrison goes for the player's units near the base ----

void crucibleOutpostHunt(int o = 0) {
    float hx = crucibleOutpostHomeX(o);
    float hy = crucibleOutpostHomeY(o);
    int e = crucibleOutpostNearest(hx, hy, cCrucibleOutpostHuntRange, false, false);
    float x = 0.0;
    float y = 0.0;

    if (e >= 0) {
        x = xsArrayGetFloat(crucibleOutpostEnemyX, e);
        y = xsArrayGetFloat(crucibleOutpostEnemyY, e);

        if ((xsArrayGetInt(crucibleOutpostHunting, o) == 0) || (crucibleOutpostDist2(x, y,
            xsArrayGetFloat(crucibleOutpostHuntX, o), xsArrayGetFloat(crucibleOutpostHuntY, o)) >= 9.0)) {
            xsArraySetInt(crucibleOutpostHunting, o, 1);
            xsArraySetFloat(crucibleOutpostHuntX, o, x);
            xsArraySetFloat(crucibleOutpostHuntY, o, y);
            crucibleOutpostSendAll(crucibleOutpostDefenders, o, cCrucibleOutpostMax, crucibleOutpostAt(x, y));
        }
    } else if (xsArrayGetInt(crucibleOutpostHunting, o) == 1) {
        xsArraySetInt(crucibleOutpostHunting, o, 0);
        crucibleOutpostToPosts(o);
    }
}

// Its ships go for the player's ships and docks in reach (bullying the docks); none: back to their posts.
void crucibleOutpostSail(int o = 0) {
    int e = -1;
    float x = 0.0;
    float y = 0.0;
    int id = -1;

    if (crucibleOutpostSea(o) == false) {
        return;
    }

    e = crucibleOutpostNearestSea(crucibleOutpostHomeX(o), crucibleOutpostHomeY(o), cCrucibleOutpostSeaRange);

    if (e >= 0) {
        x = xsArrayGetFloat(crucibleOutpostSeaX, e);
        y = xsArrayGetFloat(crucibleOutpostSeaY, e);

        if ((xsArrayGetInt(crucibleOutpostShipsOut, o) == 0) || (crucibleOutpostDist2(x, y,
            xsArrayGetFloat(crucibleOutpostShipX, o), xsArrayGetFloat(crucibleOutpostShipY, o)) >= 9.0)) {
            if (xsArrayGetInt(crucibleOutpostShipsOut, o) == 0) {
                crucibleOutpostSay(o, "ships go for the player's ships or docks");
            }

            xsArraySetInt(crucibleOutpostShipsOut, o, 1);
            xsArraySetFloat(crucibleOutpostShipX, o, x);
            xsArraySetFloat(crucibleOutpostShipY, o, y);
            crucibleOutpostSendAll(crucibleOutpostShips, o, cCrucibleOutpostShipMax, crucibleOutpostAt(x, y));
        }
    } else if (xsArrayGetInt(crucibleOutpostShipsOut, o) == 1) {
        xsArraySetInt(crucibleOutpostShipsOut, o, 0);

        for (d = 0; < cCrucibleOutpostShipMax) {
            id = xsArrayGetInt(crucibleOutpostShips, o * cCrucibleOutpostShipMax + d);

            if (id >= 0) {
                crucibleOutpostTaskOne(id, cActionTypeAttackMove, crucibleOutpostSeaPost(o, d));
            }
        }
    }
}

// ---- attack waves ----

int crucibleOutpostWaveSize(int o = 0) {
    int size = cCrucibleOutpostWaveBase + crucibleOutpostLevel(o) / 2 + crucibleWaveAge * 2
        + (crucibleWaveFactor - 1) * 2;

    if (size > cCrucibleOutpostWaveMax) {
        return (cCrucibleOutpostWaveMax);
    }

    return (size);
}

vector crucibleOutpostMarker(int o = 0, int which = 0) {
    if (which == 1) {
        return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostMarker2X, o),
            xsArrayGetFloat(crucibleOutpostMarker2Y, o)));
    }

    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostMarkerX, o), xsArrayGetFloat(crucibleOutpostMarkerY, o)));
}

// Land: the wave appears at its marker on the south edge and attack-moves the Wonder.
void crucibleOutpostLandWave(int o = 0, int size = 0) {
    int id = -1;
    int n = 0;

    xsArrayResizeInt(crucibleOutpostIds, size);

    for (k = 0; < size) {
        id = xsCreateUnit(crucibleOutpostUnit(o), cCrucibleOutpostLegion, crucibleOutpostMarker(o, 0), false, false,
            false);

        if (id >= 0) {
            xsArraySetInt(crucibleOutpostIds, n, id);
            n++;
        }
    }

    if (n > 0) {
        xsArrayResizeInt(crucibleOutpostIds, n);
        xsTaskUnits(crucibleOutpostIds, cActionTypeAttackMove, crucibleOutpostWonder());
    }

    crucibleOutpostSay(o, "attack wave of " + n + " from its marker");
}

// Sea: transports from its markers (light ones while two can carry it, else heavy) sail to its beach.
void crucibleOutpostSeaWave(int o = 0, int size = 0) {
    int capacity = cCrucibleOutpostLightCapacity;
    int ship = cCrucibleOutpostLightTransport;
    int left = size;
    int carry = 0;
    int id = -1;
    int which = 0;
    int sent = 0;
    vector beach = crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostBeachWaterX, o),
        xsArrayGetFloat(crucibleOutpostBeachWaterY, o));

    if (size > 2 * cCrucibleOutpostLightCapacity) {
        capacity = cCrucibleOutpostHeavyCapacity;
        ship = cCrucibleOutpostHeavyTransport;
    }

    for (t = 0; < cCrucibleOutpostTransportMax) {
        if ((left <= 0) || (xsArrayGetInt(crucibleOutpostTransport, t) >= 0)) {
            continue;
        }

        carry = capacity;

        if (left < carry) {
            carry = left;
        }

        id = xsCreateUnit(ship, cCrucibleOutpostLegion, crucibleOutpostMarker(o, which), false, false, false);

        if (id < 0) {
            continue;
        }

        xsArraySetInt(crucibleOutpostTransport, t, id);
        xsArraySetInt(crucibleOutpostTransportOutpost, t, o);
        xsArraySetInt(crucibleOutpostTransportUnit, t, crucibleOutpostUnit(o));
        xsArraySetInt(crucibleOutpostTransportCount, t, carry);
        xsArraySetInt(crucibleOutpostTransportState, t, 1);
        xsArraySetInt(crucibleOutpostTransportTime, t, xsGetTime());
        xsArraySetInt(crucibleOutpostTransportMarker, t, which);
        crucibleOutpostTaskOne(id, cActionTypeMove, beach);
        left = left - carry;
        which = 1 - which;
        sent++;
    }

    crucibleOutpostSay(o, "attack wave of " + (size - left) + " in " + sent + " transports");
}

// Transports at the beach land their party (made there: no real unload works) and sail off; sunk, the party's lost.
void crucibleOutpostTransports() {
    int id = -1;
    int o = 0;
    int now = xsGetTime();
    int count = 0;
    int unit = -1;
    int n = 0;
    int made = -1;
    vector at = cInvalidVector;
    vector marker = cInvalidVector;
    float bx = 0.0;
    float by = 0.0;

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
        at = xsGetUnitPosition(id);
        marker = crucibleOutpostMarker(o, xsArrayGetInt(crucibleOutpostTransportMarker, t));

        if (xsArrayGetInt(crucibleOutpostTransportState, t) == 1) {
            bx = xsArrayGetFloat(crucibleOutpostBeachWaterX, o);
            by = xsArrayGetFloat(crucibleOutpostBeachWaterY, o);

            if ((crucibleOutpostDist2(xsVectorGetX(at), xsVectorGetY(at), bx, by) > 16.0)
                && (now - xsArrayGetInt(crucibleOutpostTransportTime, t) < cCrucibleOutpostLandTimeout)) {
                continue;
            }

            count = xsArrayGetInt(crucibleOutpostTransportCount, t);
            unit = xsArrayGetInt(crucibleOutpostTransportUnit, t);
            xsArrayResizeInt(crucibleOutpostFound, count);
            n = 0;

            for (k = 0; < count) {
                made = xsCreateUnit(unit, cCrucibleOutpostLegion, crucibleOutpostAt(xsArrayGetFloat(
                    crucibleOutpostBeachX, o), xsArrayGetFloat(crucibleOutpostBeachY, o)), false, false, false);

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
            crucibleOutpostTaskOne(id, cActionTypeMove, marker);
        } else if ((crucibleOutpostDist2(xsVectorGetX(at), xsVectorGetY(at), xsVectorGetX(marker),
            xsVectorGetY(marker)) < 16.0) || (now - xsArrayGetInt(crucibleOutpostTransportTime, t)
            >= cCrucibleOutpostLandTimeout)) {
            xsSetUnitProperty(id, cUnitHitpoints, 0.0);  // gone off the map
            xsArraySetInt(crucibleOutpostTransport, t, -1);
        }
    }
}

// ---- turns ----

// Its spot (of its own, or any within help range: `own`) with the player on it, the most pressured; -1 if none.
int crucibleOutpostContested(int o = 0, bool own = true) {
    int best = -1;
    int spot = -1;
    float hx = crucibleOutpostHomeX(o);
    float hy = crucibleOutpostHomeY(o);
    float r2 = cCrucibleOutpostHelpRange * cCrucibleOutpostHelpRange;

    if (own) {
        for (s = xsArrayGetInt(crucibleOutpostSpotStart, o); < xsArrayGetInt(crucibleOutpostSpotStart, o + 1)) {
            spot = xsArrayGetInt(crucibleOutpostOwnSpots, s);

            if (xsArrayGetInt(crucibleOutpostSpotContest, spot) > 0) {
                if ((best < 0) || (xsArrayGetInt(crucibleOutpostSpotPressure, spot)
                    > xsArrayGetInt(crucibleOutpostSpotPressure, best))) {
                    best = spot;
                }
            }
        }

        return (best);
    }

    for (s = 0; < cCrucibleOutpostSpots) {
        if (xsArrayGetInt(crucibleOutpostSpotContest, s) <= 0) {
            continue;
        }

        if (crucibleOutpostDist2(hx, hy, xsArrayGetFloat(crucibleOutpostSpotX, s), xsArrayGetFloat(crucibleOutpostSpotY,
            s)) > r2) {
            continue;
        }

        if ((best < 0) || (xsArrayGetInt(crucibleOutpostSpotPressure, s) > xsArrayGetInt(crucibleOutpostSpotPressure,
            best))) {
            best = s;
        }
    }

    return (best);
}

int crucibleOutpostUnguarded(int o = 0) {
    int spot = -1;

    for (s = xsArrayGetInt(crucibleOutpostSpotStart, o); < xsArrayGetInt(crucibleOutpostSpotStart, o + 1)) {
        spot = xsArrayGetInt(crucibleOutpostOwnSpots, s);

        if (xsArrayGetInt(crucibleOutpostSpotGuards, spot) <= 0) {
            return (spot);
        }
    }

    return (-1);
}

int crucibleOutpostCap(int size = 0, int most = 0) {
    if (size > most) {
        return (most);
    }

    return (size);
}

vector crucibleOutpostSpotAt(int spot = 0) {
    return (crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostSpotX, spot), xsArrayGetFloat(crucibleOutpostSpotY, spot)));
}

void crucibleOutpostTurn(int o = 0) {
    int spot = -1;
    int e = -1;
    int size = 0;
    int made = 0;
    string where = "";

    if (crucibleOutpostTurtled(o)) {
        xsArraySetInt(crucibleOutpostGrowth, o, xsArrayGetInt(crucibleOutpostGrowth, o) + cCrucibleOutpostGrowHarassed);
        crucibleOutpostSay(o, "turtled, " + crucibleOutpostCount(o) + " defenders, " + crucibleOutpostShipCount(o)
            + " ships");
        return;
    }

    xsArraySetInt(crucibleOutpostGrowth, o, xsArrayGetInt(crucibleOutpostGrowth, o) + cCrucibleOutpostGrow);
    made = crucibleOutpostTopUp(o, cCrucibleOutpostSpawnPerTick);
    crucibleOutpostSay(o, "+" + made + ": " + crucibleOutpostCount(o) + " defenders, " + crucibleOutpostShipCount(o)
        + " ships, " + crucibleOutpostOutCount(o) + " out");

    if (xsArrayGetInt(crucibleOutpostHunting, o) == 0) {
        crucibleOutpostToPosts(o);
    }

    spot = crucibleOutpostContested(o, true);

    if (spot >= 0) {
        size = cCrucibleOutpostBullyBase + xsArrayGetInt(crucibleOutpostSpotPressure, spot) * cCrucibleOutpostBullyPer
            + crucibleWaveAge;
        made = crucibleOutpostParty(o, crucibleOutpostCap(size, cCrucibleOutpostBullyMax), 2, spot,
            crucibleOutpostSpotAt(spot));
        where = xsArrayGetString(crucibleOutpostSpotName, spot);
        crucibleOutpostSay(o, "bullies the player off " + where + " with " + made);
        return;
    }

    spot = crucibleOutpostUnguarded(o);

    if ((spot >= 0) && (crucibleOutpostOutCount(o) < cCrucibleOutpostOutMax / 2)) {
        size = cCrucibleOutpostGuardBase + crucibleOutpostLevel(o) / 4 + crucibleWaveAge;
        made = crucibleOutpostParty(o, crucibleOutpostCap(size, cCrucibleOutpostGuardMax), 1, spot,
            crucibleOutpostSpotAt(spot));
        where = xsArrayGetString(crucibleOutpostSpotName, spot);
        crucibleOutpostSay(o, "guards " + where + " with " + made);
        return;
    }

    size = crucibleOutpostCap(cCrucibleOutpostGuardBase + crucibleOutpostLevel(o) / 4 + crucibleWaveAge,
        cCrucibleOutpostRaidMax);
    spot = crucibleOutpostContested(o, false);

    if (spot >= 0) {
        made = crucibleOutpostParty(o, size, 2, spot, crucibleOutpostSpotAt(spot));
        where = xsArrayGetString(crucibleOutpostSpotName, spot);
        crucibleOutpostSay(o, "helps at " + where + " with " + made);
        return;
    }

    e = crucibleOutpostNearest(crucibleOutpostHomeX(o), crucibleOutpostHomeY(o), cCrucibleOutpostHelpRange, true,
        true);

    if (e >= 0) {
        made = crucibleOutpostParty(o, size, 3, -1, crucibleOutpostAt(xsArrayGetFloat(crucibleOutpostEnemyX, e),
            xsArrayGetFloat(crucibleOutpostEnemyY, e)));
        crucibleOutpostSay(o, "raids the player's gatherers with " + made);
        return;
    }

    if (crucibleOutpostSea(o)) {
        if (crucibleOutpostNearestSea(crucibleOutpostHomeX(o), crucibleOutpostHomeY(o), cCrucibleOutpostSeaRange) >= 0) {
            crucibleOutpostSay(o, "its ships are busy with the player's docks: no wave");
            return;
        }

        crucibleOutpostSeaWave(o, crucibleOutpostWaveSize(o));
        return;
    }

    crucibleOutpostLandWave(o, crucibleOutpostWaveSize(o));
}

// ---- every second ----

// Outpost o's buildings, garrison and ships: hit? destroyed? Its turn, its turtled spawns.
void crucibleOutpostWatch(int o = 0) {
    int now = xsGetTime();
    float total = 0.0;
    float hp = 0.0;
    int id = -1;
    int k = 0;
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

    for (d = 0; < cCrucibleOutpostMax) {
        k = o * cCrucibleOutpostMax + d;
        id = xsArrayGetInt(crucibleOutpostDefenders, k);

        if (id < 0) {
            continue;
        }

        hp = crucibleOutpostHp(id);

        if (hp < xsArrayGetFloat(crucibleOutpostDefenderHp, k) - 0.5) {
            hit = true;
        }

        if (hp <= 0.0) {
            xsArraySetInt(crucibleOutpostDefenders, k, -1);
        }

        xsArraySetFloat(crucibleOutpostDefenderHp, k, hp);
    }

    for (d = 0; < cCrucibleOutpostShipMax) {
        k = o * cCrucibleOutpostShipMax + d;
        id = xsArrayGetInt(crucibleOutpostShips, k);

        if (id < 0) {
            continue;
        }

        hp = crucibleOutpostHp(id);

        if (hp < xsArrayGetFloat(crucibleOutpostShipHp, k) - 0.5) {
            hit = true;
        }

        if (hp <= 0.0) {
            xsArraySetInt(crucibleOutpostShips, k, -1);
        }

        xsArraySetFloat(crucibleOutpostShipHp, k, hp);
    }

    if (hit) {
        if (crucibleOutpostTurtled(o) == false) {
            crucibleOutpostSay(o, "harassed: turtles, calls its parties home, hunts");
            crucibleOutpostRecall(o);
            xsArraySetInt(crucibleOutpostTurtleSpawn, o, now + cCrucibleOutpostTurtleSpawnEvery);
        }

        xsArraySetInt(crucibleOutpostHarassedAt, o, now);
        crucibleOutpostHunt(o);
    }

    if (crucibleOutpostTurtled(o) && (now >= xsArrayGetInt(crucibleOutpostTurtleSpawn, o))) {
        xsArraySetInt(crucibleOutpostTurtleSpawn, o, now + cCrucibleOutpostTurtleSpawnEvery);
        crucibleOutpostTopUp(o, cCrucibleOutpostTurtleSpawn);
    }

    if (now >= xsArrayGetInt(crucibleOutpostNextTurn, o)) {
        xsArraySetInt(crucibleOutpostNextTurn, o, now + cCrucibleOutpostTick
            + xsGetRandomNumberLH(0, cCrucibleOutpostTickSpread));
        crucibleOutpostTurn(o);
    }
}

rule crucibleOutpostStart
    active
    minInterval 1
{
    if (xsGetTime() < cCrucibleOutpostStart) {
        return;
    }

    crucibleOutpostData();
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
    crucibleOutpostDefenders = xsArrayCreateInt(cCrucibleOutposts * cCrucibleOutpostMax, -1,
        "crucibleOutpostDefenders");
    crucibleOutpostDefenderHp = xsArrayCreateFloat(cCrucibleOutposts * cCrucibleOutpostMax, 0.0,
        "crucibleOutpostDefenderHp");
    crucibleOutpostShips = xsArrayCreateInt(cCrucibleOutposts * cCrucibleOutpostShipMax, -1, "crucibleOutpostShips");
    crucibleOutpostShipHp = xsArrayCreateFloat(cCrucibleOutposts * cCrucibleOutpostShipMax, 0.0,
        "crucibleOutpostShipHp");
    crucibleOutpostOut = xsArrayCreateInt(cCrucibleOutposts * cCrucibleOutpostOutMax, -1, "crucibleOutpostOut");
    crucibleOutpostOutKind = xsArrayCreateInt(cCrucibleOutposts * cCrucibleOutpostOutMax, 0, "crucibleOutpostOutKind");
    crucibleOutpostOutSpot = xsArrayCreateInt(cCrucibleOutposts * cCrucibleOutpostOutMax, -1, "crucibleOutpostOutSpot");
    crucibleOutpostOutX = xsArrayCreateFloat(cCrucibleOutposts * cCrucibleOutpostOutMax, 0.0, "crucibleOutpostOutX");
    crucibleOutpostOutY = xsArrayCreateFloat(cCrucibleOutposts * cCrucibleOutpostOutMax, 0.0, "crucibleOutpostOutY");
    crucibleOutpostEnemyId = xsArrayCreateInt(cCrucibleOutpostEnemyMax, -1, "crucibleOutpostEnemyId");
    crucibleOutpostEnemyX = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostEnemyX");
    crucibleOutpostEnemyY = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostEnemyY");
    crucibleOutpostEnemyVillager = xsArrayCreateInt(cCrucibleOutpostEnemyMax, 0, "crucibleOutpostEnemyVillager");
    crucibleOutpostSeaId = xsArrayCreateInt(cCrucibleOutpostEnemyMax, -1, "crucibleOutpostSeaId");
    crucibleOutpostSeaX = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostSeaX");
    crucibleOutpostSeaY = xsArrayCreateFloat(cCrucibleOutpostEnemyMax, 0.0, "crucibleOutpostSeaY");
    crucibleOutpostSpotContest = xsArrayCreateInt(cCrucibleOutpostSpots + 1, 0, "crucibleOutpostSpotContest");
    crucibleOutpostSpotPressure = xsArrayCreateInt(cCrucibleOutpostSpots + 1, 0, "crucibleOutpostSpotPressure");
    crucibleOutpostSpotGuards = xsArrayCreateInt(cCrucibleOutpostSpots + 1, 0, "crucibleOutpostSpotGuards");
    crucibleOutpostTransport = xsArrayCreateInt(cCrucibleOutpostTransportMax, -1, "crucibleOutpostTransport");
    crucibleOutpostTransportOutpost = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportOutpost");
    crucibleOutpostTransportUnit = xsArrayCreateInt(cCrucibleOutpostTransportMax, -1, "crucibleOutpostTransportUnit");
    crucibleOutpostTransportCount = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportCount");
    crucibleOutpostTransportState = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportState");
    crucibleOutpostTransportTime = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportTime");
    crucibleOutpostTransportMarker = xsArrayCreateInt(cCrucibleOutpostTransportMax, 0, "crucibleOutpostTransportMarker");
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
            if (crucibleOutpostTurtled(o)) {
                crucibleOutpostHunt(o);
            } else if (xsArrayGetInt(crucibleOutpostHunting, o) == 1) {
                xsArraySetInt(crucibleOutpostHunting, o, 0);
                crucibleOutpostToPosts(o);
            }

            crucibleOutpostSail(o);
            crucibleOutpostManageOut(o);
        }
    }

    crucibleOutpostTransports();
}
