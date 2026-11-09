"""Copy units from AoE2's data file (including the Chronicles civs, which live in it) into Return of Rome's.

RoR's data file keeps AoE2's unit ids, but it reuses some slots for its own units (38 is AoE2's Knight and RoR's
Cavalry) and about a third of its graphic ids point at different sprites. RoR does read sprites from the shared
graphics folder (its own Coustillier entry uses AoE2's), so a unit can come across without copying any sprite
file: only its data, with every graphic, sound and linked unit (corpse, projectile, blood) it refers to.

- A graphic is reused when RoR's entry at that id names the same sprite file; otherwise it's appended to RoR's
  graphics table (with its deltas, recursively) and the unit points at the new id.
- A sound is reused when RoR's entry at that id plays the same files; otherwise it's appended. (DE mostly plays
  the wwise ids, which are hashes and are copied as they are.)
- A linked unit is ported the same way and appended to every civ.

Strings and icons keep AoE2's ids; whether RoR shows the right name and icon is part of the test.
Nothing here copies game files: the data mod refers to sprites the player's own install already has.
"""
from __future__ import annotations

import copy

UNIT_GRAPHICS = ("dying_graphic", "undead_graphic", "standing_graphic")    # an id, or a tuple of ids
MOVE_GRAPHICS = ("walking_graphic", "running_graphic")
ATTACK_GRAPHICS = ("attack_graphic", "attack_graphic_2")
CREATABLE_GRAPHICS = ("garrison_graphic", "hero_glow_graphic", "idle_attack_graphic", "spawning_graphic",
                      "special_graphic", "upgrade_graphic")
TASK_GRAPHICS = ("carrying_graphic_id", "moving_graphic_id", "proceeding_graphic_id", "working_graphic_id")
UNIT_SOUNDS = ("damage_sound", "dying_sound", "selection_sound", "train_sound")
BIRD_SOUNDS = ("attack_sound", "move_sound")
TASK_SOUNDS = ("resource_deposit_sound_id", "resource_gathering_sound_id")
UNIT_LINKS = ("dead_unit_id", "blood_unit_id")
MOVE_LINKS = ("tracking_unit",)
ATTACK_LINKS = ("projectile_unit_id",)
CREATABLE_LINKS = ("charge_projectile_unit", "secondary_projectile_unit")


class Porter:
    """Ports units from `src` (AoE2's DatFile) into `dst` (RoR's), sharing graphics, sounds and linked units
    between calls. Units are taken from source civ `src_civ`."""

    def __init__(self, src, dst, src_civ: int = 0):
        self.src, self.dst, self.src_civ = src, dst, src_civ
        self.graphics: dict[int, int] = {}
        self.sounds: dict[int, int] = {}
        self.units: dict[int, int] = {}
        self.added_graphics = self.added_sounds = 0

    # ---- graphics and sounds ----
    def graphics_of(self, value):
        """A graphic field is either one id or a tuple of ids."""
        return tuple(self.graphic(g) for g in value) if isinstance(value, (tuple, list)) else self.graphic(value)

    def graphic(self, gid: int) -> int:
        if gid is None or gid < 0 or gid >= len(self.src.graphics) or self.src.graphics[gid] is None:
            return gid
        if gid in self.graphics:
            return self.graphics[gid]
        g = self.src.graphics[gid]
        mine = self.dst.graphics[gid] if gid < len(self.dst.graphics) else None
        if mine is not None and mine.file_name.lower() == g.file_name.lower() and mine.frame_count == g.frame_count:
            self.graphics[gid] = gid
            return gid
        new_id = len(self.dst.graphics)
        self.graphics[gid] = new_id
        ng = copy.deepcopy(g)
        ng.id = new_id
        self.dst.graphics.append(ng)
        self.added_graphics += 1
        for delta in ng.deltas:
            delta.graphic_id = self.graphic(delta.graphic_id)
        ng.sound_id = self.sound(ng.sound_id)
        for angle in ng.angle_sounds:
            for f in ("sound_id", "sound_id_2", "sound_id_3"):
                if hasattr(angle, f):
                    setattr(angle, f, self.sound(getattr(angle, f)))
        return new_id

    def sound(self, sid: int) -> int:
        if sid is None or sid < 0 or sid >= len(self.src.sounds) or self.src.sounds[sid] is None:
            return sid
        if sid in self.sounds:
            return self.sounds[sid]
        s = self.src.sounds[sid]
        mine = self.dst.sounds[sid] if sid < len(self.dst.sounds) else None
        files = lambda snd: [i.filename.lower() for i in snd.items]
        if mine is not None and files(mine) == files(s):
            self.sounds[sid] = sid
            return sid
        new_id = len(self.dst.sounds)
        ns = copy.deepcopy(s)
        ns.id = new_id
        self.dst.sounds.append(ns)
        self.sounds[sid] = new_id
        self.added_sounds += 1
        return new_id

    # ---- units ----
    def unit(self, uid: int) -> int:
        """Port source unit `uid`, returning its id in `dst`. Linked units are ported after it."""
        if uid is None or uid < 0:
            return uid
        if uid in self.units:
            return self.units[uid]
        src_unit = self.src.civs[self.src_civ].units[uid]
        if src_unit is None:
            return -1
        new_id = len(self.dst.civs[0].units)
        self.units[uid] = new_id
        for civ in self.dst.civs:                 # reserve the slot: linked units are appended while remapping
            civ.units.append(None)
        u = copy.deepcopy(src_unit)
        u.id = u.copy_id = u.base_id = new_id
        self._remap(u)
        for civ in self.dst.civs:
            civ.units[new_id] = copy.deepcopy(u)
        return new_id

    def _remap(self, u) -> None:
        for f in UNIT_GRAPHICS:
            setattr(u, f, self.graphics_of(getattr(u, f)))
        for dg in u.damage_graphics or []:
            dg.graphic_id = self.graphic(dg.graphic_id)
        for f in UNIT_SOUNDS:
            setattr(u, f, self.sound(getattr(u, f)))
        # Links last: they append units, and this unit already has its id.
        links = [(u, f) for f in UNIT_LINKS]
        if u.dead_fish:
            for f in MOVE_GRAPHICS:
                setattr(u.dead_fish, f, self.graphics_of(getattr(u.dead_fish, f)))
            links += [(u.dead_fish, f) for f in MOVE_LINKS]
        if u.bird:
            for f in BIRD_SOUNDS:
                setattr(u.bird, f, self.sound(getattr(u.bird, f)))
            for t in u.bird.tasks:
                for f in TASK_GRAPHICS:
                    setattr(t, f, self.graphic(getattr(t, f)))
                for f in TASK_SOUNDS:
                    setattr(t, f, self.sound(getattr(t, f)))
        if u.type_50:
            for f in ATTACK_GRAPHICS:
                setattr(u.type_50, f, self.graphic(getattr(u.type_50, f)))
            links += [(u.type_50, f) for f in ATTACK_LINKS]
        if u.creatable:
            for f in CREATABLE_GRAPHICS:
                if hasattr(u.creatable, f):
                    setattr(u.creatable, f, self.graphic(getattr(u.creatable, f)))
            links += [(u.creatable, f) for f in CREATABLE_LINKS]
        for obj, f in links:
            value = getattr(obj, f)
            if value is not None and value >= 0:
                setattr(obj, f, self.unit(value))      # a link back to a unit already ported reuses its id
