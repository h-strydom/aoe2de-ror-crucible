"""The pregame briefing of each Crucible map (2026-11-26, the user's text): how it works, and where to give feedback.

Shown twice: as the campaign's intro slides before each map (`intro`: the campaign's <name>.json, which only loads
from an enabled mod's campaign folder), and as each scenario's instructions (the objectives in game). The scenario's
instructions alone showed nothing before the map (playtest 2026-11-26). Links aren't clickable in game, so the address
is spelled out. A line break in the text is one on screen: each paragraph is one line here, joined.
"""

FEEDBACK = "github.com/h-strydom/aoe2de-ror-crucible"
BACKGROUND = "textures/campaign/pcam3/trajan_background.dds"  # RoR's own (Trajan's campaign)
TEXT_RECT = {"x": 1100, "y": 560, "width": 1750, "height": 1050}  # of 3840 x 2160: on the background's scroll
# (measured off playtest screenshots, 2026-11-26: at x 230 it ran over the scroll's left edge, 2000 wide onto its roll)
TEXT_FADE = 1.5  # seconds the text takes to appear: it fades in over this (over the whole slide, it read as broken)
SLIDE_SECONDS = 600.0  # slides move on by themselves after this: long enough to sit and read (Next moves on)

START = (
    "You must play these missions through the custom campaign, with the Crucible data mod enabled. Mission will "
    "automatically end if launched incorrectly to prevent save state corruption.",
    "",
    # playtest 2026-11-26: Restart and Next level drop the data mod, and the map's check defeats you at once
    "Restart and Next level do not keep the data mod, always run maps directly from the custom campaign screen.",
)
FEEDBACK_SLIDE = f"Feedback, bugs and ideas are always welcome. You can open an issue at:\n{FEEDBACK}"

HUB_SLIDES = (
    "\n".join(
        (
            "Crucible: the Camp",
            "Crucible is a roguelite. In each run defend your Wonder against the Legion's endless waves.",
            "",
            "Defeating waves earns you resources to spend here in the camp.",
            "Upgrades unlocked here are carried into subsequent runs.",
            "",
            *START,
        )
    ),
    "\n".join(
        (
            "How the camp works:",
            "- Use wood, food, gold and stone earned during runs to buy upgrades. Higher difficulties reward more "
            "resources per wave.",
            "- A building marked with (*) has upgrades on offer.",
            "- A building marked with (!) has upgrades on offer that you can afford.",
            "- More researched upgrades unlock higher tiers.",
            "",
            "When done use the available decision to save and exit, or refund your resources.",
        )
    ),
    FEEDBACK_SLIDE,
)

RUN_SLIDES = (
    "\n".join(
        (
            "Crucible: the Run",
            "Keep your Wonder standing.",
            "",
            "The Legion's attack waves gather at the City States and march towards you.",
            "They are endless and grow stronger with each wave.",
            "",
            *START,
        )
    ),
    "\n".join(
        (
            "How a run works:",
            "- You start with your Wonder, Town Center and any upgrades you've researched in the hub.",
            "- A wave marches every 5 minutes.",
            "- You can send waves early by using the button at the Wonder.",
            "- Defeating waves earns you resources to spend in the Hub.",
            "- Surrounding Legion bases will harass you.",
            "- The run ends when your Wonder falls, or when you claim Victory.",
        )
    ),
    FEEDBACK_SLIDE,
)

HUB = "\n\n".join(HUB_SLIDES)  # the scenarios' instructions
RUN = "\n\n".join(RUN_SLIDES)


def _slide(text: str) -> dict:
    return {
        "Duration": SLIDE_SECONDS,
        "TextFadeDuration": TEXT_FADE,
        "FadeInTime": 0.2,
        "FadeOutTime": 0.2,
        "String": text,  # literal text works as well as a string id (ror-reimagined, verified 2026-11)
        "TextRect": dict(TEXT_RECT),
    }


def intro() -> dict:
    """The campaign's intro file: per map, in the campaign's order (the hub, then the run), its slideshow."""
    scenarios = []

    for slides in (HUB_SLIDES, RUN_SLIDES):
        show = {"SlideBackgroundImage": BACKGROUND, "Slides": [_slide(text) for text in slides]}
        scenarios.append({"IntroSequence": {"SequenceItems": [{"Type": "SlideShow", "Data": show}]}})

    return {"Scenarios": scenarios}
