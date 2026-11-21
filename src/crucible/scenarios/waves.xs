// ---- crucible run: waves (runtime) ----
// A wave spawns and walks in, waits staged (the Send button on), then is sent at its time or on a click; the next
// spawns. Wave 0 is sent as soon as it's staged, without moving the clock. Before a lane spawns (but for wave 0) its
// army takes a step: age up (shared), grow, upgrade (shared), swap, nothing, or again. The data block comes first.

int crucibleWave = 0;  // the wave walking in or waiting
int crucibleWaveDifficulty = 0;  // wave_table.Difficulty
int crucibleWaveSendEvery = 300;  // seconds
bool crucibleWaveWalkPending = true;  // spawn crucibleWave once the last send has been acted on
bool crucibleWaveReady = false;  // staged, button on
bool crucibleWaveArmed = false;  // the button has been seen ready since it was put on (a click is real)
int crucibleWaveSendAt = 0;

// the Legion: shared by every lane
int crucibleWaveAge = 0;
int crucibleWaveAgeChance = 0;  // percent
int crucibleWaveUpgradeTaken = -1;  // by upgrade: 1 once researched
int crucibleWaveTechQueue = -1;  // techs for the triggers to research, one at a time
int crucibleWaveTechHead = 0;
int crucibleWaveTechTail = 0;
const int cCrucibleWaveTechQueueSize = 64;

// each lane's army: its archetype, and two slots (melee, ranged) of a line and a count, at lane * 2 + slot
int crucibleWaveLaneArchetype = -1;
int crucibleWaveSlotLine = -1;
int crucibleWaveSlotCount = -1;

// every spawned unit and its wave, to tell when a wave is staged and when it is defeated
const int cCrucibleWaveCapacity = 6000;
int crucibleWaveSentIds = -1;
int crucibleWaveSentWave = -1;
int crucibleWaveSentCount = 0;
int crucibleWaveDefeated = -1;  // by wave number: 1 once defeated
int crucibleWaveDefeatedCount = 0;
int crucibleWaveLastX = -1;  // by spawned unit: where it was at the last check
int crucibleWaveLastY = -1;
int crucibleWaveOne = -1;  // a one-unit array for xsTaskUnits

// The lanes a wave comes down: 1 the Capital's (wave 0 and odd), 2 the City States'.
int crucibleWaveLaneSet(int wave = 0) {
    if ((wave == 0) || ((wave % 2) == 1)) {
        return (1);
    }

    return (2);
}

bool crucibleWaveLaneIn(int lane = 0, int set = 0) {
    if (lane < cCrucibleWaveCapitalLanes) {
        return (set == 1);
    }

    return (set == 2);
}

void crucibleWaveQueueTech(int tech = -1) {
    if ((tech < 0) || (crucibleWaveTechTail - crucibleWaveTechHead >= cCrucibleWaveTechQueueSize)) {
        return;
    }

    xsArraySetInt(crucibleWaveTechQueue, crucibleWaveTechTail % cCrucibleWaveTechQueueSize, tech);
    crucibleWaveTechTail++;
}

// One queued tech to the triggers when the last is acted on.
void crucibleWaveResearchNext() {
    if ((crucibleWaveTechHead < crucibleWaveTechTail) && (xsTriggerVariable(cCrucibleWaveTechVariable) == 0)) {
        xsSetTriggerVariable(cCrucibleWaveTechVariable,
            xsArrayGetInt(crucibleWaveTechQueue, crucibleWaveTechHead % cCrucibleWaveTechQueueSize));
        crucibleWaveTechHead++;
    }
}

// ---- the armies ----

int crucibleWaveSlot(int lane = 0, int slot = 0) {
    return (lane * 2 + slot);
}

bool crucibleWaveMayHold(int lane = 0, int line = 0) {
    int archetype = xsArrayGetInt(crucibleWaveLaneArchetype, lane);

    return (xsArrayGetInt(crucibleWaveAllowed, archetype * cCrucibleWaveLines + line) == 1);
}

