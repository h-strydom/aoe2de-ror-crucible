"""Crucible's two mods packaged for the official mod site (ageofempires.com/mods): the data mod (MOD) and the
campaign mod (campaign.CAMPAIGN_MOD: the campaign and its intro slides). Each gets a zip with the mod's files at its
root (info.json, thumbnail.jpg, modes/..., resources/...), a page image, and a text file with the title and
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
from crucible.scenarios.campaign import CAMPAIGN_MOD
from crucible.scenarios.maps import asset

THUMBNAIL = (1280, 720)
PAGE_IMAGE = (1920, 1080)
ABOUT = (
    "Crucible is a roguelite campaign for Return of Rome: defend your Wonder against the Legion's endless waves, earn "
    "resources, and spend them in the camp on upgrades that carry into every run."
)
NEEDS = (
    "Crucible needs both of its mods: Crucible Campaign (enable it in Mods > Installed Mods) and the Crucible data "
    "mod (leave it disabled, and pick it as the Data Mod on the campaign screen)."
)
DESCRIPTIONS = {
    MOD: f"The data mod for Crucible. {ABOUT}\n\n{NEEDS}",
    CAMPAIGN_MOD: f"The Crucible campaign, with its intro slides. {ABOUT}\n\n{NEEDS}",
}


def _picture(size: tuple[int, int], title: str) -> Image.Image:
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
    draw.text((size[0] // 2, size[1] // 14), title, fill=(236, 214, 160), font=font, anchor="mt")

    return card


def _one(mod_folder: Path, out_dir: Path, name: str) -> dict[str, Path]:
    """`out_dir/<name>.zip` to upload, `<name>.jpg` for the mod page and `<name>.txt` with the title and description."""
    folder = out_dir / name

    if folder.exists():
        shutil.rmtree(folder)

    shutil.copytree(mod_folder, folder, ignore=shutil.ignore_patterns(MANIFEST))
    _picture(THUMBNAIL, name).save(folder / "thumbnail.jpg", quality=90)

    zip_path = out_dir / f"{name}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(folder).as_posix())  # the mod's files at the zip's root

    image = out_dir / f"{name}.jpg"
    _picture(PAGE_IMAGE, name).save(image, quality=90)
    page = out_dir / f"{name}.txt"
    page.write_text(f"{name}\n\n{DESCRIPTIONS[name]}\n", encoding="utf-8")

    return {"zip": zip_path, "image": image, "page": page}


def package(data_mod: Path, campaign_mod: Path, out_dir: Path) -> dict[str, Path]:
    """Both mods' upload files in `out_dir`, keyed like "Crucible zip"."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}

    for name, folder in ((MOD, data_mod), (CAMPAIGN_MOD, campaign_mod)):
        files |= {f"{name} {kind}": path for kind, path in _one(folder, out_dir, name).items()}

    return files
