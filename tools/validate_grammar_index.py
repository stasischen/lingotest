"""Validate that every chapter grammar/pattern observation has live examples."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_sentence_data(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.SENTENCE_DATA\s*=\s*(\{.*\});\s*$", text, re.S)
    if not match:
        raise SystemExit(f"{path}: cannot parse window.SENTENCE_DATA")
    return json.loads(match.group(1))


def main() -> int:
    notes = json.loads((ROOT / "sentence-explorer/chapter-notes.json").read_text(encoding="utf-8"))
    corpus = load_sentence_data(ROOT / "sentence-explorer/sentences-data.js")
    rows_by_line = {int(row["sourceLine"]): row for row in corpus["rows"]}
    observations = []
    errors = []
    for note in notes:
        for kind, key in (("pattern", "patterns"), ("grammar", "grammar")):
            for item in note[key]:
                lines = item.get("example_lines", [])
                observation = (kind, str(note["book"]), int(note["chapter"]), item["label"], lines)
                observations.append(observation)
                if not lines:
                    errors.append(f"{observation[:4]}: no example_lines")
                missing = [line for line in lines if int(line) not in rows_by_line]
                if missing:
                    errors.append(f"{observation[:4]}: missing source lines {missing}")
    if errors:
        raise SystemExit("\n".join(errors))
    patterns = sum(item[0] == "pattern" for item in observations)
    grammar = sum(item[0] == "grammar" for item in observations)
    links = sum(len(item[4]) for item in observations)
    unique_lines = len({int(line) for item in observations for line in item[4]})
    print(f"PASS observations={len(observations)} patterns={patterns} grammar={grammar} evidence_links={links} unique_source_lines={unique_lines}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