// A line `slot` of `lane` could swap to: allowed, open in the Legion's age, not older than `current`, not `current`.
// `better`: only lines of a later age than `current`.
bool crucibleWaveCanSwap(int lane = 0, int slot = 0, int line = 0, int current = 0, bool better = false) {
    if ((line == current) || (xsArrayGetInt(crucibleWaveLineSlot, line) != slot) || (crucibleWaveMayHold(lane, line) == false)) {
        return (false);
    }

    int age = xsArrayGetInt(crucibleWaveLineAge, line);
    int had = xsArrayGetInt(crucibleWaveLineAge, current);

    if ((age > crucibleWaveAge) || (age < had)) {
        return (false);
    }

    return ((better == false) || (age > had));
}

// A random line `slot` of `lane` could swap to (later ages if any, else the same age); -1 if none.
int crucibleWaveSwapTarget(int lane = 0, int slot = 0) {
    int current = xsArrayGetInt(crucibleWaveSlotLine, crucibleWaveSlot(lane, slot));
    bool better = false;
    int count = 0;

    for (l = 0; < cCrucibleWaveLines) {
        if (crucibleWaveCanSwap(lane, slot, l, current, true)) {
            count++;
        }
    }

    if (count > 0) {
        better = true;
    } else {
        for (m = 0; < cCrucibleWaveLines) {
            if (crucibleWaveCanSwap(lane, slot, m, current, false)) {
                count++;
            }
        }
    }

    if (count == 0) {
        return (-1);
    }

    int roll = xsGetRandomNumberLH(0, count);

    for (n = 0; < cCrucibleWaveLines) {
        if (crucibleWaveCanSwap(lane, slot, n, current, better)) {
            if (roll == 0) {
                return (n);
            }

            roll--;
        }
    }

    return (-1);
}

// The oldest line of a later age than `slot`'s, up to `upTo` (for the age-up catch-up); -1 if none.
int crucibleWaveNextLine(int lane = 0, int slot = 0) {
    int current = xsArrayGetInt(crucibleWaveSlotLine, crucibleWaveSlot(lane, slot));
    int best = -1;

    for (l = 0; < cCrucibleWaveLines) {
        if (crucibleWaveCanSwap(lane, slot, l, current, true)) {
            if ((best < 0) || (xsArrayGetInt(crucibleWaveLineAge, l) < xsArrayGetInt(crucibleWaveLineAge, best))) {
                best = l;
            }
        }
    }

    return (best);
}

void crucibleWaveSetLine(int lane = 0, int slot = 0, int line = 0) {
    int k = crucibleWaveSlot(lane, slot);
    string from = xsArrayGetString(crucibleWaveLineName, xsArrayGetInt(crucibleWaveSlotLine, k));
    xsArraySetInt(crucibleWaveSlotLine, k, line);
    xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": " + from + " become "
        + xsArrayGetString(crucibleWaveLineName, line));
}

// Swap a slot's line, a slot behind the Legion's age first. False if no slot can.
bool crucibleWaveSwap(int lane = 0) {
    int behind = -1;
    int any = -1;

    for (slot = 0; < 2) {
        if (crucibleWaveSwapTarget(lane, slot) >= 0) {
            int line = xsArrayGetInt(crucibleWaveSlotLine, crucibleWaveSlot(lane, slot));

            if (xsArrayGetInt(crucibleWaveLineAge, line) < crucibleWaveAge) {
                if ((behind < 0) || (xsGetRandomNumberLH(0, 2) == 0)) {
                    behind = slot;
                }
            }

            if ((any < 0) || (xsGetRandomNumberLH(0, 2) == 0)) {
                any = slot;
            }
        }
    }

    if (behind >= 0) {
        any = behind;
    }

    if (any < 0) {
        return (false);
    }

    crucibleWaveSetLine(lane, any, crucibleWaveSwapTarget(lane, any));
    return (true);
}

