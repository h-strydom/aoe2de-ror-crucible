// ---- Crucible shop: runtime (the generated data block comes first) ----
// crucibleShopOpen() after a wave (or a base) grants cCrucibleChoices choices. Each choice: two categories on the choice
// buttons, from different tag axes (a combat boon, a Stable boon); a click locks in (the other is disabled); when the
// pick finishes, each boon slot on row 1 gets a random boon of that category, at its lowest tier or, by the tier-up
// roll, a better one (at that tier's price); boons stack on a slot, and the next choice (if any are left) appears on
// the same buttons. crucibleShopOpenPoor() (wave 0) skips the choice: each slot gets a random boon with a Poor tier,
// of any category, at that tier (free), no tier-up roll.

int crucibleShopState = 0;  // 0 closed, 1 choosing, 2 picked
int crucibleShopCategory1 = -1;
int crucibleShopCategory2 = -1;
int crucibleShopPicked = 0;  // the choice clicked: 1 or 2
int crucibleShopChoices = 0;  // choices still to make
bool crucibleShopReady = false;
bool crucibleShopPoor = false;  // a Poor offer is being made

void crucibleShopInit() {
    if (crucibleShopReady) {
        return;
    }

    crucibleShopData();
    xsEffectAmount(cDisableTech, cCrucibleChoice1, cAttributeDisable, 0, 1);
    xsEffectAmount(cDisableTech, cCrucibleChoice2, cAttributeDisable, 0, 1);
    crucibleShopReady = true;
}

int crucibleShopChoice(int number = 1) {
    if (number == 1) {
        return (cCrucibleChoice1);
    }

    return (cCrucibleChoice2);
}

// A boon that can be offered now: not offered yet, and with a Poor tier if the offer is a Poor one.
bool crucibleShopOfferable(int boon = 0) {
    if (xsArrayGetInt(crucibleBoonTaken, boon) == 1) {
        return (false);
    }

    return ((crucibleShopPoor == false) || (xsArrayGetInt(crucibleBoonLowest, boon) == 0));
}

// A boon is of `category`; every boon is of category -1.
bool crucibleShopMember(int category = 0, int boon = 0) {
    if (category < 0) {
        return (true);
    }

    return (xsArrayGetInt(crucibleBoonMember, category * cCrucibleBoons + boon) == 1);
}

// Boons of a category that can be offered now.
int crucibleShopAvailable(int category = 0) {
    int count = 0;

    for (boon = 0; < cCrucibleBoons) {
        if (crucibleShopMember(category, boon)) {
            if (crucibleShopOfferable(boon)) {
                count = count + 1;
            }
        }
    }

    return (count);
}

// A random category with boons left, not of axis `skipAxis`; -1 if none.
int crucibleShopRandomCategory(int skipAxis = -1) {
    int count = 0;

    for (a = 0; < cCrucibleCategories) {
        if ((xsArrayGetInt(crucibleCategoryAxis, a) != skipAxis) && (crucibleShopAvailable(a) > 0)) {
            count = count + 1;
        }
    }

    if (count == 0) {
        return (-1);
    }

    int roll = xsGetRandomNumberLH(0, count);

    for (b = 0; < cCrucibleCategories) {
        if ((xsArrayGetInt(crucibleCategoryAxis, b) != skipAxis) && (crucibleShopAvailable(b) > 0)) {
            if (roll == 0) {
                return (b);
            }

            roll = roll - 1;
        }
    }

    return (-1);
}

void crucibleShopName(int number = 1, int category = 0) {
    int tech = crucibleShopChoice(number);
    string name = xsArrayGetString(crucibleCategoryName, category);
    int count = crucibleShopAvailable(category);

    xsSetTechName(tech, 1, name + " boons (" + count + ")");
    xsSetTechDescription(tech, 1, "Choose from " + count + " " + name + " boons.");
}

// Show the next choice: two categories with boons left on the choice buttons, from different axes.
void crucibleShopShow() {
    crucibleShopCategory1 = crucibleShopRandomCategory(-1);

    if (crucibleShopCategory1 < 0) {
        xsChatData("Shop: no boons left");
        crucibleShopChoices = 0;
        return;
    }

    crucibleShopCategory2 = crucibleShopRandomCategory(xsArrayGetInt(crucibleCategoryAxis, crucibleShopCategory1));
    crucibleShopName(1, crucibleShopCategory1);

    if (crucibleShopCategory2 < 0) {
        xsSetTriggerVariable(cCrucibleChoicesVariable, 1);  // only choice 1
    } else {
        crucibleShopName(2, crucibleShopCategory2);
        xsSetTriggerVariable(cCrucibleChoicesVariable, 2);  // both
    }

    crucibleShopState = 1;
    xsChatData("Shop: choose a boon category on the Wonder");
}

