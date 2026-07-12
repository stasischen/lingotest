"""Validate chapter-guide JSON against sentence rows in the source Markdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


BOOK_RE = re.compile(r"^# Book (.+?)\s*$")
CHAPTER_RE = re.compile(r"^## Chapter (\d+)")


def source_inventory(path: Path) -> tuple[list[tuple[str, int]], dict[int, tuple[str, int]], dict[int, str]]:
    keys: list[tuple[str, int]] = []
    line_map: dict[int, tuple[str, int]] = {}
    surfaces: dict[int, str] = {}
    book: str | None = None
    chapter: int | None = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if match := BOOK_RE.match(line):
            book, chapter = match.group(1), None
            continue
        if match := CHAPTER_RE.match(line):
            chapter = int(match.group(1))
            if book and (book, chapter) not in keys:
                keys.append((book, chapter))
            continue
        if not (book and chapter and line.startswith("|") and not line.startswith("| ---")):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] != "Speaker" and cells[1] and cells[2]:
            line_map[number] = (book, chapter)
            surfaces[number] = cells[1]
    return keys, line_map, surfaces


def validate(source: Path, notes_path: Path, expected_books: set[str]) -> list[str]:
    source_keys, line_map, surfaces = source_inventory(source)
    expected_keys = [key for key in source_keys if key[0] in expected_books]
    notes = json.loads(notes_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if not isinstance(notes, list):
        return ["root must be a JSON array"]
    actual_keys: list[tuple[str, int]] = []
    for item_index, item in enumerate(notes):
        try:
            key = (str(item["book"]), int(item["chapter"]))
        except (KeyError, TypeError, ValueError):
            errors.append(f"item[{item_index}] has invalid book/chapter")
            continue
        actual_keys.append(key)
        if not item.get("topics_zh"):
            errors.append(f"{key}: topics_zh is empty")
        covered_lines: set[int] = set()
        for field in ("patterns", "grammar", "functions"):
            entries = item.get(field)
            if not isinstance(entries, list) or not entries:
                errors.append(f"{key}: {field} must be a non-empty array")
                continue
            for entry_index, entry in enumerate(entries):
                prefix = f"{key}: {field}[{entry_index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{prefix} is not an object")
                    continue
                if not str(entry.get("label", "")).strip():
                    errors.append(f"{prefix} label is empty")
                label = str(entry.get("label", "")).strip()
                if label in {"Thai", "---"} or label in surfaces.values():
                    errors.append(f"{prefix} label is a table token or full source sentence")
                if not str(entry.get("explanation_zh", "")).strip():
                    errors.append(f"{prefix} explanation_zh is empty")
                lines = entry.get("example_lines")
                if not isinstance(lines, list) or not lines:
                    errors.append(f"{prefix} example_lines is empty")
                    continue
                for line in lines:
                    if line_map.get(line) != key:
                        errors.append(f"{prefix} line {line} maps to {line_map.get(line)}")
                    else:
                        covered_lines.add(line)
        source_lines = {line for line, line_key in line_map.items() if line_key == key}
        missing_lines = sorted(source_lines - covered_lines)
        if missing_lines:
            errors.append(f"{key}: uncovered source lines {missing_lines}")
    if len(actual_keys) != len(set(actual_keys)):
        errors.append("duplicate chapter keys")
    if actual_keys != expected_keys:
        missing = [key for key in expected_keys if key not in actual_keys]
        extra = [key for key in actual_keys if key not in expected_keys]
        errors.append(f"chapter order/set mismatch; missing={missing}; extra={extra}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--books", required=True, help="comma-separated book IDs")
    args = parser.parse_args()
    errors = validate(args.source, args.notes, set(args.books.split(",")))
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for error in errors[:100]:
            print(f"- {error}")
        raise SystemExit(1)
    count = len(json.loads(args.notes.read_text(encoding="utf-8")))
    print(f"PASS: {args.notes} ({count} chapters)")


if __name__ == "__main__":
    main()
