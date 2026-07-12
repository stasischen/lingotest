"""Build the static sentence explorer data from the Gemini Markdown corpus."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


BOOK_RE = re.compile(r"^# Book (.+?)\s*$")
CHAPTER_RE = re.compile(r"^## Chapter (\d+)")


def level_band(book: str) -> str:
    if book in {"1", "2"}:
        return "A1 foundation"
    if book in {"3", "4"}:
        return "A1–A2 mixed"
    if book in {"5", "6", "7", "8", "9"}:
        return "A2–B1 reference"
    return "B1–B2 reference"


def parse(source: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    book = chapter = None
    for line_no, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if match := BOOK_RE.match(raw):
            book = match.group(1)
            chapter = None
            continue
        if match := CHAPTER_RE.match(raw):
            chapter = int(match.group(1))
            continue
        if not (book and chapter and raw.startswith("|") and not raw.startswith("| ---")):
            continue
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] == "Speaker":
            continue
        speaker, thai, english = cells
        rows.append(
            {
                "id": len(rows) + 1,
                "book": book,
                "chapter": chapter,
                "speaker": "Female" if "Female" in speaker else "Male" if "Male" in speaker else speaker,
                "thai": thai,
                "english": english,
                "level": level_band(book),
                "sourceLine": line_no,
            }
        )
    return rows


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_sentence_data.py SOURCE.md OUTPUT.js")
    source, output = map(Path, sys.argv[1:])
    rows = parse(source)
    books = list(dict.fromkeys(str(row["book"]) for row in rows))
    payload = {
        "meta": {
            "title": "Thai Gemini Sentence Corpus",
            "rowCount": len(rows),
            "bookCount": len(books),
            "chapterCount": len({(row["book"], row["chapter"]) for row in rows}),
            "books": books,
            "source": "content-th/docs/gemini/sentences.md",
            "status": "Reference corpus — not learner-ready or production-approved",
        },
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "window.SENTENCE_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
