// ---- crucible run: waves (runtime) ----
// A wave walks in, waits staged (the Send button on), then is sent at its time or on a click; the next walks in.

int crucibleWave = 1;  // the wave walking in or waiting; odd: the Capital's, even: the city states'
bool crucibleWaveReady = false;  // staged, button on
bool crucibleWaveArmed = false;  // the button has been seen ready since it was put on (a click is real)
int crucibleWaveSendAt = cCrucibleWaveSendTime;
int crucibleWaveUnits = -1;  // reused array (xsGetPlayerUnitIds with -1 makes a new one)

// every sent unit and its wave, to tell when a wave is defeated
const int cCrucibleWaveCapacity = 4000;
int crucibleWaveSentIds = -1;
int crucibleWaveSentWave = -1;
int crucibleWaveSentCount = 0;
int crucibleWaveDefeated = -1;  // by wave number: 1 once defeated
int crucibleWaveDefeatedCount = 0;

bool crucibleWaveCapital() {
    return ((crucibleWave % 2) == 1);
}

// Every wave unit still between its spawn row and its staging row is on the staging row (and there is one).
bool crucibleWaveStaged() {
    int walking = 0;
    int waiting = 0;
    vector pos = cInvalidVector;
    bool capital = crucibleWaveCapital();
    crucibleWaveUnits = xsGetPlayerUnitIds(cCrucibleWaveLegion, cCrucibleWaveUnit, crucibleWaveUnits);

    for (i = 0; < xsArrayGetSize(crucibleWaveUnits)) {
        pos = xsGetUnitPosition(xsArrayGetInt(crucibleWaveUnits, i));

        if (capital) {
            if (crucibleWaveCapitalCorridor(pos)) { walking++; }
            if (crucibleWaveCapitalStaged(pos)) { waiting++; }
        } else {
            if (crucibleWaveCityStatesCorridor(pos)) { walking++; }
            if (crucibleWaveCityStatesStaged(pos)) { waiting++; }
        }
    }

    return ((walking > 0) && (waiting == walking));
}

// Note the wave's units (still between spawn and staging) as sent with this wave.
void crucibleWaveRecord() {
    vector pos = cInvalidVector;
    bool capital = crucibleWaveCapital();
    bool mine = false;
    int id = -1;
    crucibleWaveUnits = xsGetPlayerUnitIds(cCrucibleWaveLegion, cCrucibleWaveUnit, crucibleWaveUnits);

    for (i = 0; < xsArrayGetSize(crucibleWaveUnits)) {
        id = xsArrayGetInt(crucibleWaveUnits, i);
        pos = xsGetUnitPosition(id);

        if (capital) {
            mine = crucibleWaveCapitalCorridor(pos);
        } else {
            mine = crucibleWaveCityStatesCorridor(pos);
        }

        if (mine && (crucibleWaveSentCount < cCrucibleWaveCapacity)) {
            xsArraySetInt(crucibleWaveSentIds, crucibleWaveSentCount, id);
            xsArraySetInt(crucibleWaveSentWave, crucibleWaveSentCount, crucibleWave);
            crucibleWaveSentCount++;
        }
    }
}

bool crucibleWaveAlive(int id = -1) {
    if (xsDoesUnitExist(id) == false) {
        return (false);
    }

    return (xsGetUnitProperty(id, cUnitHitpoints) > 0);
}

// Each sent wave with no unit left alive is defeated: count it once.
void crucibleWaveCountDefeated() {
    bool alive = false;  // declared outside the loop: XS runs a declaration in a loop only once

    for (wave = 1; < crucibleWave) {
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
                xsSetPlayerAttribute(cCrucibleWaveCounterPlayer, cCrucibleWaveCounterResource, crucibleWaveDefeatedCount);
                xsChatData("Wave %d defeated", wave);
            }
        }
    }
}

void crucibleWaveSend() {
    crucibleWaveRecord();

    if (crucibleWaveCapital()) {
        xsSetTriggerVariable(cCrucibleWaveOrderVariable, 3);
    } else {
        xsSetTriggerVariable(cCrucibleWaveOrderVariable, 4);
    }

    xsSetTriggerVariable(cCrucibleWaveButtonVariable, 2);
    crucibleWave++;
    crucibleWaveReady = false;
    crucibleWaveArmed = false;
    crucibleWaveSendAt = xsGetTime() + cCrucibleWaveSendTime;
}

rule crucibleWaveStart
    active
    highFrequency
{
    crucibleWaveSentIds = xsArrayCreateInt(cCrucibleWaveCapacity, -1, "crucible wave sent ids");
    crucibleWaveSentWave = xsArrayCreateInt(cCrucibleWaveCapacity, 0, "crucible wave sent wave");
    crucibleWaveDefeated = xsArrayCreateInt(1000, 0, "crucible wave defeated");
    xsSetPlayerAttribute(cCrucibleWaveCounterPlayer, cCrucibleWaveCounterResource, 0);
    xsSetTriggerVariable(cCrucibleWaveOrderVariable, 1);
    xsDisableSelf();
}

rule crucibleWaves
    active
    minInterval 1
{
    int state = xsGetTechState(cCrucibleWaveButton, 1);

    if ((crucibleWaveReady == false) && crucibleWaveStaged()) {
        xsSetTriggerVariable(cCrucibleWaveButtonVariable, 1);
        crucibleWaveReady = true;
    }

    if (crucibleWaveReady && (state == cTechStateReady)) {
        crucibleWaveArmed = true;
    }

    if ((crucibleWaveArmed && (state == cTechStateDone)) || (xsGetTime() >= crucibleWaveSendAt)) {
        crucibleWaveSend();
    }

    crucibleWaveCountDefeated();
}
