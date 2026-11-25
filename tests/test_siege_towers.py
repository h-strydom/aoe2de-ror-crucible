from crucible.datamod import buildings, siege_towers
from crucible.datamod.mod import DataMod


def _mod() -> DataMod:
    mod = DataMod.from_ror()
    buildings.add(mod)
    siege_towers.add(mod)

    return mod


def _commands(mod: DataMod, tech: int, unit: int) -> list[tuple[int, int, float]]:
    effect = mod.data.effects[mod.data.techs[tech].effect_id]

    return [(c.type, c.c, c.d) for c in effect.effect_commands if c.a == unit]


def test_siege_towers_shoot_as_their_siege_line_and_follow_its_upgrades():
    mod = _mod()
    units = mod.data.civs[1].units

    for tower in siege_towers.TOWERS:
        unit = units[mod.manifest[tower.key]]
        siege = units[tower.line[0]].type_50
        assert unit.class_ == 52 and unit.enabled == 0  # a tower, switched on by trigger
        assert [(a.class_, a.amount) for a in unit.type_50.attacks] == [(a.class_, a.amount) for a in siege.attacks]
        assert (unit.type_50.max_range, unit.type_50.min_range) == (siege.max_range, siege.min_range)
        assert [(c.type, c.amount) for c in unit.creatable.resource_costs if c.type >= 0] == list(tower.costs)
        assert [(t.unit_id, t.button_id) for t in unit.creatable.train_locations] == [(118, tower.button)]

    ballista = mod.manifest["ballista_tower"]
    helepolis = _commands(mod, 27, ballista)
    assert (4, 9, 3 * 256 + 5) in helepolis  # +5 pierce: 40 to Helepolis' 45
    assert (0, 16, 627) in helepolis  # Helepolis' projectile

    tech = mod.data.techs[siege_towers.TOWER_TECH]
    assert [r for r in tech.required_techs if r >= 0] == list(siege_towers.TOWER_TECH_REQUIRES)
    assert not mod.data.effects[tech.effect_id].effect_commands  # no longer upgrades the towers


def test_siege_changes_reach_the_towers_once_but_not_their_cost():
    mod = _mod()
    catapult = mod.manifest["catapult_tower"]
    before = len(_commands(mod, 37, catapult))
    siege_towers.mirror(mod)
    alchemy = _commands(mod, 37, catapult)  # +1 attack to each of the Stone Thrower line
    assert before == 0 and alchemy.count((4, 9, 4 * 256 + 1)) == 1  # once, and the towers' fire arrows undone

    cost = mod.new_effect("cost", [(5, -1, 13, 104, 0.5)])  # a siege cost cut
    siege_towers.mirror(mod)
    assert not [c for c in mod.data.effects[cost].effect_commands if c.a == catapult]


def test_siege_towers_take_no_tower_range_or_attack_and_no_siege_hit_points():
    mod = _mod()
    siege_towers.mirror(mod)
    names = {t.name: i for i, t in enumerate(mod.data.techs)}

    for tower in siege_towers.TOWERS:
        unit = mod.manifest[tower.key]
        wood = _commands(mod, names["Wood Working"], unit)  # +1 range to towers, undone
        assert (4, siege_towers.RANGE, -1.0) in wood
        alchemy = mod.data.effects[mod.data.techs[names["Alchemy"]].effect_id].effect_commands
        tower_fire = [c.d for c in alchemy if c.b == 52 and c.c == siege_towers.ATTACK]
        assert all((4, siege_towers.ATTACK, -d) in _commands(mod, names["Alchemy"], unit) for d in tower_fire)
        assert mod.data.civs[1].units[unit].type_50.break_off_combat == 26 if tower.siege_class == 13 else True

    hit_points = mod.new_effect("siege hit points", [(5, -1, 13, 0, 1.1)])
    siege_towers.mirror(mod)
    assert not [c for c in mod.data.effects[hit_points].effect_commands if c.a == mod.manifest["catapult_tower"]]
