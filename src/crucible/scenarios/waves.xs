// ---- crucible run: waves (runtime) ----
// A wave spawns and walks in, waits staged (the Send button on), then is sent at its time or on a click; the next
// spawns. Wave 0 is sent as soon as it's staged, without moving the clock. Before a lane spawns (but for wave 0) its
// army takes a step: age up (shared), grow, upgrade (shared), swap (along its path), nothing, or again; each done
// `scale` times. The data block (wave_table) comes first.

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
int crucibleWaveFamilyLevel = -1;  // by family: the line it's upgraded to
int crucibleWaveTechQueue = -1;  // techs for the triggers to research, one at a time
int crucibleWaveTechHead = 0;
int crucibleWaveTechTail = 0;
const int cCrucibleWaveTechQueueSize = 64;

// each lane: its archetype; each slot (lane * 2 + slot): its path (families, -1 past the end), where on it, how many
int crucibleWaveLaneArchetype = -1;
int crucibleWaveChain = -1;  // (lane * 2 + slot) * cCrucibleWaveStages + stage
int crucibleWaveChainPos = -1;
int crucibleWaveSlotCount = -1;

// every spawned unit and its wave, to tell when a wave is staged and when it is defeated
const int cCrucibleWaveCapacity = 8000;
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

// ---- families and slots ----

int crucibleWaveSlot(int lane = 0, int slot = 0) {
    return (lane * 2 + slot);
}

bool crucibleWaveIsMain(int lane = 0, int slot = 0) {
    return (xsArrayGetInt(crucibleWaveArchetypeMain, xsArrayGetInt(crucibleWaveLaneArchetype, lane)) == slot);
}

// The family slot `k` (lane * 2 + slot) holds.
int crucibleWaveSlotFamily(int k = 0) {
    return (xsArrayGetInt(crucibleWaveChain, k * cCrucibleWaveStages + xsArrayGetInt(crucibleWaveChainPos, k)));
}

// The furthest line of `family` a slot may field: a support slot stops before the main-only lines.
int crucibleWaveCap(int family = 0, bool main = true) {
    if (main) {
        return (xsArrayGetInt(crucibleWaveCapMain, family));
    }

    return (xsArrayGetInt(crucibleWaveCapSupport, family));
}

int crucibleWaveLineOf(int family = 0, bool main = true) {
    int line = xsArrayGetInt(crucibleWaveFamilyLevel, family);
    int cap = crucibleWaveCap(family, main);

    if (line > cap) {
        line = cap;
    }

    return (line);
}

// The unit (wave_table.units index) `family` fields in a main or support slot.
int crucibleWaveFamilyUnit(int family = 0, bool main = true) {
    return (xsArrayGetInt(crucibleWaveLineUnit, family * cCrucibleWaveLines + crucibleWaveLineOf(family, main)));
}

int crucibleWaveSlotUnit(int lane = 0, int slot = 0) {
    return (crucibleWaveFamilyUnit(crucibleWaveSlotFamily(crucibleWaveSlot(lane, slot)), crucibleWaveIsMain(lane, slot)));
}

string crucibleWaveSlotName(int lane = 0, int slot = 0) {
    return (xsArrayGetString(crucibleWaveUnitName, crucibleWaveSlotUnit(lane, slot)));
}

bool crucibleWaveSiegeOpen(int family = 0) {
    return ((xsArrayGetInt(crucibleWaveFamilySlot, family) == cCrucibleWaveSiegeSlot)
        && (xsArrayGetInt(crucibleWaveLineAge, family * cCrucibleWaveLines) <= crucibleWaveAge));
}

// The slot can move on along its path: a next family, open in the Legion's age.
bool crucibleWaveCanAdvance(int lane = 0, int slot = 0) {
    int k = crucibleWaveSlot(lane, slot);
    int pos = xsArrayGetInt(crucibleWaveChainPos, k);

    if (pos + 1 >= cCrucibleWaveStages) {
        return (false);
    }

    int next = xsArrayGetInt(crucibleWaveChain, k * cCrucibleWaveStages + pos + 1);

    if (next < 0) {
        return (false);
    }

    return (xsArrayGetInt(crucibleWaveLineAge, next * cCrucibleWaveLines) <= crucibleWaveAge);
}

void crucibleWaveAdvance(int lane = 0, int slot = 0, string why = "swap") {
    int k = crucibleWaveSlot(lane, slot);
    string from = xsArrayGetString(crucibleWaveFamilyName, crucibleWaveSlotFamily(k));
    xsArraySetInt(crucibleWaveChainPos, k, xsArrayGetInt(crucibleWaveChainPos, k) + 1);
    xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + " " + why + ": " + from + " become "
        + xsArrayGetString(crucibleWaveFamilyName, crucibleWaveSlotFamily(k)) + " (" + crucibleWaveSlotName(lane, slot)
        + ")");
}

