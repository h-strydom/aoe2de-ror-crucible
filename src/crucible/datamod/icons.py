"""Upgrade icons: a tech button can only show tech icons, so each Icon borrows an existing RoR tech's picture."""

from aoe2ed import tables
from genieutils.datfile import DatFile

from crucible.bonuses.model import Icon

SOURCES: dict[Icon, str] = {
    Icon.FARM: "plow",
    Icon.FISH: "fishing_ship",
    Icon.FOOD: "domestication",
    Icon.WOOD: "woodworking",
    Icon.STONE: "stone_mining",
    Icon.GOLD: "gold_mining",
    Icon.VILLAGER: "wheel",
    Icon.TRADE: "merchant_ship",
    Icon.TECHNOLOGY: "writing",
    Icon.ACADEMY: "phalangite",
    Icon.ARCHERY_RANGE: "improved_bow",
    Icon.BARRACKS: "axe",
    Icon.DOCK: "medium_war_ship",
    Icon.GOVERNMENT_CENTER: "nobility",
    Icon.MARKET: "coinage",
    Icon.SIEGE_WORKSHOP: "catapult",
    Icon.STABLE: "cavalry",
    Icon.STORAGE_PIT: "toolworking",
    Icon.TEMPLE: "polytheism",
    Icon.TOWN_CENTER: "tool_age",
    Icon.ARCHER: "composite_bow",
    Icon.CAMEL: "heavy_cavalry",  # RoR has no camel tech
    Icon.CAVALRY: "cavalry",
    Icon.CHARIOT: "chariot",
    Icon.ELEPHANT: "war_elephant",
    Icon.INFANTRY: "long_sword",
    Icon.PRIEST: "monotheism",
    Icon.SHIP: "trireme",
    Icon.SIEGE: "heavy_catapult",
    Icon.TRANSPORT: "light_transport",
    Icon.BUILDING: "architecture",
    Icon.HOUSE: "urbanization",
    Icon.TOWER: "guard_tower",
    Icon.WALL: "fortified_wall",
}


def icon_id(icon: Icon, data: DatFile) -> int:
    """The tech icon id for `icon`: its source tech's."""
    return data.techs[tables.tech_id(SOURCES[icon].upper(), "ror")].icon_id
