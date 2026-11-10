"""Test: the newly compiled stats work in game. Boons researched for free at the start, chosen where the compile is a
guess (not copied from one of RoR's own bonuses) or where the result is easy to see."""

from crucible.bonuses import catalogue

NAME = "compiled"
BOONS = (
    "shang_1",  # Villagers -10 food cost: food cost attribute (guess)
    "shang_5",  # Town Centers +4 population room: first resource storage (guess)
    "hittites_6",  # Towers +4 population room (guess)
    "palmyrans_2",  # Villagers +1 melee armour: class armour
    "palmyrans_3",  # Villagers +1 pierce armour
    "hittites_1",  # Archers +1 attack: class attack
    "egyptians_5",  # Priests +3 range, and line of sight
    "macedonians_5",  # Houses +50 HP: buildings in every age
    "sumerians_3",  # Farms +125 food
    "choson_6",  # Storage Pit technologies -40% cost: tech costs
    "palmyrans_9",  # +30% research speed (guess)
)
BUTTONS: dict[str, int] = {}
UNITS = ("villager", "villager", "bowman", "priest", "sentry_tower", "house", "storage_pit")


def setup(s, ctx, techs: dict[str, int], top: int) -> str:
    from crucible.scenarios.check import add_unit

    for k, unit in enumerate(UNITS):
        add_unit(s, unit, 6 + 4 * k, top + 6)

    research = "\n".join(f"    xsResearchTechnology({techs[boon]}, true, false, 1);" for boon in BOONS)
    ctx.xs(f"""// ---- crucible check: compiled ----
void crucibleCompiled() {{
{research}
    xsChatData("Compiled boons researched");
}}

rule crucibleCompiledStart
    active
    minInterval 1
{{
    crucibleCompiled();
    xsDisableSelf();
}}
""")
    boons = "; ".join(catalogue.by_id(boon).description for boon in BOONS)

    return (
        f"COMPILED STATS, researched for free at the start: {boons}. Look at the villagers (cost at the Town "
        "Center, armour), the population cap (Town Center and the tower each +4), the bowman's attack, the priest's "
        "range, the house's HP (and after Tool Age), a new farm's food, Storage Pit tech costs and research times."
    )