// Move one slot on along its path. False if neither can.
bool crucibleWaveSwap(int lane = 0) {
    int count = 0;

    for (slot = 0; < 2) {
        if (crucibleWaveCanAdvance(lane, slot)) {
            count++;
        }
    }

    if (count == 0) {
        return (false);
    }

    int roll = xsGetRandomNumberLH(0, count);

    for (s = 0; < 2) {
        if (crucibleWaveCanAdvance(lane, s)) {
            if (roll == 0) {
                crucibleWaveAdvance(lane, s, "swap");
                return (true);
            }

            roll--;
        }
    }

    return (false);
}

void crucibleWaveGrow(int lane = 0, int add = 1) {
    int slot = xsArrayGetInt(crucibleWaveArchetypeMain, xsArrayGetInt(crucibleWaveLaneArchetype, lane));

    if (xsGetRandomNumberLH(0, 100) >= cCrucibleWaveMainShare) {
        slot = 1 - slot;
    }

    int k = crucibleWaveSlot(lane, slot);
    xsArraySetInt(crucibleWaveSlotCount, k, xsArrayGetInt(crucibleWaveSlotCount, k) + add);
    xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": +" + add + " " + crucibleWaveSlotName(lane, slot));
}

// ---- the Legion: shared ----

// Some lane fields unit `k` (wave_table.units index), or the Legion may bring it this age (siege, the Priest).
bool crucibleWaveFielded(int k = 0) {
    for (lane = 0; < cCrucibleWaveLanes) {
        for (slot = 0; < 2) {
            if ((xsArrayGetInt(crucibleWaveSlotCount, crucibleWaveSlot(lane, slot)) > 0)
                && (crucibleWaveSlotUnit(lane, slot) == k)) {
                return (true);
            }
        }
    }

    if (crucibleWaveAge < cCrucibleWaveSiegeAge) {
        return (false);
    }

    if (k == cCrucibleWavePriest) {
        return (true);
    }

    for (f = 0; < cCrucibleWaveFamilies) {
        if (crucibleWaveSiegeOpen(f) && (crucibleWaveFamilyUnit(f, true) == k)) {
            return (true);
        }
    }

    return (false);
}

// The furthest line of `family` any slot fielding it may take (siege: all); -1 if nothing fields it.
int crucibleWaveReach(int family = 0) {
    if (crucibleWaveSiegeOpen(family)) {
        return (xsArrayGetInt(crucibleWaveFamilyLines, family) - 1);
    }

    int reach = -1;

    for (lane = 0; < cCrucibleWaveLanes) {
        for (slot = 0; < 2) {
            int k = crucibleWaveSlot(lane, slot);

            if ((xsArrayGetInt(crucibleWaveSlotCount, k) > 0) && (crucibleWaveSlotFamily(k) == family)) {
                int cap = crucibleWaveCap(family, crucibleWaveIsMain(lane, slot));

                if (cap > reach) {
                    reach = cap;
                }
            }
        }
    }

    return (reach);
}

// A stat upgrade the Legion could take now: not taken, its age reached, what it needs taken, and it improves a unit
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

// A family's next line is open: some slot fielding it may take it, and the Legion's age has reached it.
bool crucibleWaveLineUpOpen(int family = 0) {
    int next = xsArrayGetInt(crucibleWaveFamilyLevel, family) + 1;

    if ((next >= xsArrayGetInt(crucibleWaveFamilyLines, family)) || (next > crucibleWaveReach(family))) {
        return (false);
    }

    return (xsArrayGetInt(crucibleWaveLineAge, family * cCrucibleWaveLines + next) <= crucibleWaveAge);
}

