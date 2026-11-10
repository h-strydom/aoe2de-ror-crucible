"""Test: research speed, the one compiled stat that failed (multiplying resource 86). Researched for free at the start;
the rest are confirmed."""

from crucible.bonuses import catalogue

NAME = "compiled"
BOONS = ("palmyrans_9",)  # +30% research speed: the research time resource set, as Palmyrans do
BUTTONS: dict[str, int] = {}
UNITS = ("villager", "storage_pit")


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
        f"RESEARCH SPEED, researched for free at the start: {boons}. Toolworking at the Storage Pit takes 40 s "
        "normally: it should take about 31 s (time it, or compare the progress bar with a 40 s count)."
    )
