import pytest

from crucible import meta
from crucible.datamod.shop import SEND_WAVE, choice_key


@pytest.fixture
def techs() -> dict[str, int]:
    """A stand-in for the data mod's manifest: every tech a scenario looks up."""
    keys = [SEND_WAVE, choice_key(1), choice_key(2), meta.BEGIN, *(u.tech for u in meta.UPGRADES)]

    return {key: 1000 + n for n, key in enumerate(keys)}
