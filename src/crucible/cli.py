"""Command line entry point: `uv run crucible <command>`."""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crucible",
                                     description="Build the Crucible campaign for AoE2 DE Return of Rome.")
    parser.add_subparsers(dest="command")
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
