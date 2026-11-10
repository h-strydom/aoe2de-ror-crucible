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

    parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
