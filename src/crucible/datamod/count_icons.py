"""Count icons for the hub's buttons: a picture per count an upgrade can show (levels bought of its levels, "2/6"),
so a button shows how far its upgrade has gone.

RoR finds a tech's picture by its icon number: `widgetui/icons.json` maps the number to a material name,
`widgetui/morematerials.json` the material to a texture file. The mod ships copies of both (made from the game's own
at build time, never committed) with a new number per count, each a PNG of its own. A trigger's Change Technology
Icon shows them; the same number set as a tech's icon in the data showed RoR's default scroll instead (icon probe,
2026-11-20).
"""

import io
import json

from aoe2ed.config import find_game_dir
from PIL import Image, ImageDraw, ImageFont

from crucible import meta
from crucible.datamod.mod import DataMod

WIDGETUI = "modes/Pompeii/widgetui"
TEXTURES = "textures/ingame/tech/crucible"
SIZE = 256  # RoR's tech pictures are 256 px squares
BACKGROUND = (20, 40, 110, 255)
TEXT = (255, 255, 255, 255)
FONT, FONT_SIZE = "arialbd.ttf", 96


def key(label: str) -> str:
    """The manifest key of a count's icon number."""
    return f"icon {label}"


def label(upgrade: meta.Upgrade, level: int) -> str:
    """What the button shows with `level` bought: "2/6"."""
    return f"{level}/{upgrade.levels}"


def labels() -> list[str]:
    """Every count a button can show while its upgrade is on offer."""
    return list(dict.fromkeys(label(u, level) for u in meta.UPGRADES for level in range(u.levels)))


def _picture(text: str) -> bytes:
    image = Image.new("RGBA", (SIZE, SIZE), BACKGROUND)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(FONT, FONT_SIZE)
    except OSError:
        font = ImageFont.load_default(size=FONT_SIZE)

    draw.text((SIZE / 2, SIZE / 2), text, fill=TEXT, font=font, anchor="mm")
    data = io.BytesIO()
    image.save(data, "PNG")

    return data.getvalue()


def add(mod: DataMod) -> None:
    game = find_game_dir() / WIDGETUI
    icons = json.loads((game / "icons.json").read_text(encoding="utf-8-sig"))
    materials = json.loads((game / "morematerials.json").read_text(encoding="utf-8-sig"))
    first = max(int(n) for n in icons["Techs"]) + 1

    for n, text in enumerate(labels()):
        number, name = first + n, f"CrucibleCount{n:03d}"
        path = f"{TEXTURES}/count_{n:03d}.png"
        mod.files[f"{WIDGETUI}/{path}"] = _picture(text)
        icons["Techs"][f"{number:03d}"] = name
        materials["GlobalTextures"].append({"TextureDef": {"Name": name, "FileName": path, "Cached": "precached"}})
        materials["Materials"].append(
            {"MaterialDef": {"Name": name, "Type": "Texture", "Blend": "None", "TextureRef": name}}
        )
        mod.manifest[key(text)] = number

    mod.files[f"{WIDGETUI}/icons.json"] = json.dumps(icons, indent=2).encode("utf-8")
    mod.files[f"{WIDGETUI}/morematerials.json"] = json.dumps(materials, indent=2).encode("utf-8")
