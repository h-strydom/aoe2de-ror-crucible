"""What a bonus is: one modifier, decomposed by hand from a civ's bonus text.

A civ's text ("Academy units and elephant units +25% hit points, Camel Riders +15% hit points") becomes one
modifier per group of targets that share a change, so each can be handed out, retuned or widened on its own.
"""

from dataclasses import dataclass
from enum import StrEnum


class Stat(StrEnum):
    HP = "hp"
    ATTACK = "attack"
    SPEED = "speed"
    WORK_RATE = "work rate"
    START_RESOURCES = "start resources"
    TECH_COST = "tech cost"


class Mode(StrEnum):
    PERCENT = "x"  # +0.25x: 25% more
    FLAT = "+"  # +50: fifty more


@dataclass(frozen=True)
class Change:
    amount: float
    mode: Mode

    def __str__(self) -> str:
        return f"{self.amount:+g}{'x' if self.mode is Mode.PERCENT else ''}"


def pct(amount: float) -> Change:
    """A relative change: pct(0.25) is +25%, pct(-1) makes something free."""
    return Change(amount, Mode.PERCENT)


def flat(amount: float) -> Change:
    """An absolute change: flat(50) is +50."""
    return Change(amount, Mode.FLAT)


@dataclass(frozen=True)
class Modifier:
    """One bonus that can be handed out on its own (to the player, the enemy, as metaprogression or a boon).

    `targets` are RoR object names (units, buildings or techs), empty for player-wide changes. `tags` group
    modifiers for the hand-outs ("pick a stable upgrade"); anything goes, kept lowercase. `name` is the shop label.
    """

    change: Change
    stat: Stat
    targets: tuple[str, ...]
    tags: tuple[str, ...]
    civ: str
    name: str
    kind: str = "civ"  # "civ" or "team"

    @property
    def id(self) -> str:
        """Stable key: civ and name, e.g. "carthaginians.academy_hp"."""
        return f"{self.civ}.{self.name.lower().replace(' ', '_')}"

    def __str__(self) -> str:
        on = ", ".join(self.targets) or "player"
        return f"{self.change} {self.stat} [{on}] [{', '.join(self.tags)}] {self.civ} ({self.kind})"
