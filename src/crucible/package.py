"""The Crucible data mod packaged for the official mod site (ageofempires.com/mods): a zip with the mod's files at
its root (info.json, thumbnail.jpg, modes/..., resources/...), a page image, and a text file with the title and
description to paste. The upload is done by hand, signed in.

Published, the mod gets an id; whether a scenario then records the data mod it was made with (so the campaign's
"Scenario Default" picks it) is what publishing is meant to find out: a local mod isn't recorded.
"""

import shutil
import zipfile
from pathlib import Path

from aoe2ed.render.renderer import render_scenario
from PIL import Image, ImageChops, ImageDraw, ImageFont

from crucible.datamod.mod import MANIFEST, MOD
from crucible.scenarios.maps import asset

THUMBNAIL = (1280, 720)
PAGE_IMAGE = (1920, 1080)
DESCRIPTION = (
    "The data mod for Crucible, a roguelite campaign for Return of Rome: survive the waves of the Legion, pick boons "
    "between waves, and spend what you earn in the camp on upgrades that carry into every run. Pick it as the Data "
    "Mod on the campaign screen. Work in progress."
)


def _picture(size: tuple[int, int]) -> Image.Image:
    """The arena, rendered, on a card of the render's own dark backdrop, with the title."""
    arena = render_scenario(asset("arena"), orientation="diamond", grid=False).convert("RGB")
    edge = arena.getpixel((0, 0))
    arena = arena.crop(ImageChops.difference(arena, Image.new("RGB", arena.size, edge)).getbbox())
    card = Image.new("RGB", size, edge)
    top = size[1] // 4
    arena = arena.resize((int(arena.width * (size[1] - top) / arena.height), size[1] - top))
    card.paste(arena, ((size[0] - arena.width) // 2, top))

    draw = ImageDraw.Draw(card)
    font = ImageFont.load_default(size=size[1] // 9)
    draw.text((size[0] // 2, size[1] // 14), MOD, fill=(236, 214, 160), font=font, anchor="mt")

    return card


def package(mod_folder: Path, out_dir: Path) -> dict[str, Path]:
    """`out_dir/<MOD>.zip` to upload, `<MOD>.jpg` for the mod page and `<MOD>.txt` with the title and description."""
    out_dir.mkdir(parents=True, exist_ok=True)
    folder = out_dir / MOD

    if folder.exists():
        shutil.rmtree(folder)

    shutil.copytree(mod_folder, folder, ignore=shutil.ignore_patterns(MANIFEST))
    _picture(THUMBNAIL).save(folder / "thumbnail.jpg", quality=90)

    zip_path = out_dir / f"{MOD}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(folder).as_posix())  # the mod's files at the zip's root

    image = out_dir / f"{MOD}.jpg"
    _picture(PAGE_IMAGE).save(image, quality=90)
    page = out_dir / f"{MOD}.txt"
    page.write_text(f"{MOD}\n\n{DESCRIPTION}\n", encoding="utf-8")

    return {"zip": zip_path, "image": image, "page": page}
