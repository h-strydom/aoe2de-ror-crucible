// ---- Crucible shop: runtime (the generated data block comes first) ----
// crucibleShopOpen() after a wave (or a base) grants cCrucibleChoices choices. Each choice: two categories on the choice
// buttons, from different tag axes (a combat boon, a Stable boon), drawn by weight: a category picked before weighs
// more (cCrucibleCategoryBoost a pick), so the shop leans towards what the player goes for. A click locks in (the other
// is disabled); when the pick finishes, each boon slot gets a random boon of that category at its next level, at its
// rarity's price less the Wonder's boon discount. Each level is its own tech and they stack: a boon comes back at its
// next level once the last is bought (playtest 2026-11-23). A boon goes on the button of rows 1-2
// (cCrucibleButtons) with the fewest unbought boons: they only stack once every button holds one, so a boon the player
// can't use yet doesn't block the next. crucibleShopOpenPoor() (wave 0) skips the choice: each slot gets the first
// level of a random common boon, free.
// Rerolls (the Trade Workshop's): while a choice is up, the Wonder's reroll shows two other categories; the
// upgrade's level is the free rerolls a run, then a reroll costs gold (the paid tech). Triggers show a reroll
// (cCrucibleRerollSignal: 1 the free one, 2 the paid one); XS hides them. Spies starts hidden (a trigger
// shows it for the upgrade). A reroll weighs the categories it turns down less from then on, and each Legion base
// destroyed gives a free reroll more (with the upgrade). A category with fewer boons left than the offer's slots
// weighs that much less, so the shop spreads out again once a favourite runs dry (playtest 2026-11-24).
// With one boon left nothing was offered (playtest 2026-11-24): rolls are kept below their count whatever
// xsGetRandomNumberLH's top end does, a pick that offers nothing gives its choice back, and choices with no boons
// left wait (crucibleShopRetry) for a bought boon's next level instead of being dropped.

int crucibleShopState = 0;  // 0 closed, 1 choosing, 2 picked
int crucibleShopCategory1 = -1;
int crucibleShopCategory2 = -1;
int crucibleShopPicked = 0;  // the choice clicked: 1 or 2
int crucibleShopChoices = 0;  // choices still to make
bool crucibleShopReady = false;
bool crucibleShopPoor = false;  // the free offer (wave 0) is being made
int crucibleShopRetry = 0;  // seconds: choices waiting for boons look again then
bool crucibleShopEmptySaid = false;  // "no boons left" said, until a choice shows again

const int cCrucibleShopPendingSize = 400;
int crucibleShopPendingTech = -1;  // boons on the Wonder not yet bought: their tech, button and boon
int crucibleShopPendingButton = -1;
int crucibleShopPendingBoon = -1;
int crucibleShopPendingCount = 0;
int crucibleShopButtonLoad = -1;  // by button (1 to cCrucibleButtons): unbought boons on it
int crucibleShopRerollShown = 0;  // 0 none, 1 the free reroll, 2 the paid one; -1 to be shown again
int crucibleShopRerollsUsed = 0;  // free rerolls used this run
bool crucibleShopRerollHandled = false;  // a reroll's research seen done, until it's shown again
int crucibleShopSkip1 = -1;  // categories a reroll leaves out
int crucibleShopSkip2 = -1;
int crucibleShopRerollBonus = 0;  // free rerolls more this run: a Legion base destroyed each

void crucibleShopInit() {
    if (crucibleShopReady) {
        return;
    }

    crucibleShopData();
    crucibleShopPendingTech = xsArrayCreateInt(cCrucibleShopPendingSize, -1, "crucibleShopPendingTech");
    crucibleShopPendingButton = xsArrayCreateInt(cCrucibleShopPendingSize, 0, "crucibleShopPendingButton");
    crucibleShopPendingBoon = xsArrayCreateInt(cCrucibleShopPendingSize, -1, "crucibleShopPendingBoon");
    crucibleShopButtonLoad = xsArrayCreateInt(cCrucibleButtons + 1, 0, "crucibleShopButtonLoad");
    xsEffectAmount(cDisableTech, cCrucibleChoice1, cAttributeDisable, 0, 1);
    xsEffectAmount(cDisableTech, cCrucibleChoice2, cAttributeDisable, 0, 1);

    if (cCrucibleRerollFree >= 0) {
        xsEffectAmount(cDisableTech, cCrucibleRerollFree, cAttributeDisable, 0, 1);
        xsEffectAmount(cDisableTech, cCrucibleRerollPaid, cAttributeDisable, 0, 1);
    }

    if (cCrucibleSpies >= 0) {
        xsEffectAmount(cDisableTech, cCrucibleSpies, cAttributeDisable, 0, 1);
    }

    crucibleShopReady = true;
}

