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
    p_res = sub.add_parser("resource-test", help="build the resource test scenario (extreme gather values, a "
                                                 "mismatched gather swap, trickles, generation)")
    p_res.add_argument("--install", action="store_true", help="also rebuild and install the data mod, and copy the "
                                                              "scenario into your Return of Rome scenario folder")
    sub.add_parser("resource-report", help="print what the resource test recorded")
    p_combat = sub.add_parser("combat-test", help="build the combat test scenario (friendly fire, splash, "
                                                  "projectiles, minimum and maximum range, trade shares)")
    p_combat.add_argument("--install", action="store_true", help="copy it into your Return of Rome scenario folder")
    sub.add_parser("combat-report", help="print what the combat test recorded")
    p_fire = sub.add_parser("fire-test", help="build the friendly fire test scenario")
    p_fire.add_argument("--install", action="store_true", help="copy it into your Return of Rome scenario folder")
    sub.add_parser("fire-report", help="print what the friendly fire test recorded")
    p_cat = sub.add_parser("catapult-tower", help="build the catapult tower demo: every tower fires a Stone "
                                                  "Thrower's stone")
    p_cat.add_argument("--install", action="store_true", help="copy it into your Return of Rome scenario folder")
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
    if args.command == "resource-test":
        from . import resourcetest, testmod
        path, _, _ = resourcetest.build_mission(ROOT / "out")
        print(path)
        if args.install:
            from aoe2ed import game
            res = testmod.build(ROOT / "out")
            print(f"  installed data mod: {testmod.install(res)['data_mod']}")
            print(f"  installed: {game.install(path, game='ror')['installed']}")
        return 0
    if args.command == "resource-report":
        from aoe2ed import game

        from . import resourcetest
        record = Path(game.read_xsdat(resourcetest.CAMPAIGN)["path"])
        print(resourcetest.report(record))
        return 0
    if args.command == "combat-test":
        from . import combattest
        path, _ = combattest.build(ROOT / "out")
        print(path)
        if args.install:
            from aoe2ed import game
            print(f"  installed: {game.install(path, game='ror')['installed']}")
        return 0
    if args.command == "combat-report":
        from aoe2ed import game

        from . import combattest
        record = Path(game.read_xsdat(combattest.NAME)["path"])
        print(combattest.report(record, combattest.labels()))
        return 0
    if args.command == "fire-test":
        from . import firetest
        path, _ = firetest.build(ROOT / "out")
        print(path)
        if args.install:
            from aoe2ed import game
            print(f"  installed: {game.install(path, game='ror')['installed']}")
        return 0
    if args.command == "fire-report":
        from aoe2ed import game

        from . import firetest
        record = Path(game.read_xsdat(firetest.NAME)["path"])
        print(firetest.report(record, firetest.labels()))
        return 0
    if args.command == "catapult-tower":
        from . import catapulttower
        path = catapulttower.build(ROOT / "out")
        print(path)
        if args.install:
            from aoe2ed import game
            print(f"  installed: {game.install(path, game='ror')['installed']}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
