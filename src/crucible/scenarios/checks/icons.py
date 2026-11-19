"""Icons: can the data mod bring tech icons of its own, and can a trigger swap a button's icon mid-game? If so, the
hub's upgrade buttons can show their count ("0/5") on the icon.

RoR finds a tech's picture by its icon number: `widgetui/icons.json` maps the number to a material name,
`widgetui/morematerials.json` the material to a texture file. The mod ships copies of both (made from the game's own
at build time, never committed) with new numbers for pictures of its own: PNG ("0/5" to "4/5", dark blue) and DDS
("0/5" to "4/5", dark red).

On the Wonder: 1, a tech with the first PNG icon; 2, one with the first DDS icon; 3, one whose icon a trigger swaps
every 5 seconds through the PNG ones; 4, one whose icon a trigger swaps through RoR's own first five (tells whether
Change Technology Icon works at all).
"""

import io
import json

from aoe2ed.config import find_game_dir
from PIL import Image, ImageDraw, ImageFont

NAME = "icons"
BOONS = ()
BUTTONS = {}
PLAYER, WONDER = 1, 276
INTERVAL = 5  # seconds
SIZE = 256  # RoR's tech pictures are 256 px squares
COUNT = 5
WIDGETUI = "modes/Pompeii/widgetui"
TEXTURES = "textures/ingame/tech/crucible"
KINDS = {"png": (20, 40, 110), "dds": (110, 25, 25)}  # file type -> background
TECHS = {  # manifest key -> (button, title)
    "probe_icon_png": (1, "Probe: PNG icon"),
    "probe_icon_dds": (2, "Probe: DDS icon"),
    "probe_icon_swap": (3, "Probe: icon swapped (PNG)"),
    "probe_icon_ror": (4, "Probe: icon swapped (RoR's)"),
}


def _picture(text: str, background: tuple[int, int, int], kind: str) -> bytes:
    image = Image.new("RGBA", (SIZE, SIZE), (*background, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arialbd.ttf", 110)
    except OSError:
        font = ImageFont.load_default(size=110)

    draw.text((SIZE / 2, SIZE / 2), text, fill=(255, 255, 255, 255), font=font, anchor="mm")
    data = io.BytesIO()

    if kind == "dds":
        image.save(data, "DDS", pixel_format="DXT5")
    else:
        image.save(data, "PNG")

    return data.getvalue()


def icon_numbers(first: int) -> dict[str, list[int]]:
    """File type -> its icons' numbers, from the first free one."""
    return {kind: [first + k * COUNT + n for n in range(COUNT)] for k, kind in enumerate(KINDS)}


def datamod(mod) -> None:
    from crucible.bonuses.model import Icon
    from crucible.datamod.icons import icon_id

    game = find_game_dir() / WIDGETUI
    icons = json.loads((game / "icons.json").read_text(encoding="utf-8-sig"))
    materials = json.loads((game / "morematerials.json").read_text(encoding="utf-8-sig"))
    first = max(int(n) for n in icons["Techs"]) + 1
    numbers = icon_numbers(first)

    for kind, background in KINDS.items():
        for n, number in enumerate(numbers[kind]):
            name = f"CrucibleProbe{kind.upper()}{n}"
            path = f"{TEXTURES}/{kind}_{n}.{kind}"
            mod.files[f"{WIDGETUI}/{path}"] = _picture(f"{n}/{COUNT - 1}", background, kind)
            icons["Techs"][f"{number:03d}"] = name
            materials["GlobalTextures"].append({"TextureDef": {"Name": name, "FileName": path, "Cached": "precached"}})
            materials["Materials"].append(
                {"MaterialDef": {"Name": name, "Type": "Texture", "Blend": "None", "TextureRef": name}}
            )

    mod.files[f"{WIDGETUI}/icons.json"] = json.dumps(icons, indent=2).encode("utf-8")
    mod.files[f"{WIDGETUI}/morematerials.json"] = json.dumps(materials, indent=2).encode("utf-8")
    starts = {
        "probe_icon_png": numbers["png"][0],
        "probe_icon_dds": numbers["dds"][0],
        "probe_icon_swap": numbers["png"][0],
        "probe_icon_ror": icon_id(Icon.TECHNOLOGY, mod.data),
    }

    for key, (button, title) in TECHS.items():
        mod.manifest[key] = mod.new_tech(
            f"Crucible {key}",
            effect=mod.new_effect(f"Crucible {key}", []),
            title=title,
            description=title,
            tooltip=title,
            icon=starts[key],
            location=WONDER,
            button=button,
            research_time=60,
        )

    mod.manifest["probe_icon_first"] = first


def setup(o, ctx, techs: dict[str, int], top: int) -> str:
    numbers = icon_numbers(techs["probe_icon_first"])
    swaps = {"probe_icon_swap": numbers["png"], "probe_icon_ror": list(range(1, COUNT + 1))}

    for key, cycle in swaps.items():
        for step, number in enumerate(cycle):
            ctx.trigger(
                f"Icons: {key} {step}",
                [{"type": "timer", "timer": INTERVAL * (step + 1)}],
                [
                    {
                        "type": "change_technology_icon",
                        "source_player": PLAYER,
                        "technology": techs[key],
                        "quantity": number,
                    }
                ],
            )

    return f"""ICONS. Select the Wonder. Button 1: a PNG icon of the mod's own (blue "0/4"). Button 2: a DDS one (red
"0/4"). Button 3: starts on blue "0/4", and its icon should step through "1/4" to "4/4", one every 5 s. Button 4: its
icon steps through RoR's icons 1 to 5, one every 5 s. Look at each: does 1 or 2 show the picture (or black, or
another icon)? Do 3 and 4 change? (Icon numbers from {numbers['png'][0]}.)"""
