// ---- crucible run: waves (runtime) ----
// A wave spawns and walks in, waits staged (the Send button on), then is sent at its time or on a click; the next
// spawns. Wave 0 is sent as soon as it's staged, without moving the clock. The data block (wave_table) comes first.

int crucibleWave = 0;  // the wave walking in or waiting
int crucibleWaveDifficulty = 0;  // wave_table.Difficulty
bool crucibleWaveWalkPending = true;  // spawn crucibleWave once the last send has been acted on
bool crucibleWaveReady = false;  // staged, button on
bool crucibleWaveArmed = false;  // the button has been seen ready since it was put on (a click is real)
int crucibleWaveSendAt = cCrucibleWaveSendTime;
int crucibleWaveLaneArchetype = -1;  // by lane

// every spawned unit and its wave, to tell when a wave is staged and when it is defeated
const int cCrucibleWaveCapacity = 4000;
int crucibleWaveSentIds = -1;
int crucibleWaveSentWave = -1;
int crucibleWaveSentCount = 0;
int crucibleWaveDefeated = -1;  // by wave number: 1 once defeated
int crucibleWaveDefeatedCount = 0;
int crucibleWaveLastX = -1;  // by spawned unit: where it was at the last check
int crucibleWaveLastY = -1;
int crucibleWaveOne = -1;  // a one-unit array for xsTaskUnits

// The lanes a wave comes down: 1 the Capital's, 2 the City States', 3 all.
int crucibleWaveLaneSet(int wave = 0) {
    if (wave >= cCrucibleWaveAllLanesFrom) {
        return (3);
    }

    if ((wave == 0) || ((wave % 2) == 1)) {
        return (1);
    }

    return (2);
}

bool crucibleWaveLaneIn(int lane = 0, int set = 0) {
    if (set == 3) {
        return (true);
    }

    if (lane < cCrucibleWaveCapitalLanes) {
        return (set == 1);
    }

    return (set == 2);
}

// Where a wave's numbers are in the tables; waves after the last repeat it.
int crucibleWaveIndex(int wave = 0) {
    if (wave >= cCrucibleWaves) {
        wave = cCrucibleWaves - 1;
    }

    return (crucibleWaveDifficulty * cCrucibleWaves + wave);
}

// One of up to cCrucibleWaveChoices unit ids from `base` in `array`, at random; -1 if none.
int crucibleWavePick(int array = -1, int base = 0) {
    int count = 0;

    for (i = 0; < cCrucibleWaveChoices) {
        if (xsArrayGetInt(array, base + i) >= 0) {
            count++;
        }
    }

    if (count == 0) {
        return (-1);
    }

    return (xsArrayGetInt(array, base + xsGetRandomNumberLH(0, count)));
}

int crucibleWaveUnitBase(int archetype = 0, int age = 0, int slot = 0) {
    return (((archetype * cCrucibleWaveAges + age) * 2 + slot) * cCrucibleWaveChoices);
}

// Spawn `unit` as the `n`th of its group on `lane`: rows of cCrucibleWaveColumns, inwards from the spawn row.
void crucibleWaveSpawn(int lane = 0, int n = 0, int unit = -1) {
    if (unit < 0) {
        return;
    }

    int column = n % cCrucibleWaveColumns;
    int row = n / cCrucibleWaveColumns;
    float side = column - (cCrucibleWaveColumns - 1) / 2;
    float depth = 0.5 + row * cCrucibleWaveRowSpacing;
    float dx = xsArrayGetFloat(crucibleWaveDirX, lane);
    float dy = xsArrayGetFloat(crucibleWaveDirY, lane);
    float x = xsArrayGetFloat(crucibleWaveSpawnX, lane) + dx * depth + dy * side * cCrucibleWaveSpacing;
    float y = xsArrayGetFloat(crucibleWaveSpawnY, lane) + dy * depth + dx * side * cCrucibleWaveSpacing;
    int id = xsCreateUnit(unit, cCrucibleWaveLegion, xsVectorSet(x, y, 0.0), false, false, false);

    if (id < 0) {
        xsChatData("Waves: could not spawn unit %d", unit);
        return;
    }

    if (crucibleWaveSentCount < cCrucibleWaveCapacity) {
        xsArraySetInt(crucibleWaveSentIds, crucibleWaveSentCount, id);
        xsArraySetInt(crucibleWaveSentWave, crucibleWaveSentCount, crucibleWave);
        crucibleWaveSentCount++;
    }
}

