"""The pregame briefing of each Crucible map (2026-11-26): how it works, and where to give feedback.

Shown twice: as the campaign's intro slides before each map (`intro`: the campaign's <name>.json, which only loads
from a local mod's campaign folder), and as each scenario's instructions (the objectives in game). The scenario's
instructions alone showed nothing before the map (playtest 2026-11-26). Links aren't clickable in game, so the address
is spelled out. A line break in the text is one on screen: each paragraph is one line here, joined.
"""

FEEDBACK = "github.com/h-strydom/aoe2de-ror-crucible"
BACKGROUND = "textures/campaign/pcam3/trajan_background.dds"  # RoR's own (Trajan's campaign)
TEXT_RECT = {"x": 1100, "y": 560, "width": 2000, "height": 1050}  # of 3840 x 2160: on the background's scroll
# (measured off a playtest screenshot, 2026-11-26: at the left the text ran over the scroll's edge)
TEXT_FADE = 1.5  # seconds the text takes to appear: it fades in over this (over the whole slide, it read as broken)
CHARS_PER_SECOND = 14  # reading pace: how long a slide stays
MIN_SECONDS, MAX_SECONDS = 8.0, 60.0

START = (  # playtest 2026-11-26: Restart and Next level drop the data mod, and the map's check defeats you at once
    "<b>Always start a map from the campaign screen, with Crucible chosen as the data mod.<b> Restart and Next level "
    "don't keep the data mod, and the map ends in defeat at once."
)
FOOTER = f"Feedback, bugs and ideas are very welcome: open an issue at\n{FEEDBACK}"

HUB_SLIDES = (
    "\n".join(
        (
            "<b>Crucible: the Camp<b>",
            "Crucible is a roguelite. In each run you hold your Wonder against the Legion's waves, which never end. "
            "What a run earns comes back here, to buy upgrades that make the next run stronger.",
            "",
            "Play it from the Crucible campaign: only the campaign keeps your upgrades between runs.",
        )
    ),
    "\n".join(
        (
            "<b>How the camp works<b>",
            "- Your food, wood, gold and stone here are what your runs earned. Each wave you defeat pays 1 to 3 (by "
            "difficulty) of its age's resource: food in the Stone Age, wood in the Tool Age, gold in the Bronze Age, "
            "stone after.",
            "- A building marked (*) has upgrades on offer, (!) one you can afford. Research an upgrade to buy it.",
            "- Buying upgrades opens the next tier: more buildings, units and techs to start the run with, and later "
            "the ages.",
            "- The Wonder sells upgrades for every run: more and faster boons, rerolls, spies and more.",
            "- When you're ready, answer the question: save and start the run, or reset everything (what you spent "
            "comes back).",
        )
    ),
    f"{START}\n\n{FOOTER}",
)

RUN_SLIDES = (
    "\n".join(
        (
            "<b>Crucible: the Run<b>",
            "Keep your Wonder standing. The Legion's waves gather at the City States and march down the roads to your "
            "base. They never end, and grow stronger as the Legion ages up.",
        )
    ),
    "\n".join(
        (
            "<b>How a run works<b>",
            "- You start with your Town Center, your Wonder and what your camp upgrades bring.",
            "- A wave marches 5 minutes after the last one, or as soon as you click Send next wave on the Wonder.",
            "- Each wave you defeat pays currency for the camp (kept at once, even if the run is lost) and a boon "
            "choice on the Wonder.",
            "- The Legion's bases around the map raid you while they stand. Destroy one for a boon choice and a free "
            "reroll.",
            "- The Legion's outposts guard the resources around them.",
            "- The run ends when your Wonder falls, or when you claim victory (any time). Then it's back to the camp.",
        )
    ),
    f"{START}\n\n{FOOTER}",
)

HUB = "\n\n".join(HUB_SLIDES)  # the scenarios' instructions
RUN = "\n\n".join(RUN_SLIDES)


def _plain(text: str) -> str:
    return text.replace("<b>", "")  # slides show the tags as typed (unverified): kept plain


def _seconds(text: str) -> float:
    return round(min(max(len(text) / CHARS_PER_SECOND, MIN_SECONDS), MAX_SECONDS), 1)


def _slide(text: str) -> dict:
    duration = _seconds(text)

    return {
        "Duration": duration,
        "TextFadeDuration": TEXT_FADE,
        "FadeInTime": 0.2,
        "FadeOutTime": 0.2,
        "String": _plain(text),  # literal text works as well as a string id (ror-reimagined, verified 2026-11)
        "TextRect": dict(TEXT_RECT),
    }


def intro() -> dict:
    """The campaign's intro file: per map, in the campaign's order (the hub, then the run), its slideshow."""
    scenarios = []

    for slides in (HUB_SLIDES, RUN_SLIDES):
        show = {"SlideBackgroundImage": BACKGROUND, "Slides": [_slide(text) for text in slides]}
        scenarios.append({"IntroSequence": {"SequenceItems": [{"Type": "SlideShow", "Data": show}]}})

    return {"Scenarios": scenarios}