// A random open upgrade (a line upgrade cCrucibleWaveLineWeight times as likely). False if none is open.
bool crucibleWaveUpgrade() {
    int total = 0;

    for (u = 0; < cCrucibleWaveUpgrades) {
        if (crucibleWaveUpgradeOpen(u)) {
            total++;
        }
    }

    for (f = 0; < cCrucibleWaveFamilies) {
        if (crucibleWaveLineUpOpen(f)) {
            total = total + cCrucibleWaveLineWeight;
        }
    }

    if (total == 0) {
        return (false);
    }

    int roll = xsGetRandomNumberLH(0, total);

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

    for (g = 0; < cCrucibleWaveFamilies) {
        if (crucibleWaveLineUpOpen(g)) {
            if (roll < cCrucibleWaveLineWeight) {
                string from = xsArrayGetString(crucibleWaveUnitName, crucibleWaveFamilyUnit(g, true));
                xsArraySetInt(crucibleWaveFamilyLevel, g, xsArrayGetInt(crucibleWaveFamilyLevel, g) + 1);
                xsChatData("Legion: " + from + " become "
                    + xsArrayGetString(crucibleWaveUnitName, crucibleWaveFamilyUnit(g, true)));
                return (true);
            }

            roll = roll - cCrucibleWaveLineWeight;
        }
    }

    return (false);
}