// The group of the current wave on `lane`: main units, other units, siege, and a Priest from its age.
void crucibleWaveSpawnGroup(int lane = 0) {
    int k = crucibleWaveIndex(crucibleWave);
    int age = xsArrayGetInt(crucibleWaveAge, k);
    int archetype = xsArrayGetInt(crucibleWaveLaneArchetype, lane);
    int n = 0;

    for (i = 0; < xsArrayGetInt(crucibleWaveMain, k)) {
        crucibleWaveSpawn(lane, n, crucibleWavePick(crucibleWaveUnit, crucibleWaveUnitBase(archetype, age, 0)));
        n++;
    }

    for (j = 0; < xsArrayGetInt(crucibleWaveOther, k)) {
        crucibleWaveSpawn(lane, n, crucibleWavePick(crucibleWaveUnit, crucibleWaveUnitBase(archetype, age, 1)));
        n++;
    }

    int siegeBase = age * cCrucibleWaveChoices;
    int siegeKinds = 0;

    for (c = 0; < cCrucibleWaveChoices) {
        if (xsArrayGetInt(crucibleWaveSiegeUnit, siegeBase + c) >= 0) {
            siegeKinds++;
        }
    }

    if (siegeKinds > 0) {
        for (s = 0; < xsArrayGetInt(crucibleWaveSiege, k)) {
            crucibleWaveSpawn(lane, n, xsArrayGetInt(crucibleWaveSiegeUnit, siegeBase + (s % siegeKinds)));
            n++;
        }
    }

    if (age >= xsArrayGetInt(crucibleWavePriestAge, crucibleWaveDifficulty)) {
        crucibleWaveSpawn(lane, n, cCrucibleWavePriest);
    }
}

// Spawn the current wave on its lanes and have the triggers walk it in.
void crucibleWaveWalkIn() {
    int set = crucibleWaveLaneSet(crucibleWave);
    int age = xsArrayGetInt(crucibleWaveAge, crucibleWaveIndex(crucibleWave));
    string text = "Wave " + crucibleWave + " (" + xsArrayGetString(crucibleWaveAgeName, age) + ")";

    for (lane = 0; < cCrucibleWaveLanes) {
        if (crucibleWaveLaneIn(lane, set)) {
            crucibleWaveSpawnGroup(lane);
            text = text + ", " + xsArrayGetString(crucibleWaveLaneName, lane);

            if (age > 0) {
                int archetype = xsArrayGetInt(crucibleWaveLaneArchetype, lane);
                text = text + ": " + xsArrayGetString(crucibleWaveArchetypeName, archetype);
            }
        }
    }

    xsChatData(text);
    xsSetTriggerVariable(cCrucibleWaveWalkVariable, set);
    crucibleWaveWalkPending = false;
}

// Each lane an archetype, no two the same.
void crucibleWaveRollArchetypes() {
    crucibleWaveLaneArchetype = xsArrayCreateInt(cCrucibleWaveLanes, -1, "crucibleWaveLaneArchetype");
    bool taken = true;  // declared outside the loop: XS runs a declaration in a loop only once
    int roll = 0;

    for (lane = 0; < cCrucibleWaveLanes) {
        taken = true;

        while (taken) {
            roll = xsGetRandomNumberLH(0, cCrucibleWaveArchetypes);
            taken = false;

            for (other = 0; < lane) {
                if (xsArrayGetInt(crucibleWaveLaneArchetype, other) == roll) {
                    taken = true;
                }
            }
        }

        xsArraySetInt(crucibleWaveLaneArchetype, lane, roll);
    }
}

