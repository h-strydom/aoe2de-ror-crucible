"""Command line entry point: `uv run crucible <command>`."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crucible",
        description="Build the Crucible campaign for AoE2 DE Return of Rome.",
    )
    sub = parser.add_subparsers(dest="command")
    check = sub.add_parser(
        "check",
        help="build the data mod and crucible_check, the scenario for checking things in game",
    )
    check.add_argument(
        "--test",
        action="append",
        help="a test to include (repeatable; all registered tests if none): see scenarios/checks/",
    )
    check.add_argument("--install", action="store_true", help="install the data mod and the scenario")
    maps = sub.add_parser("map", help="the hand-made maps kept in assets/: the arena and meta (the hub)")
    maps.add_argument(
        "action",
        choices=("save", "install"),
        help="save: copy the game's copy into the repo after editing; install: put the repo's copy in the game",
    )
    maps.add_argument("name", choices=("arena", "meta"))
    campaign = sub.add_parser(
        "campaign",
        help="build the data mod, crucible_hub, crucible_run and the Crucible campaign that plays them in turn",
    )
    campaign.add_argument("--install", action="store_true", help="install the data mod, the scenarios and the campaign")
    package = sub.add_parser("package", help="the data mod as a zip for the official mod site, with its page files")
    package.add_argument("--to", type=Path, default=OUT / "package", help="where to put them (default: out/package)")
    args = parser.parse_args(argv)

    if args.command == "check":
        from aoe2ed import game

        from crucible.datamod import build
        from crucible.scenarios import check as check_scenario
        from crucible.scenarios.checks import TESTS

        tests = args.test or list(TESTS)
        unknown = [name for name in tests if name not in TESTS]

        if unknown:
            parser.error(f"unknown tests {unknown}; registered: {sorted(TESTS)}")

        folder = build.build(check_scenario.boons(tests), OUT, buttons=check_scenario.buttons(tests))
        techs = build.manifest(folder)
        scenario = check_scenario.build(OUT, techs, tests)
        print(f"tests: {', '.join(tests)}")
        print(folder, scenario, sep="\n")

        if args.install:
            print(f"installed: {build.install(folder)}")
            print(f"installed: {game.install(scenario, game='ror')['installed']}")

        return 0

    if args.command == "map":
        from crucible.scenarios import maps as hand_made

        if args.action == "save":
            print(f"saved: {hand_made.save(args.name)}")
        else:
            print(f"installed: {hand_made.install(args.name)}")

        return 0

    if args.command == "campaign":
        from aoe2ed import game

        from crucible.bonuses import catalogue
        from crucible.datamod import build
        from crucible.scenarios import campaign as crucible_campaign
        from crucible.scenarios import hub, run

        folder = build.build(list(catalogue.ALL), OUT)
        techs = build.manifest(folder)
        scenarios = [hub.build(OUT, techs), run.build(OUT, techs)]
        built = crucible_campaign.build(OUT, *scenarios)
        print(folder, *scenarios, built, sep="\n")

        if args.install:
            print(f"installed: {build.install(folder)}")

            for path in (*scenarios, built):
                print(f"installed: {game.install(path, game='ror')['installed']}")

        return 0

    if args.command == "package":
        from crucible import package as mod_package
        from crucible.bonuses import catalogue
        from crucible.datamod import build

        for kind, path in mod_package.package(build.build(list(catalogue.ALL), OUT), args.to).items():
            print(f"{kind}: {path}")

        return 0

    parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
