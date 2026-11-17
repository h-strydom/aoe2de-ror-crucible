import pytest

from crucible import meta
from crucible.bonuses import catalogue
from crucible.datamod.shop import END_RUN, SEND_WAVE, choice_key


@pytest.fixture
def techs() -> dict[str, int]:
    """A stand-in for the data mod's manifest: every tech a scenario looks up, the boons too."""
    keys = [SEND_WAVE, END_RUN, choice_key(1), choice_key(2), meta.BEGIN, *(u.tech for u in meta.UPGRADES)]
    keys += [m.id for m in catalogue.ALL]

    return {key: 1000 + n for n, key in enumerate(keys)}
