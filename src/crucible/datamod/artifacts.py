"""The run's artifacts, garrisonable (scenarios/relics): a copy of RoR's walking artifact (944, a Relic Cart with the
artifact look and a garrison task) in the priest class, which garrisons where the artifact's own class never could
(engine facts: copies in the infantry or priest class garrisoned a Barracks). Its every building type takes it in
(the priest garrison category) with room for at least one. Made tough: the Legion would otherwise kill it.
"""

from crucible.datamod.mod import DataMod
from crucible.scenarios.relics import ARTIFACT_KEY, groups

SOURCE = 944
PRIEST_CLASS = 18
PRIEST_CATEGORY = 8  # garrison type bit
HIT_POINTS = 5000


def add(mod: DataMod) -> None:
    copy = mod.copy_unit(SOURCE)
    buildings = {i for ids in groups(mod.data).values() for i in ids}

    for civ in mod.data.civs:
        artifact = civ.units[copy]

        if artifact:
            artifact.class_ = PRIEST_CLASS
            artifact.hit_points = HIT_POINTS

        for i in buildings:
            unit = civ.units[i]

            if unit and unit.building:
                unit.building.garrison_type |= PRIEST_CATEGORY
                unit.garrison_capacity = max(unit.garrison_capacity, 1)

    mod.manifest[ARTIFACT_KEY] = copy
