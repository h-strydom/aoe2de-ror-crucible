from crucible.scenarios import briefing


def test_each_briefing_explains_its_map_and_links_the_repo():
    for text, title in ((briefing.HUB, "the Camp"), (briefing.RUN, "the Run")):
        assert text.startswith(f"<b>Crucible: {title}<b>")
        assert briefing.START[0] in text
        assert text.endswith(briefing.FEEDBACK)
        assert "  " not in text and not text.count("<b>") % 2