// The Legion's next age; with move-on, every lane's main slot moves on as far as the new age opens its path.
void crucibleWaveAgeUp() {
    crucibleWaveAge++;
    crucibleWaveAgeChance = cCrucibleWaveAgeUpStart;
    crucibleWaveQueueTech(xsArrayGetInt(crucibleWaveAgeTech, crucibleWaveAge));
    xsChatData("Legion: the " + xsArrayGetString(crucibleWaveAgeName, crucibleWaveAge));

    if (cCrucibleWaveMoveOn == false) {
        return;
    }

    for (lane = 0; < cCrucibleWaveLanes) {
        for (slot = 0; < 2) {
            if (crucibleWaveIsMain(lane, slot)) {
                for (step = 0; < cCrucibleWaveStages) {
                    if (crucibleWaveCanAdvance(lane, slot)) {
                        crucibleWaveAdvance(lane, slot, "moves on");
                    }
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
// 2 swap, 3 nothing, 4 again; each done `scale` times; an upgrade or swap that can't happen grows instead.
void crucibleWaveEvolve(int lane = 0) {
    int scale = 1 + crucibleWave / cCrucibleWaveScaleEvery;
    int steps = 1;
    int done = 0;
    int step = 0;
    int n = 0;

    while ((steps > 0) && (done < cCrucibleWaveMaxSteps)) {
        steps--;
        done++;

        if ((crucibleWaveAge < cCrucibleWaveLastAge) && (xsGetRandomNumberLH(0, 100) < crucibleWaveAgeChance)) {
            crucibleWaveAgeUp();
            continue;
        }

        crucibleWaveAgeChance = crucibleWaveAgeChance + cCrucibleWaveAgeUpStep;
        step = crucibleWaveRollStep();
        n = 0;

        if (step == 4) {
            xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": evolves again");
            steps = steps + 2;
        } else if (step == 3) {
            xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": no change");
        } else if (step == 1) {
            for (i = 0; < scale * cCrucibleWaveUpgradeScale) {
                if (crucibleWaveUpgrade()) {
                    n++;
                }
            }

            if (n == 0) {
                crucibleWaveGrow(lane, scale * cCrucibleWaveGrowScale);
            }
        } else if (step == 2) {
            for (j = 0; < scale * cCrucibleWaveSwapScale) {
                if (crucibleWaveSwap(lane)) {
                    n++;
                }
            }

            if (n == 0) {
                crucibleWaveGrow(lane, scale * cCrucibleWaveGrowScale);
            }
        } else {
            crucibleWaveGrow(lane, scale * cCrucibleWaveGrowScale);
        }
    }
}

// ---- spawning ----

// Spawn unit `k` (wave_table.units index) as the `n`th of its group on `lane`: rows of cCrucibleWaveColumns, inwards
// from the spawn row.
void crucibleWaveSpawn(int lane = 0, int n = 0, int k = -1) {
    if (k < 0) {
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
    int unit = xsArrayGetInt(crucibleWaveUnitId, k);
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

// `lane`'s army, and by chance a siege unit and a Priest (they come and go).
void crucibleWaveSpawnGroup(int lane = 0) {
    int n = 0;

    for (slot = 0; < 2) {
        int unit = crucibleWaveSlotUnit(lane, slot);

        for (i = 0; < xsArrayGetInt(crucibleWaveSlotCount, crucibleWaveSlot(lane, slot))) {
            crucibleWaveSpawn(lane, n, unit);
            n++;
        }
    }

    if (xsGetRandomNumberLH(0, 100) < xsArrayGetInt(crucibleWaveSiegeChance, crucibleWaveAge)) {
        int kinds = 0;

        for (f = 0; < cCrucibleWaveFamilies) {
            if (crucibleWaveSiegeOpen(f)) {
                kinds++;
            }
        }

        if (kinds > 0) {
            int pick = xsGetRandomNumberLH(0, kinds);

            for (g = 0; < cCrucibleWaveFamilies) {
                if (crucibleWaveSiegeOpen(g)) {
                    if (pick == 0) {
                        crucibleWaveSpawn(lane, n, crucibleWaveFamilyUnit(g, true));
                        n++;
                    }

                    pick--;
                }
            }
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

// A slot's path: one of its archetype's paths, and at each stage one of its options (rolled once, at the start).
void crucibleWaveRollPath(int lane = 0, int slot = 0) {
    int archetype = xsArrayGetInt(crucibleWaveLaneArchetype, lane);
    int k = crucibleWaveSlot(lane, slot);
    int path = xsGetRandomNumberLH(0, xsArrayGetInt(crucibleWavePathCount, archetype * 2 + slot));
    int base = ((archetype * 2 + slot) * cCrucibleWavePaths + path) * cCrucibleWaveStages * cCrucibleWaveOptions;
    int options = 0;
    int family = 0;
    bool ended = false;  // declared outside the loop: XS runs a declaration in a loop only once

    for (stage = 0; < cCrucibleWaveStages) {
        options = 0;

        for (o = 0; < cCrucibleWaveOptions) {
            if (xsArrayGetInt(crucibleWavePath, base + stage * cCrucibleWaveOptions + o) != -2) {
                options++;
            }
        }

        if ((options == 0) || ended) {
            ended = true;
        } else {
            family = xsArrayGetInt(crucibleWavePath, base + stage * cCrucibleWaveOptions + xsGetRandomNumberLH(0, options));

            if (family < 0) {
                ended = true;
            } else {
                xsArraySetInt(crucibleWaveChain, k * cCrucibleWaveStages + stage, family);
            }
        }
    }
}

// Each lane an archetype, no two the same; its paths; its starting army; its caption.
void crucibleWaveSetUpLanes() {
    crucibleWaveLaneArchetype = xsArrayCreateInt(cCrucibleWaveLanes, -1, "crucibleWaveLaneArchetype");
    crucibleWaveChain = xsArrayCreateInt(cCrucibleWaveLanes * 2 * cCrucibleWaveStages, -1, "crucibleWaveChain");
    crucibleWaveChainPos = xsArrayCreateInt(cCrucibleWaveLanes * 2, 0, "crucibleWaveChainPos");
    crucibleWaveSlotCount = xsArrayCreateInt(cCrucibleWaveLanes * 2, cCrucibleWaveStartCount, "crucibleWaveSlotCount");
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
        crucibleWaveRollPath(lane, 0);
        crucibleWaveRollPath(lane, 1);
        xsSetTriggerVariable(crucibleWaveLaneVariable(lane), roll + 1);  // the lane's caption
        xsChatData(xsArrayGetString(crucibleWaveLaneName, lane) + ": " + xsArrayGetString(crucibleWaveArchetypeName, roll));
    }
}

// ---- waves in play ----

bool crucibleWaveAlive(int id = -1) {
    if (xsDoesUnitExist(id) == false) {
        return (false);
    }

    return (xsGetUnitProperty(id, cUnitHitpoints) > 0);
}

// Every living unit of the current wave has walked in: out of its spawn rows, and on a staging row or standing still
// (a big group's formation is wider than the row). Checked once a second; the first check counts as moving.
bool crucibleWaveStaged() {
    int walking = 0;
    int waiting = 0;
    int id = -1;
    vector pos = cInvalidVector;
    float dx = 0.0;
    float dy = 0.0;
    bool moved = false;

    for (i = 0; < crucibleWaveSentCount) {
        if (xsArrayGetInt(crucibleWaveSentWave, i) == crucibleWave) {
            id = xsArrayGetInt(crucibleWaveSentIds, i);

            if (crucibleWaveAlive(id)) {
                walking++;
                pos = xsGetUnitPosition(id);
                dx = xsVectorGetX(pos) - xsArrayGetFloat(crucibleWaveLastX, i);
                dy = xsVectorGetY(pos) - xsArrayGetFloat(crucibleWaveLastY, i);
                moved = (dx * dx + dy * dy) > 0.09;
                xsArraySetFloat(crucibleWaveLastX, i, xsVectorGetX(pos));
                xsArraySetFloat(crucibleWaveLastY, i, xsVectorGetY(pos));

                if ((crucibleWaveInSpawnRows(pos) == false) && (crucibleWaveStagedAt(pos) || (moved == false))) {
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
    crucibleWaveFamilyLevel = xsArrayCreateInt(cCrucibleWaveFamilies, 0, "crucible wave family level");
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
