from crucible.scenarios import briefing, campaign


def test_each_briefing_explains_its_map_and_links_the_repo():
    for text, title in ((briefing.HUB, "the Camp"), (briefing.RUN, "the Run")):
        assert text.startswith(f"Crucible: {title}")
        assert briefing.START[-1] in text
        assert text.endswith(briefing.FEEDBACK)
        assert "  " not in text


def test_the_campaign_intro_shows_each_maps_briefing_as_slides(tmp_path):
    built = tmp_path / "Crucible.aoe2campaign"
    built.write_bytes(b"campaign")
    folder = campaign.mod(tmp_path / "out", built)
    assert (folder / "info.json").is_file()
    assert {p.name for p in (folder / campaign.FOLDER).iterdir()} == {"Crucible.aoe2campaign", "Crucible.json"}
    scenarios = briefing.intro()["Scenarios"]
    assert len(scenarios) == 2  # the hub, then the run

    for scenario, slides in zip(scenarios, (briefing.HUB_SLIDES, briefing.RUN_SLIDES), strict=True):
        shown = scenario["IntroSequence"]["SequenceItems"][0]["Data"]["Slides"]
        assert [s["String"] for s in shown] == list(slides)
        assert all(s["Duration"] == briefing.SLIDE_SECONDS for s in shown)
        assert shown[-1]["String"].endswith(briefing.FEEDBACK)
