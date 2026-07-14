#!/usr/bin/env python3
"""Build the static zh-TW A1 curriculum explorer payload."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


THEME_RE = re.compile(r"^# Theme (\d+)｜(.+)$", re.MULTILINE)
UNIT_RE = re.compile(
    r"^## (ZH-A1-T\d{2}-U\d{2})｜([^\r\n]+)\r?\n(.*?)(?=^## ZH-A1-|^# Theme|\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_metadata(block: str) -> tuple[dict[str, str], list[str]]:
    metadata: dict[str, str] = {}
    body: list[str] = []
    for raw in block.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        candidate = line[2:].strip() if line.startswith("- ") else line
        if candidate.startswith(("類型：", "情境：", "角色：")):
            for part in candidate.split("｜"):
                if "：" in part:
                    key, value = part.split("：", 1)
                    metadata[key.strip()] = value.strip()
            continue
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            line = line[2:-2]
        body.append(line)
    return metadata, body


def build_payload(root: Path) -> dict[str, object]:
    coverage_path = root / "ZH_TW_A1_THEME_COVERAGE_V1.tsv"
    coverage = list(csv.DictReader(coverage_path.open(encoding="utf-8"), delimiter="\t"))
    content_rows = {row["record_id"]: row for row in coverage if row["record_type"] == "content_unit"}

    themes: list[dict[str, object]] = []
    units: list[dict[str, object]] = []
    for fragment in sorted((root / "fragments").glob("themes_*.md")):
        text = fragment.read_text(encoding="utf-8")
        theme_matches = list(THEME_RE.finditer(text))
        for index, theme_match in enumerate(theme_matches):
            start = theme_match.end()
            end = theme_matches[index + 1].start() if index + 1 < len(theme_matches) else len(text)
            theme_text = text[start:end]
            number = int(theme_match.group(1))
            theme_units: list[str] = []
            for match in UNIT_RE.finditer(theme_text):
                unit_id, title, block = match.groups()
                metadata, body = parse_metadata(block)
                mapping = content_rows[unit_id]
                units.append(
                    {
                        "id": unit_id,
                        "theme_id": mapping["theme_id"],
                        "theme_number": number,
                        "title": title.strip(),
                        "type": metadata.get("類型", "內容"),
                        "setting": metadata.get("情境", ""),
                        "roles": metadata.get("角色", ""),
                        "body": body,
                        "subtopic": mapping["primary_subtopic_or_requirement"],
                        "grammar": mapping["grammar_occurrences"].split(";"),
                        "frames": mapping["frame_occurrences"].split(";"),
                        "formulaic": mapping["formulaic_occurrences"].split(";"),
                        "pragmatics": mapping["pragmatics_occurrences"].split(";"),
                    }
                )
                theme_units.append(unit_id)
            themes.append(
                {
                    "number": number,
                    "name": theme_match.group(2).strip(),
                    "id": units[-1]["theme_id"] if theme_units else "",
                    "unit_ids": theme_units,
                }
            )

    denominator_rows = []
    for row in coverage:
        if row["record_type"] == "content_unit":
            continue
        denominator_rows.append(
            {
                "kind": row["record_type"],
                "id": row["record_id"],
                "theme_id": row["theme_id"],
                "status": row["status"],
                "unit_ids": [value for value in row["content_unit_ids"].split(";") if value],
                "quote": row["exact_evidence_quote"],
                "requirement": row["primary_subtopic_or_requirement"],
                "gap_reason": "" if row["gap_reason"] == "none" else row["gap_reason"],
            }
        )

    return {
        "schema_version": "zh_tw_a1_curriculum_explorer.v1",
        "status": {"review": "user-review-ready", "native": "native_pending", "production": False},
        "summary": {
            "themes": len(themes),
            "units": len(units),
            "teaching_targets": sum(row["kind"] == "teaching_target" for row in denominator_rows),
            "richness_rows": sum(row["kind"] == "richness_row" for row in denominator_rows),
            "evidenced": sum(row["status"] == "evidenced" for row in denominator_rows),
            "genuine_gaps": sum(row["status"] == "genuine_gap" for row in denominator_rows),
        },
        "themes": themes,
        "units": units,
        "coverage": denominator_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("curriculum_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = build_payload(args.curriculum_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "window.ZH_A1_CURRICULUM = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
