// ---- Crucible shop: runtime (the generated data block comes first) ----
// crucibleShopOpen() after a wave grants cCrucibleChoices choices. Each choice: two categories on the choice buttons;
// a click locks in (the other is disabled); when the pick finishes, each boon slot on row 1 gets a boon of that
// category, stacking on the ones there, and the next choice (if any are left) appears on the same buttons.

int crucibleShopState = 0;  // 0 closed, 1 choosing, 2 picked
int crucibleShopCategory1 = -1;
int crucibleShopCategory2 = -1;
int crucibleShopPicked = 0;  // the choice clicked: 1 or 2
int crucibleShopChoices = 0;  // choices still to make
bool crucibleShopReady = false;

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

// Boons of a category (and rarity, unless -1) that haven't been offered yet.
int crucibleShopAvailable(int category = 0, int rarity = -1) {
    int count = 0;

    for (boon = 0; < cCrucibleBoons) {
        if (xsArrayGetInt(crucibleBoonMember, category * cCrucibleBoons + boon) == 1) {
            if (xsArrayGetInt(crucibleBoonTaken, boon) == 0) {
                if ((rarity < 0) || (xsArrayGetInt(crucibleBoonRarity, boon) == rarity)) {
                    count = count + 1;
                }
            }
        }
    }

    return (count);
}

// A random category with boons left, other than `skip`; -1 if none.
int crucibleShopRandomCategory(int skip = -1) {
    int count = 0;

    for (a = 0; < cCrucibleCategories) {
        if ((a != skip) && (crucibleShopAvailable(a, -1) > 0)) {
            count = count + 1;
        }
    }

    if (count == 0) {
        return (-1);
    }

    int roll = xsGetRandomNumberLH(0, count);

    for (b = 0; < cCrucibleCategories) {
        if ((b != skip) && (crucibleShopAvailable(b, -1) > 0)) {
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
    int count = crucibleShopAvailable(category, -1);

    xsSetTechName(tech, 1, name + " boons (" + count + ")");
    xsSetTechDescription(tech, 1, "Choose from " + count + " " + name + " boons (choices left: " + crucibleShopChoices + ").");
}

// Show the next choice: two categories with boons left on the choice buttons.
void crucibleShopShow() {
    crucibleShopCategory1 = crucibleShopRandomCategory(-1);

    if (crucibleShopCategory1 < 0) {
        xsChatData("Shop: no boons left");
        crucibleShopChoices = 0;
        return;
    }

    crucibleShopCategory2 = crucibleShopRandomCategory(crucibleShopCategory1);
    crucibleShopName(1, crucibleShopCategory1);

    if (crucibleShopCategory2 < 0) {
        xsSetTriggerVariable(cCrucibleChoicesVariable, 1);  // only choice 1
    } else {
        crucibleShopName(2, crucibleShopCategory2);
        xsSetTriggerVariable(cCrucibleChoicesVariable, 2);  // both
    }

    crucibleShopState = 1;
    xsChatData("Shop: choose (choices left: %d)", crucibleShopChoices);
}

// A wave is defeated: grant its choices, and show one unless a choice is already up.
void crucibleShopOpen() {
    crucibleShopInit();
    crucibleShopChoices = crucibleShopChoices + cCrucibleChoices;

    if (crucibleShopState == 0) {
        crucibleShopShow();
    }
}

// A rarity drawn by points among those the category still has; -1 if none.
int crucibleShopRarity(int category = 0) {
    int total = 0;

    for (a = 0; < cCrucibleRarities) {
        if (crucibleShopAvailable(category, a) > 0) {
            total = total + xsArrayGetInt(crucibleRarityPoints, a);
        }
    }

    if (total == 0) {
        return (-1);
    }

    int roll = xsGetRandomNumberLH(0, total);

    for (b = 0; < cCrucibleRarities) {
        if (crucibleShopAvailable(category, b) > 0) {
            int points = xsArrayGetInt(crucibleRarityPoints, b);

            if (roll < points) {
                return (b);
            }

            roll = roll - points;
        }
    }

    return (-1);
}

// A random boon of the category and rarity that hasn't been offered; -1 if none.
int crucibleShopBoon(int category = 0, int rarity = 0) {
    int count = crucibleShopAvailable(category, rarity);

    if (count == 0) {
        return (-1);
    }

    int roll = xsGetRandomNumberLH(0, count);

    for (boon = 0; < cCrucibleBoons) {
        if (xsArrayGetInt(crucibleBoonMember, category * cCrucibleBoons + boon) == 1) {
            if ((xsArrayGetInt(crucibleBoonTaken, boon) == 0) && (xsArrayGetInt(crucibleBoonRarity, boon) == rarity)) {
                if (roll == 0) {
                    return (boon);
                }

                roll = roll - 1;
            }
        }
    }

    return (-1);
}

// One boon of the category on each slot. Boons stack on a slot: the one on top researches, then the next shows.
void crucibleShopOffer(int category = 0) {
    int offered = 0;

    for (slot = 0; < cCrucibleSlots) {
        int rarity = crucibleShopRarity(category);

        if (rarity >= 0) {
            int boon = crucibleShopBoon(category, rarity);
            int tech = xsArrayGetInt(crucibleBoonTech, boon);

            xsEffectAmount(cModifyTech, tech, cAttrSetLocation, cCrucibleWonder, 1);
            xsEffectAmount(cModifyTech, tech, cAttrSetButton, slot + 1, 1);
            xsArraySetInt(crucibleBoonTaken, boon, 1);
            offered = offered + 1;
        }
    }

    xsChatData("Shop: %d boons offered", offered);
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
