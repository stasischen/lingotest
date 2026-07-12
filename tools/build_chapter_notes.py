"""Build the browser-ready chapter guide from reviewed JSON segments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    notes: list[dict] = []
    for path in args.inputs:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list):
            raise SystemExit(f"{path}: expected a JSON array")
        notes.extend(payload)

    keys = [(str(note["book"]), int(note["chapter"])) for note in notes]
    if len(keys) != len(set(keys)):
        raise SystemExit("duplicate book/chapter keys in merged inputs")
    if len(notes) != 70:
        raise SystemExit(f"expected 70 chapters, got {len(notes)}")

    body = json.dumps(notes, ensure_ascii=False, indent=2)
    if args.output.suffix.lower() == ".json":
        output = f"{body}\n"
    else:
        output = (
            "// Generated from reviewed chapter-guide JSON; reference only.\n"
            f"window.CHAPTER_NOTES = {body};\n"
        )
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output} ({len(notes)} chapters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
