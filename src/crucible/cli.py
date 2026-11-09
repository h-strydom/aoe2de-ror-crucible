"""Command line entry point: `uv run crucible <command>`."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crucible", description=__doc__)
    sub = parser.add_subparsers(dest="command")
    p_test = sub.add_parser("test-map", help="build the engine test scenario (no-build terrain, safe zone, resource "
                                             "amounts, formations)")
    p_test.add_argument("--install", action="store_true", help="copy it into your Return of Rome scenario folder")
    p_mod = sub.add_parser("test-mod", help="build the data mod test: a data mod, a dropsites-only mod and a "
                                            "two-mission test campaign")
    p_mod.add_argument("--install", action="store_true", help="copy the mods into your profile's local mods and the "
                                                              "campaign into Return of Rome's campaign folder")
    args = parser.parse_args(argv)

    if args.command == "test-map":
        from . import testmap
        path = testmap.build(ROOT / "out")
        print(path)
        if args.install:
            from aoe2ed import game
            print(f"  installed: {game.install(path, game='ror')['installed']}")
        return 0
    if args.command == "test-mod":
        from . import testmod
        res = testmod.build(ROOT / "out")
        for key, path in res.items():
            print(f"{key}: {path}")
        if args.install:
            for key, path in testmod.install(res).items():
                print(f"  installed {key}: {path}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
