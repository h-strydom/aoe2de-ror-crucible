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
        "upgrade-check",
        help="build the data mod with one upgrade and a scenario to check it in game",
    )
    check.add_argument("upgrade", help='a modifier id from the catalogue, e.g. "carthaginians_4"')
    check.add_argument("--install", action="store_true", help="install the data mod and the scenario")
    args = parser.parse_args(argv)

    if args.command == "upgrade-check":
        from aoe2ed import game

        from crucible.bonuses import catalogue
        from crucible.datamod import build
        from crucible.scenarios import upgrade_check

        modifier = catalogue.by_id(args.upgrade)
        folder = build.build([modifier], OUT)
        scenario = upgrade_check.build(modifier, OUT)
        print(f"{modifier.name}: {modifier.description} (tech {build.manifest(folder)[modifier.id]})")
        print(folder, scenario, sep="\n")
        if args.install:
            print(f"installed: {build.install(folder)}")
            print(f"installed: {game.install(scenario, game='ror')['installed']}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
