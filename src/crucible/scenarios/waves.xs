// ---- crucible run: waves (runtime) ----
// A wave walks in, waits staged (the Send button on), then is sent at its time or on a click; the next walks in.

int crucibleWave = 1;  // the wave walking in or waiting; odd: the Capital's, even: the city states'
bool crucibleWaveReady = false;  // staged, button on
bool crucibleWaveArmed = false;  // the button has been seen ready since it was put on (a click is real)
int crucibleWaveSendAt = cCrucibleWaveSendTime;
int crucibleWaveUnits = -1;  // reused array (xsGetPlayerUnitIds with -1 makes a new one)

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

void crucibleWaveSend() {
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
}