// 0 to n - 1.
int crucibleShopRandom(int n = 1) {
    int r = xsGetRandomNumberLH(0, n);

    if (r >= n) {
        return (n - 1);
    }

    return (r);
}

int crucibleShopChoice(int number = 1) {
    if (number == 1) {
        return (cCrucibleChoice1);
    }

    return (cCrucibleChoice2);
}

// The tech of the boon's next level; -1 once it has none left.
int crucibleShopNextTech(int boon = 0) {
    int level = xsArrayGetInt(crucibleBoonNext, boon);

    if (level >= cCrucibleLevels) {
        return (-1);
    }

    return (xsArrayGetInt(crucibleBoonLevel, boon * cCrucibleLevels + level));
}

// A boon that can be offered now: not on the Wonder already, a next level left, and in the free offer a common
// boon not bought yet.
bool crucibleShopOfferable(int boon = 0) {
    if (xsArrayGetInt(crucibleBoonPending, boon) == 1) {
        return (false);
    }

    if (crucibleShopNextTech(boon) < 0) {
        return (false);
    }

    if (crucibleShopPoor == false) {
        return (true);
    }

    return ((xsArrayGetInt(crucibleBoonNext, boon) == 0) && (xsArrayGetInt(crucibleBoonRarity, boon) == 0));
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

bool crucibleShopEligible(int category = 0, int skipAxis = -1) {
    if ((category == crucibleShopSkip1) || (category == crucibleShopSkip2)) {
        return (false);
    }

    return ((xsArrayGetInt(crucibleCategoryAxis, category) != skipAxis) && (crucibleShopAvailable(category) > 0));
}

int crucibleShopMeta(int variable = -1) {
    if (variable < 0) {
        return (0);
    }

    return (xsTriggerVariable(variable));
}

int crucibleShopSlots() {
    int slots = cCrucibleSlots + crucibleShopMeta(cCrucibleSlotsVariable);

    if (slots > cCrucibleMaxSlots) {
        return (cCrucibleMaxSlots);
    }

    return (slots);
}

// Its weight, less in proportion while it has fewer boons left than the offer's slots (at least 1).
int crucibleShopWeight(int category = 0) {
    int weight = xsArrayGetInt(crucibleCategoryWeight, category);
    int available = crucibleShopAvailable(category);
    int slots = crucibleShopSlots();

    if (available < slots) {
        weight = weight * available / slots;
    }

    if (weight < 1) {
        return (1);
    }

    return (weight);
}

// A category with boons left, not of axis `skipAxis`, drawn by weight; -1 if none.
int crucibleShopRandomCategory(int skipAxis = -1) {
    int total = 0;

    for (a = 0; < cCrucibleCategories) {
        if (crucibleShopEligible(a, skipAxis)) {
            total = total + crucibleShopWeight(a);
        }
    }

    if (total <= 0) {
        return (-1);
    }

    int roll = crucibleShopRandom(total);

    for (b = 0; < cCrucibleCategories) {
        if (crucibleShopEligible(b, skipAxis)) {
            roll = roll - crucibleShopWeight(b);

            if (roll < 0) {
                return (b);
            }
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
        if (crucibleShopEmptySaid == false) {
            xsChatData("Shop: no boons left to offer: your choices wait for the next");
            crucibleShopEmptySaid = true;
        }

        return;
    }

    crucibleShopEmptySaid = false;

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

    int roll = crucibleShopRandom(count);

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

// The rarity's price less the Wonder's boon discount (percent off by its level); free in the free offer.
void crucibleShopPrice(int tech = -1, int rarity = 0) {
    int level = crucibleShopMeta(cCrucibleDiscountVariable);

    if (level >= xsArrayGetSize(crucibleShopDiscount)) {
        level = xsArrayGetSize(crucibleShopDiscount) - 1;
    }

    int keep = 100 - xsArrayGetInt(crucibleShopDiscount, level);

    if (crucibleShopPoor) {
        keep = 0;
    }

    xsEffectAmount(cModifyTech, tech, cAttrSetFoodCost, xsArrayGetInt(crucibleRarityCost, rarity * 4) * keep / 100, 1);
    xsEffectAmount(cModifyTech, tech, cAttrSetWoodCost, xsArrayGetInt(crucibleRarityCost, rarity * 4 + 1) * keep / 100, 1);
    xsEffectAmount(cModifyTech, tech, cAttrSetStoneCost, xsArrayGetInt(crucibleRarityCost, rarity * 4 + 2) * keep / 100, 1);
    xsEffectAmount(cModifyTech, tech, cAttrSetGoldCost, xsArrayGetInt(crucibleRarityCost, rarity * 4 + 3) * keep / 100, 1);
}

// The button for the next boon: the one with the fewest unbought boons (a free one first), the lowest of those.
int crucibleShopFreeButton() {
    int best = 1;

    for (b = 2; <= cCrucibleButtons) {
        if (xsArrayGetInt(crucibleShopButtonLoad, b) < xsArrayGetInt(crucibleShopButtonLoad, best)) {
            best = b;
        }
    }

    return (best);
}

// Bought boons free their buttons, and their boon moves on to its next level.
void crucibleShopFreeBought() {
    int i = 0;
    int button = 0;
    int boon = 0;
    int last = 0;

    while (i < crucibleShopPendingCount) {
        if (xsGetTechState(xsArrayGetInt(crucibleShopPendingTech, i), 1) == cTechStateDone) {
            button = xsArrayGetInt(crucibleShopPendingButton, i);
            boon = xsArrayGetInt(crucibleShopPendingBoon, i);
            last = crucibleShopPendingCount - 1;
            xsArraySetInt(crucibleShopButtonLoad, button, xsArrayGetInt(crucibleShopButtonLoad, button) - 1);
            xsArraySetInt(crucibleBoonNext, boon, xsArrayGetInt(crucibleBoonNext, boon) + 1);
            xsArraySetInt(crucibleBoonPending, boon, 0);
            xsArraySetInt(crucibleShopPendingTech, i, xsArrayGetInt(crucibleShopPendingTech, last));
            xsArraySetInt(crucibleShopPendingButton, i, xsArrayGetInt(crucibleShopPendingButton, last));
            xsArraySetInt(crucibleShopPendingBoon, i, xsArrayGetInt(crucibleShopPendingBoon, last));
            crucibleShopPendingCount = last;
        } else {
            i++;
        }
    }
}

// One boon of the category per slot, each at its next level on the freest button. Stacked boons: the one on top
// researches, then the next shows. How many were offered.
int crucibleShopOffer(int category = 0) {
    int offered = 0;
    int slots = crucibleShopSlots();
    int speed = crucibleShopMeta(cCrucibleSpeedVariable);
    int time = cCrucibleBoonTime * (cCrucibleSpeedTiers - speed) / cCrucibleSpeedTiers;
    int boon = -1;  // declared outside the loop: XS runs a declaration in a loop only once
    int tech = -1;
    int button = 0;

    if (time < 1) {
        time = 1;  // the fastest is 1 s: at 0 the game researches a tech by itself
    }

    for (slot = 0; < slots) {
        boon = crucibleShopBoon(category);

        if (boon >= 0) {
            tech = crucibleShopNextTech(boon);
            crucibleShopFreeBought();
            button = crucibleShopFreeButton();

            crucibleShopPrice(tech, xsArrayGetInt(crucibleBoonRarity, boon));
            xsEffectAmount(cModifyTech, tech, cAttrSetTime, time, 1);
            xsEffectAmount(cModifyTech, tech, cAttrSetLocation, cCrucibleWonder, 1);
            xsEffectAmount(cModifyTech, tech, cAttrSetButton, button, 1);
            xsArraySetInt(crucibleShopButtonLoad, button, xsArrayGetInt(crucibleShopButtonLoad, button) + 1);

            if (crucibleShopPendingCount < cCrucibleShopPendingSize) {
                xsArraySetInt(crucibleShopPendingTech, crucibleShopPendingCount, tech);
                xsArraySetInt(crucibleShopPendingButton, crucibleShopPendingCount, button);
                xsArraySetInt(crucibleShopPendingBoon, crucibleShopPendingCount, boon);
                crucibleShopPendingCount++;
            }

            xsArraySetInt(crucibleBoonPending, boon, 1);
            offered = offered + 1;
        }
    }

    xsChatData("Shop: %d boons offered", offered);

    return (offered);
}

// The reroll the Wonder should show: none without the upgrade or a choice up; the free one while some are left.
int crucibleShopRerollWanted() {
    int level = crucibleShopMeta(cCrucibleRerollsVariable);

    if ((cCrucibleRerollFree < 0) || (level <= 0) || (crucibleShopState != 1)) {
        return (0);
    }

    if (crucibleShopRerollsUsed < level + crucibleShopRerollBonus) {
        return (1);
    }

    return (2);
}

void crucibleShopRerollShow(int wanted = 0) {
    if (wanted == crucibleShopRerollShown) {
        return;
    }

    if (wanted != 1) {
        xsEffectAmount(cDisableTech, cCrucibleRerollFree, cAttributeDisable, 0, 1);
    }

    if (wanted != 2) {
        xsEffectAmount(cDisableTech, cCrucibleRerollPaid, cAttributeDisable, 0, 1);
    }

    if (wanted > 0) {
        xsSetTriggerVariable(cCrucibleRerollSignal, wanted);
    }

    crucibleShopRerollShown = wanted;
}

// A category a reroll turned down weighs less.
void crucibleShopDisfavour(int category = -1) {
    int weight = 0;

    if (category < 0) {
        return;
    }

    weight = xsArrayGetInt(crucibleCategoryWeight, category) - cCrucibleCategoryRerollPenalty;

    if (weight < cCrucibleCategoryMin) {
        weight = cCrucibleCategoryMin;
    }

    xsArraySetInt(crucibleCategoryWeight, category, weight);
}

// A Legion base destroyed: a free reroll more, with the upgrade.
void crucibleShopRerollGift() {
    if ((cCrucibleRerollFree < 0) || (crucibleShopMeta(cCrucibleRerollsVariable) <= 0)) {
        return;
    }

    crucibleShopRerollBonus++;
    xsChatData("Shop: a free reroll more");
}

// Two other categories than those on offer (the same ones if there are no others); those weigh less from now on.
void crucibleShopRedraw() {
    crucibleShopDisfavour(crucibleShopCategory1);
    crucibleShopDisfavour(crucibleShopCategory2);
    crucibleShopSkip1 = crucibleShopCategory1;
    crucibleShopSkip2 = crucibleShopCategory2;

    if (crucibleShopRandomCategory(-1) < 0) {
        crucibleShopSkip1 = -1;
        crucibleShopSkip2 = -1;
    }

    crucibleShopShow();
    crucibleShopSkip1 = -1;
    crucibleShopSkip2 = -1;
}

// A reroll researched: redraw if the choice is still up, else give back what it cost; then show the right one.
void crucibleShopReroll() {
    if (cCrucibleRerollFree < 0) {
        return;
    }

    int free = xsGetTechState(cCrucibleRerollFree, 1);
    int paid = xsGetTechState(cCrucibleRerollPaid, 1);

    if ((free == cTechStateResearching) || (free == cTechStateQueued)) {
        return;
    }

    if ((paid == cTechStateResearching) || (paid == cTechStateQueued)) {
        return;
    }

    if ((free == cTechStateDone) || (paid == cTechStateDone)) {
        if (crucibleShopRerollHandled == false) {
            crucibleShopRerollHandled = true;
            crucibleShopRerollShown = -1;  // a researched tech comes back by trigger

            if (crucibleShopState == 1) {
                if (free == cTechStateDone) {
                    crucibleShopRerollsUsed++;
                }

                crucibleShopRedraw();
            } else if (paid == cTechStateDone) {
                xsSetPlayerAttribute(1, cAttributeGold, xsPlayerAttribute(1, cAttributeGold) + cCrucibleRerollGold);
            }
        }
    } else {
        crucibleShopRerollHandled = false;
    }

    crucibleShopRerollShow(crucibleShopRerollWanted());
}

// Wave 0 is defeated: no choice, the first level of a common boon, free, on each slot.
void crucibleShopOpenPoor() {
    crucibleShopInit();
    crucibleShopPoor = true;
    crucibleShopOffer(-1);
    crucibleShopPoor = false;
}

// The player picked `category`: the shop offers it more often from now on.
void crucibleShopFavour(int category = -1) {
    if (category >= 0) {
        xsArraySetInt(crucibleCategoryWeight, category, xsArrayGetInt(crucibleCategoryWeight, category) + cCrucibleCategoryBoost);
    }
}

rule crucibleShop
    active
    highFrequency
{
    crucibleShopInit();
    crucibleShopFreeBought();
    crucibleShopReroll();

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
        int offered = 0;

        if (crucibleShopPicked == 1) {
            crucibleShopFavour(crucibleShopCategory1);
            offered = crucibleShopOffer(crucibleShopCategory1);
        } else {
            crucibleShopFavour(crucibleShopCategory2);
            offered = crucibleShopOffer(crucibleShopCategory2);
        }

        crucibleShopPicked = 0;
        crucibleShopState = 0;

        if (offered > 0) {
            crucibleShopChoices = crucibleShopChoices - 1;  // else the choice comes back
        }

        if (crucibleShopChoices > 0) {
            crucibleShopShow();
        }

        return;
    }

    if ((crucibleShopState == 0) && (crucibleShopChoices > 0) && (xsGetTime() >= crucibleShopRetry)) {
        crucibleShopRetry = xsGetTime() + 5;
        crucibleShopShow();
    }
}