void crucibleWaveGrow(int lane = 0) {
    int melee = crucibleWaveSlot(lane, 0);
    int ranged = crucibleWaveSlot(lane, 1);
    int size = xsArrayGetInt(crucibleWaveSlotCount, melee) + xsArrayGetInt(crucibleWaveSlotCount, ranged);
    int add = size / cCrucibleWaveGrowPer;
    int slot = xsArrayGetInt(crucibleWaveArchetypeMain, xsArrayGetInt(crucibleWaveLaneArchetype, lane));

    if (add < 1) {
        add = 1;
    }

    if (xsGetRandomNumberLH(0, 100) >= cCrucibleWaveMainShare) {
        slot = 1 - slot;
    }

    int k = crucibleWaveSlot(lane, slot);
    xsArraySetInt(crucibleWaveSlotCount, k, xsArrayGetInt(crucibleWaveSlotCount, k) + add);
    xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": +" + add + " "
        + xsArrayGetString(crucibleWaveLineName, xsArrayGetInt(crucibleWaveSlotLine, k)));
}

// ---- the Legion: shared ----

// Some lane fields unit `k` (wave_table units: lines, then siege and the Priest), or may bring it this age.
bool crucibleWaveFielded(int k = 0) {
    if (k < cCrucibleWaveLines) {
        for (s = 0; < cCrucibleWaveLanes * 2) {
            if ((xsArrayGetInt(crucibleWaveSlotLine, s) == k) && (xsArrayGetInt(crucibleWaveSlotCount, s) > 0)) {
                return (true);
            }
        }

        return (false);
    }

    if (crucibleWaveAge < cCrucibleWaveSiegeAge) {
        return (false);
    }

    if (k == cCrucibleWavePriestIndex) {
        return (true);
    }

    for (c = 0; < cCrucibleWaveSiegeChoices) {
        if (xsArrayGetInt(crucibleWaveSiegeIndex, crucibleWaveAge * cCrucibleWaveSiegeChoices + c) == k) {
            return (true);
        }
    }

    return (false);
}

// An upgrade the Legion could take now: not taken, its age reached, what it needs taken, and it improves a unit
// some lane fields.
bool crucibleWaveUpgradeOpen(int u = 0) {
    if ((xsArrayGetInt(crucibleWaveUpgradeTaken, u) == 1) || (xsArrayGetInt(crucibleWaveUpgradeAge, u) > crucibleWaveAge)) {
        return (false);
    }

    int requires = xsArrayGetInt(crucibleWaveUpgradeRequires, u);

    if ((requires >= 0) && (xsArrayGetInt(crucibleWaveUpgradeTaken, requires) == 0)) {
        return (false);
    }

    for (k = 0; < cCrucibleWaveUnits) {
        if ((xsArrayGetInt(crucibleWaveImproves, u * cCrucibleWaveUnits + k) == 1) && crucibleWaveFielded(k)) {
            return (true);
        }
    }

    return (false);
}

// A random open upgrade, researched for the Legion. False if none is open.
bool crucibleWaveUpgrade() {
    int count = 0;

    for (u = 0; < cCrucibleWaveUpgrades) {
        if (crucibleWaveUpgradeOpen(u)) {
            count++;
        }
    }

    if (count == 0) {
        return (false);
    }

    int roll = xsGetRandomNumberLH(0, count);

    for (v = 0; < cCrucibleWaveUpgrades) {
        if (crucibleWaveUpgradeOpen(v)) {
            if (roll == 0) {
                xsArraySetInt(crucibleWaveUpgradeTaken, v, 1);
                crucibleWaveQueueTech(xsArrayGetInt(crucibleWaveUpgradeTech, v));
                xsChatData("Legion: " + xsArrayGetString(crucibleWaveUpgradeName, v));
                return (true);
            }

            roll--;
        }
    }

    return (false);
}

// The Legion's next age; any slot two ages behind it moves one line on.
void crucibleWaveAgeUp() {
    crucibleWaveAge++;
    crucibleWaveAgeChance = cCrucibleWaveAgeUpStart;
    crucibleWaveQueueTech(xsArrayGetInt(crucibleWaveAgeTech, crucibleWaveAge));
    xsChatData("Legion: the " + xsArrayGetString(crucibleWaveAgeName, crucibleWaveAge));

    for (lane = 0; < cCrucibleWaveLanes) {
        for (slot = 0; < 2) {
            int line = xsArrayGetInt(crucibleWaveSlotLine, crucibleWaveSlot(lane, slot));

            if (xsArrayGetInt(crucibleWaveLineAge, line) <= crucibleWaveAge - 2) {
                int next = crucibleWaveNextLine(lane, slot);

                if (next >= 0) {
                    crucibleWaveSetLine(lane, slot, next);
                }
            }
        }
    }
}

