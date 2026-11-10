"""The strings the mod ships (names, tooltips), in the file the game copies into new mods for theirs."""

from pathlib import Path

# RoR's mode folder has no modded-strings file of its own, so it ships at both paths until a playtest shows which
# one RoR reads.
STRINGS_DIRS = (
    Path("resources") / "en" / "strings" / "key-value",
    Path("modes") / "Pompeii" / "resources" / "en" / "strings" / "key-value",
)

STRINGS_FILE = "key-value-modded-strings-utf8.txt"
FIRST_STRING = 7_100_000


class Strings:
    """Hands out string ids from FIRST_STRING up, and writes them all out."""

    def __init__(self, first: int = FIRST_STRING) -> None:
        self.next_id = first
        self.texts: dict[int, str] = {}

    def add(self, text: str) -> int:
        string_id = self.next_id
        self.texts[string_id] = text
        self.next_id += 1

        return string_id

    def lines(self) -> str:
        """One `id "text"` line per string, newlines written as \\n."""
        return "".join(f'{string_id} "{text.replace(chr(10), "\\n")}"\n' for string_id, text in self.texts.items())

    def write(self, folder: Path) -> None:
        for strings_dir in STRINGS_DIRS:
            (folder / strings_dir).mkdir(parents=True, exist_ok=True)
            (folder / strings_dir / STRINGS_FILE).write_text(self.lines(), encoding="utf-8")