bool crucibleWaveAlive(int id = -1) {
    if (xsDoesUnitExist(id) == false) {
        return (false);
    }

    return (xsGetUnitProperty(id, cUnitHitpoints) > 0);
}

// Every living unit of the current wave is on a staging row (and there is one).
bool crucibleWaveStaged() {
    int walking = 0;
    int waiting = 0;
    int id = -1;

    for (i = 0; < crucibleWaveSentCount) {
        if (xsArrayGetInt(crucibleWaveSentWave, i) == crucibleWave) {
            id = xsArrayGetInt(crucibleWaveSentIds, i);

            if (crucibleWaveAlive(id)) {
                walking++;

                if (crucibleWaveStagedAt(xsGetUnitPosition(id))) {
                    waiting++;
                }
            }
        }
    }

    return ((walking > 0) && (waiting == walking));
}

// Each sent wave with no unit left alive is defeated: count it once. Wave 0 gives free Poor boons.
void crucibleWaveCountDefeated() {
    bool alive = false;  // declared outside the loop: XS runs a declaration in a loop only once

    for (wave = 0; < crucibleWave) {
        if (xsArrayGetInt(crucibleWaveDefeated, wave) == 0) {
            alive = false;

            for (i = 0; < crucibleWaveSentCount) {
                if ((xsArrayGetInt(crucibleWaveSentWave, i) == wave)
                    && crucibleWaveAlive(xsArrayGetInt(crucibleWaveSentIds, i))) {
                    alive = true;
                    break;
                }
            }

            if (alive == false) {
                xsArraySetInt(crucibleWaveDefeated, wave, 1);
                crucibleWaveDefeatedCount++;
                xsSetPlayerAttribute(cCrucibleWaveCounterPlayer, cCrucibleWaveCounterRelics, crucibleWaveDefeatedCount);
                xsChatData("Wave %d defeated", wave);

                if (wave == 0) {
                    crucibleShopOpenPoor();  // free Poor boons
                } else {
                    crucibleShopOpen();  // a decision: two boon categories on the Wonder
                }

                if (crucibleWaveDefeatedCount >= cCrucibleWaves) {
                    xsSetTriggerVariable(cCrucibleWaveWonVariable, 1);  // win now or fight on
                }
            }
        }
    }
}

// Sent units standing idle (no target, not moved since the last check) go on to the Wonder: attack-moving to it, or
// attacking it once near (the end of the road, or the gap a tower left, isn't where they stop).
void crucibleWavePush() {
    int id = -1;
    vector pos = cInvalidVector;
    float x = 0.0;
    float y = 0.0;
    float dx = 0.0;
    float dy = 0.0;

    for (i = 0; < crucibleWaveSentCount) {
        if (xsArrayGetInt(crucibleWaveSentWave, i) < crucibleWave) {
            id = xsArrayGetInt(crucibleWaveSentIds, i);

            if (crucibleWaveAlive(id)) {
                pos = xsGetUnitPosition(id);
                x = xsVectorGetX(pos);
                y = xsVectorGetY(pos);
                dx = x - xsArrayGetFloat(crucibleWaveLastX, i);
                dy = y - xsArrayGetFloat(crucibleWaveLastY, i);

                if ((xsGetUnitTargetUnitId(id) < 0) && ((dx * dx + dy * dy) < 0.09)) {
                    xsArraySetInt(crucibleWaveOne, 0, id);
                    dx = x - xsVectorGetX(cCrucibleWaveWonderAt);
                    dy = y - xsVectorGetY(cCrucibleWaveWonderAt);

                    if ((dx * dx + dy * dy) < cCrucibleWaveAtWonder) {
                        xsTaskUnits(crucibleWaveOne, cActionTypeDefault, cCrucibleWaveWonderAt, cCrucibleWaveWonder);
                    } else {
                        xsTaskUnits(crucibleWaveOne, cActionTypeAttackMove, cCrucibleWaveWonderAt);
                    }
                }

                xsArraySetFloat(crucibleWaveLastX, i, x);
                xsArraySetFloat(crucibleWaveLastY, i, y);
            }
        }
    }
}