int crucibleWaveRollStep() {
    int total = 0;

    for (s = 0; < cCrucibleWaveSteps) {
        total = total + xsArrayGetInt(crucibleWaveStepWeight, s);
    }

    int roll = xsGetRandomNumberLH(0, total);

    for (t = 0; < cCrucibleWaveSteps) {
        roll = roll - xsArrayGetInt(crucibleWaveStepWeight, t);

        if (roll < 0) {
            return (t);
        }
    }

    return (0);
}

// `lane` evolves: one step, or more if a step says again (at most cCrucibleWaveMaxSteps). Steps 0 grow, 1 upgrade,
// 2 swap, 3 nothing, 4 again; an upgrade or swap that can't happen grows instead.
void crucibleWaveEvolve(int lane = 0) {
    int steps = 1;
    int done = 0;
    int step = 0;

    while ((steps > 0) && (done < cCrucibleWaveMaxSteps)) {
        steps--;
        done++;

        if ((crucibleWaveAge < cCrucibleWaveLastAge) && (xsGetRandomNumberLH(0, 100) < crucibleWaveAgeChance)) {
            crucibleWaveAgeUp();
            continue;
        }

        crucibleWaveAgeChance = crucibleWaveAgeChance + cCrucibleWaveAgeUpStep;
        step = crucibleWaveRollStep();

        if (step == 4) {
            xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": evolves again");
            steps = steps + 2;
        } else if (step == 3) {
            xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": no change");
        } else if ((step == 1) && crucibleWaveUpgrade()) {
        } else if ((step == 2) && crucibleWaveSwap(lane)) {
        } else {
            crucibleWaveGrow(lane);
        }
    }
}

// ---- spawning ----

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

// `lane`'s army, and by chance siege and a Priest (they come and go).
void crucibleWaveSpawnGroup(int lane = 0) {
    int n = 0;

    for (slot = 0; < 2) {
        int k = crucibleWaveSlot(lane, slot);
        int unit = xsArrayGetInt(crucibleWaveLineUnit, xsArrayGetInt(crucibleWaveSlotLine, k));

        for (i = 0; < xsArrayGetInt(crucibleWaveSlotCount, k)) {
            crucibleWaveSpawn(lane, n, unit);
            n++;
        }
    }

    if (xsGetRandomNumberLH(0, 100) < xsArrayGetInt(crucibleWaveSiegeChance, crucibleWaveAge)) {
        int kinds = 0;

        for (c = 0; < cCrucibleWaveSiegeChoices) {
            if (xsArrayGetInt(crucibleWaveSiegeUnit, crucibleWaveAge * cCrucibleWaveSiegeChoices + c) >= 0) {
                kinds++;
            }
        }

        if (kinds > 0) {
            int pick = xsGetRandomNumberLH(0, kinds);
            crucibleWaveSpawn(lane, n, xsArrayGetInt(crucibleWaveSiegeUnit, crucibleWaveAge * cCrucibleWaveSiegeChoices + pick));
            n++;
        }
    }

    if (xsGetRandomNumberLH(0, 100) < xsArrayGetInt(crucibleWavePriestChance, crucibleWaveAge)) {
        crucibleWaveSpawn(lane, n, cCrucibleWavePriest);
    }
}

// The current wave's lanes evolve (but for wave 0) and spawn; the triggers walk them in.
void crucibleWaveWalkIn() {
    int set = crucibleWaveLaneSet(crucibleWave);

    xsChatData("Wave " + crucibleWave + " (" + xsArrayGetString(crucibleWaveAgeName, crucibleWaveAge) + ")");

    for (lane = 0; < cCrucibleWaveLanes) {
        if (crucibleWaveLaneIn(lane, set)) {
            if (crucibleWave > 0) {
                crucibleWaveEvolve(lane);
            }

            crucibleWaveSpawnGroup(lane);
        }
    }

    xsSetTriggerVariable(cCrucibleWaveWalkVariable, set);
    crucibleWaveWalkPending = false;
}

