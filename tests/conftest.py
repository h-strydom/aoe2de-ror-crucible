import pytest

from crucible import meta
from crucible.bonuses import catalogue
from crucible.boons import catalogue as boons
from crucible.datamod import boons as boon_techs
from crucible.datamod import count_icons
from crucible.datamod.shop import SEND_WAVE, choice_key


@pytest.fixture
def techs() -> dict[str, int]:
    """A stand-in for the data mod's manifest: every tech a scenario looks up, the boons too."""
    keys = [SEND_WAVE, choice_key(1), choice_key(2), *(u.tech for u in meta.UPGRADES)]
    keys += [m.id for m in catalogue.ALL] + [p.copy_key for p in meta.PLACES if p.copy_of >= 0]
    keys += [count_icons.key(label) for label in count_icons.labels()]
    keys += [boon_techs.key(b, tier) for b in boons.ALL for tier in b.tiers]

    return {key: 1000 + n for n, key in enumerate(keys)}
