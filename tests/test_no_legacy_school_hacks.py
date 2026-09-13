from __future__ import annotations

from pathlib import Path
import unittest


TEXT_SUFFIXES = {
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
LEGACY_TERM = "school-hacks"


class NoLegacySchoolHacksTest(unittest.TestCase):
    def test_repository_contains_no_school_hacks_references(self):
        root = Path(__file__).resolve().parents[1]
        offenders: list[str] = []

        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            relative = path.relative_to(root)
            if LEGACY_TERM in relative.as_posix().lower():
                offenders.append(str(relative))
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if LEGACY_TERM in content.lower():
                offenders.append(str(relative))

        self.assertEqual([], offenders, f"Legacy School Hacks references found: {offenders}")


if __name__ == "__main__":
    unittest.main()