// A wave is defeated: grant its choices, and show one unless a choice is already up.
void crucibleShopOpen() {
    crucibleShopInit();
    crucibleShopChoices = crucibleShopChoices + cCrucibleChoices;

    if (crucibleShopState == 0) {
        crucibleShopShow();
    }
}


// A random boon of the category that can be offered now; -1 if none.
int crucibleShopBoon(int category = 0) {
    int count = crucibleShopAvailable(category);

    if (count == 0) {
        return (-1);
    }

    int roll = xsGetRandomNumberLH(0, count);

    for (boon = 0; < cCrucibleBoons) {
        if (crucibleShopMember(category, boon)) {
            if (crucibleShopOfferable(boon)) {
                if (roll == 0) {
                    return (boon);
                }

                roll = roll - 1;
            }
        }
    }

    return (-1);
}

// How many tiers up the roll gives: each (tiers, chance) in turn takes its slice of 100.
int crucibleShopTiersUp() {
    int roll = xsGetRandomNumberLH(0, 100);

    for (i = 0; < cCrucibleTierUps) {
        int chance = xsArrayGetInt(crucibleTierUpChance, i);

        if (roll < chance) {
            return (xsArrayGetInt(crucibleTierUpSteps, i));
        }

        roll = roll - chance;
    }

    return (0);
}

// The tech of the boon's rolled tier: its lowest, up by the roll, down to the best tier it has a tech for.
int crucibleShopTierTech(int boon = 0) {
    int lowest = xsArrayGetInt(crucibleBoonLowest, boon);
    int tier = lowest;

    if (crucibleShopPoor == false) {
        tier = lowest + crucibleShopTiersUp();
    }

    if (tier >= cCrucibleTiers) {
        tier = cCrucibleTiers - 1;
    }

    while (tier >= lowest) {
        int tech = xsArrayGetInt(crucibleBoonTier, boon * cCrucibleTiers + tier);

        if (tech >= 0) {
            if (tier > lowest) {
                xsChatData("Shop: a boon rolled %d tiers up", tier - lowest);
            }

            return (tech);
        }

        tier = tier - 1;
    }

    return (-1);
}

// A meta upgrade's level, read when needed (the bank loads it at the start); 0 without one.
int crucibleShopMeta(int variable = -1) {
    if (variable < 0) {
        return (0);
    }

    return (xsTriggerVariable(variable));
}

// One boon of the category on each slot. Boons stack on a slot: the one on top researches, then the next shows.
void crucibleShopOffer(int category = 0) {
    int offered = 0;
    int slots = cCrucibleSlots + crucibleShopMeta(cCrucibleSlotsVariable);
    int speed = crucibleShopMeta(cCrucibleSpeedVariable);
    int time = cCrucibleBoonTime * (cCrucibleSpeedTiers - speed) / cCrucibleSpeedTiers;

    if (slots > cCrucibleMaxSlots) {
        slots = cCrucibleMaxSlots;
    }

    if (time < 1) {
        time = 1;  // at 0 the game researches a tech by itself
    }

    for (slot = 0; < slots) {
        int boon = crucibleShopBoon(category);

        if (boon >= 0) {
            int tech = crucibleShopTierTech(boon);

            xsEffectAmount(cModifyTech, tech, cAttrSetTime, time, 1);
            xsEffectAmount(cModifyTech, tech, cAttrSetLocation, cCrucibleWonder, 1);
            xsEffectAmount(cModifyTech, tech, cAttrSetButton, slot + 1, 1);
            xsArraySetInt(crucibleBoonTaken, boon, 1);
            offered = offered + 1;
        }
    }

    xsChatData("Shop: %d boons offered", offered);
}

// Wave 0 is defeated: no choice, a free Poor boon of any category on each slot.
void crucibleShopOpenPoor() {
    crucibleShopInit();
    crucibleShopPoor = true;
    crucibleShopOffer(-1);
    crucibleShopPoor = false;
}

rule crucibleShop
    active
    highFrequency
{
    crucibleShopInit();

    if (crucibleShopState == 1) {
        for (number = 1; < 3) {
            int techState = xsGetTechState(crucibleShopChoice(number), 1);

            if ((crucibleShopPicked == 0) && ((techState == cTechStateResearching) || (techState == cTechStateQueued))) {
                crucibleShopPicked = number;
                xsEffectAmount(cDisableTech, crucibleShopChoice(3 - number), cAttributeDisable, 0, 1);
                crucibleShopState = 2;
            }
        }

        return;
    }

    if ((crucibleShopState == 2) && (xsGetTechState(crucibleShopChoice(crucibleShopPicked), 1) == cTechStateDone)) {
        if (crucibleShopPicked == 1) {
            crucibleShopOffer(crucibleShopCategory1);
        } else {
            crucibleShopOffer(crucibleShopCategory2);
        }

        crucibleShopPicked = 0;
        crucibleShopState = 0;
        crucibleShopChoices = crucibleShopChoices - 1;

        if (crucibleShopChoices > 0) {
            crucibleShopShow();
        }
    }
}
