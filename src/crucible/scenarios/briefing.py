"""The pregame briefing of each Crucible map (the scenario's instructions, 2026-11-26): how it works, and where to give
feedback. The game shows it before the map starts and in the objectives during it; links aren't clickable there, so
the address is spelled out. A line break in the text is one on screen: each paragraph is one line here, joined.
"""

FEEDBACK = "github.com/h-strydom/aoe2de-ror-crucible"
START = (  # playtest 2026-11-26: Restart and Next level drop the data mod, and the map's check defeats you at once
    "<b>Always start a map from the campaign screen, with Crucible chosen as the data mod.<b> Restart and Next level "
    "don't keep the data mod, and the map ends in defeat at once.",
    "",
)
FOOTER = ("Feedback, bugs and ideas are very welcome: open an issue at", FEEDBACK)

HUB = "\n".join(
    (
        "<b>Crucible: the Camp<b>",
        "Crucible is a roguelite. In each run you hold your Wonder against the Legion's waves, which never end. What a "
        "run earns comes back here, to buy upgrades that make the next run stronger.",
        "",
        "<b>How the camp works<b>",
        "- Your food, wood, gold and stone here are what your runs earned. Each wave you defeat pays 1 to 3 (by "
        "difficulty) of its age's resource: food in the Stone Age, wood in the Tool Age, gold in the Bronze Age, stone "
        "after.",
        "- A building marked (*) has upgrades on offer, (!) one you can afford. Research an upgrade to buy it.",
        "- Buying upgrades opens the next tier: more buildings, units and techs to start the run with, and later the "
        "ages.",
        "- The Wonder sells upgrades for every run: more and faster boons, rerolls, spies and more.",
        "- When you're ready, answer the question: save and start the run, or reset everything (what you spent comes "
        "back).",
        "",
        "Play it from the Crucible campaign: only the campaign keeps your upgrades between runs.",
        "",
        *START,
        *FOOTER,
    )
)

RUN = "\n".join(
    (
        "<b>Crucible: the Run<b>",
        "Keep your Wonder standing. The Legion's waves gather at the City States and march down the roads to your "
        "base. They never end, and grow stronger as the Legion ages up.",
        "",
        "<b>How a run works<b>",
        "- You start with your Town Center, your Wonder and what your camp upgrades bring.",
        "- A wave marches 5 minutes after the last one, or as soon as you click Send next wave on the Wonder.",
        "- Each wave you defeat pays currency for the camp (kept at once, even if the run is lost) and a boon choice "
        "on the Wonder.",
        "- The Legion's bases around the map raid you while they stand. Destroy one for a boon choice and a free "
        "reroll.",
        "- The Legion's outposts guard the resources around them.",
        "- The run ends when your Wonder falls, or when you claim victory (any time). Then it's back to the camp.",
        "",
        *START,
        *FOOTER,
    )
)