void crucibleWaveSend() {
    xsSetTriggerVariable(cCrucibleWaveSendVariable, crucibleWaveLaneSet(crucibleWave));
    xsSetTriggerVariable(cCrucibleWaveButtonVariable, 2);

    if (crucibleWave > 0) {
        crucibleWaveSendAt = xsGetTime() + cCrucibleWaveSendTime;
        xsSetTriggerVariable(cCrucibleWaveTimerVariable, 1);
    }

    crucibleWave++;
    crucibleWaveReady = false;
    crucibleWaveArmed = false;
    crucibleWaveWalkPending = true;  // next check, once the send is acted on: the send's area holds the spawn rows
}

rule crucibleWaveStart
    active
    highFrequency
{
    crucibleWaveData();
    crucibleWaveSentIds = xsArrayCreateInt(cCrucibleWaveCapacity, -1, "crucible wave sent ids");
    crucibleWaveSentWave = xsArrayCreateInt(cCrucibleWaveCapacity, -1, "crucible wave sent wave");
    crucibleWaveDefeated = xsArrayCreateInt(1000, 0, "crucible wave defeated");
    crucibleWaveLastX = xsArrayCreateFloat(cCrucibleWaveCapacity, -100.0, "crucible wave last x");
    crucibleWaveLastY = xsArrayCreateFloat(cCrucibleWaveCapacity, -100.0, "crucible wave last y");
    crucibleWaveOne = xsArrayCreateInt(1, -1, "crucible wave one");
    int difficulty = xsGetDifficulty();

    if ((difficulty >= 0) && (difficulty < xsArrayGetSize(crucibleWaveDifficultyOf))) {
        crucibleWaveDifficulty = xsArrayGetInt(crucibleWaveDifficultyOf, difficulty);
    } else {
        crucibleWaveDifficulty = xsArrayGetInt(crucibleWaveDifficultyOf, 0);  // Extreme: as Hardest
    }

    crucibleWaveRollArchetypes();
    xsSetPlayerAttribute(cCrucibleWaveCounterPlayer, cCrucibleWaveCounterRelics, 0);
    xsChatData("Waves: difficulty %d (0 Standard, 1 Moderate, 2 Hard)", crucibleWaveDifficulty);
    xsDisableSelf();
}

rule crucibleWaves
    active
    minInterval 1
{
    if (crucibleWaveSentIds < 0) {
        return;
    }

    if (crucibleWaveWalkPending) {
        if (xsTriggerVariable(cCrucibleWaveSendVariable) == 0) {
            crucibleWaveWalkIn();
        }

        crucibleWaveCountDefeated();
        crucibleWavePush();
        return;
    }

    int state = xsGetTechState(cCrucibleWaveButton, 1);

    if ((crucibleWaveReady == false) && crucibleWaveStaged()) {
        if (crucibleWave == 0) {
            crucibleWaveSend();  // wave 0 goes at once
            return;
        }

        xsSetTriggerVariable(cCrucibleWaveButtonVariable, 1);
        crucibleWaveReady = true;
    }

    if (crucibleWaveReady && (state == cTechStateReady)) {
        crucibleWaveArmed = true;
    }

    bool clicked = crucibleWaveArmed && (state == cTechStateDone);

    if (clicked || ((crucibleWave > 0) && (xsGetTime() >= crucibleWaveSendAt))) {
        crucibleWaveSend();
    }

    crucibleWaveCountDefeated();
    crucibleWavePush();
}