// Each lane an archetype, no two the same, and the starting army.
void crucibleWaveSetUpLanes() {
    crucibleWaveLaneArchetype = xsArrayCreateInt(cCrucibleWaveLanes, -1, "crucibleWaveLaneArchetype");
    crucibleWaveSlotLine = xsArrayCreateInt(cCrucibleWaveLanes * 2, 0, "crucibleWaveSlotLine");
    crucibleWaveSlotCount = xsArrayCreateInt(cCrucibleWaveLanes * 2, 0, "crucibleWaveSlotCount");
    bool taken = true;  // declared outside the loop: XS runs a declaration in a loop only once
    int roll = 0;
    string text = "Waves:";

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
        xsArraySetInt(crucibleWaveSlotLine, crucibleWaveSlot(lane, 0), cCrucibleWaveStartMelee);
        xsArraySetInt(crucibleWaveSlotCount, crucibleWaveSlot(lane, 0), cCrucibleWaveStartMeleeCount);
        xsArraySetInt(crucibleWaveSlotLine, crucibleWaveSlot(lane, 1), cCrucibleWaveStartRanged);
        xsArraySetInt(crucibleWaveSlotCount, crucibleWaveSlot(lane, 1), cCrucibleWaveStartRangedCount);
        text = text + " " + xsArrayGetString(crucibleWaveLaneName, lane) + ": "
            + xsArrayGetString(crucibleWaveArchetypeName, roll) + ";";
    }

    xsChatData(text);
}

// ---- waves in play ----

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

// Each sent wave with no unit left alive is defeated: count it once. Wave 0 gives free Poor boons; later waves a
// choice (two every cCrucibleWaveDoubleEvery), with the tier-up chances growing per wave.
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
                crucibleShopTierBonus = crucibleWaveDefeatedCount * cCrucibleWaveTierUpPerWave;

                if (wave == 0) {
                    crucibleShopOpenPoor();  // free Poor boons
                } else {
                    crucibleShopOpen();  // a decision: two boon categories on the Wonder

                    if ((crucibleWaveDefeatedCount % cCrucibleWaveDoubleEvery) == 0) {
                        crucibleShopOpen();
                    }
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
        crucibleWaveSendAt = xsGetTime() + crucibleWaveSendEvery;
        xsSetTriggerVariable(cCrucibleWaveTimerVariable, crucibleWaveDifficulty + 1);
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
    crucibleWaveDefeated = xsArrayCreateInt(cCrucibleWaveCapacity, 0, "crucible wave defeated");
    crucibleWaveLastX = xsArrayCreateFloat(cCrucibleWaveCapacity, -100.0, "crucible wave last x");
    crucibleWaveLastY = xsArrayCreateFloat(cCrucibleWaveCapacity, -100.0, "crucible wave last y");
    crucibleWaveOne = xsArrayCreateInt(1, -1, "crucible wave one");
    crucibleWaveUpgradeTaken = xsArrayCreateInt(cCrucibleWaveUpgrades, 0, "crucible wave upgrade taken");
    crucibleWaveTechQueue = xsArrayCreateInt(cCrucibleWaveTechQueueSize, -1, "crucible wave tech queue");
    int difficulty = xsGetDifficulty();

    if ((difficulty >= 0) && (difficulty < xsArrayGetSize(crucibleWaveDifficultyOf))) {
        crucibleWaveDifficulty = xsArrayGetInt(crucibleWaveDifficultyOf, difficulty);
    } else {
        crucibleWaveDifficulty = xsArrayGetInt(crucibleWaveDifficultyOf, 0);  // Extreme: as Hardest
    }

    crucibleWaveSendEvery = xsArrayGetInt(crucibleWaveSendTime, crucibleWaveDifficulty);
    crucibleWaveSendAt = crucibleWaveSendEvery;
    crucibleWaveAgeChance = cCrucibleWaveAgeUpStart;
    crucibleWaveSetUpLanes();
    xsSetPlayerAttribute(cCrucibleWaveCounterPlayer, cCrucibleWaveCounterRelics, 0);
    xsSetTriggerVariable(cCrucibleWaveTimerVariable, crucibleWaveDifficulty + 1);
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

    crucibleWaveResearchNext();

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
