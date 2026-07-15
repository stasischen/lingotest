#!/usr/bin/env python3
"""Build the static Thai A1 curriculum explorer payload."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


THEME_RE = re.compile(r"^# Theme (\d+)｜(.+)$", re.MULTILINE)
UNIT_RE = re.compile(
    r"^## (TH-A1-T\d{2}-U\d{2})｜([^\r\n]+)\r?\n(.*?)(?=^## TH-A1-|^# Theme|\Z)",
    re.MULTILINE | re.DOTALL,
)
I18N_UNIT_RE = re.compile(
    r"^## (TH-A1-T\d{2}-U\d{2})｜([^\r\n]+)\r?\n(.*?)(?=^## TH-A1-|\Z)",
    re.MULTILINE | re.DOTALL,
)


def strip_outer_bold(value: str) -> str:
    return value[2:-2] if value.startswith("**") and value.endswith("**") and len(value) > 4 else value


def parse_block(block: str, metadata_keys: tuple[str, ...]) -> tuple[dict[str, str], list[str]]:
    metadata: dict[str, str] = {}
    body: list[str] = []
    for raw in block.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        candidate = line[2:].strip() if line.startswith("- ") else line
        if candidate.startswith(metadata_keys):
            for part in candidate.split("｜"):
                if "：" in part:
                    key, value = part.split("：", 1)
                    metadata[key.strip()] = value.strip()
            continue
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            line = line[2:-2]
        body.append(line)
    return metadata, body


def load_i18n(root: Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for fragment in sorted((root / "i18n" / "zh_tw").glob("themes_*.md")):
        text = fragment.read_text(encoding="utf-8")
        for match in I18N_UNIT_RE.finditer(text):
            unit_id, title, block = match.groups()
            if unit_id in rows:
                raise ValueError(f"duplicate zh-TW unit: {unit_id}")
            metadata, body = parse_block(block, ("類型：", "情境：", "角色：", "傳送者與接收者："))
            rows[unit_id] = {"title": title.strip(), "metadata": metadata, "body": body}
    return rows


def build_payload(root: Path) -> dict[str, object]:
    coverage_path = root / "TH_A1_THEME_COVERAGE_V1.tsv"
    coverage_rows = list(csv.DictReader(coverage_path.open(encoding="utf-8"), delimiter="\t"))
    denominator_rows = []
    theme_ids: list[str] = []
    unit_mapping: dict[str, list[dict[str, object]]] = {}
    for row in coverage_rows:
        if row["theme_id"] not in theme_ids:
            theme_ids.append(row["theme_id"])
        item = {
            "kind": row["record_type"],
            "id": row["record_id"],
            "theme_id": row["theme_id"],
            "status": row["status"],
            "unit_ids": [value for value in row["content_unit_ids"].split(";") if value],
            "quote": strip_outer_bold(row["exact_evidence_quote"]),
            "requirement": row["primary_subtopic_or_requirement"],
            "gap_reason": "" if row["gap_reason"] == "none" else row["gap_reason"],
        }
        denominator_rows.append(item)
        for unit_id in item["unit_ids"]:
            unit_mapping.setdefault(unit_id, []).append(item)
    if len(theme_ids) != 12:
        raise ValueError(f"expected 12 coverage themes, found {len(theme_ids)}")

    i18n = load_i18n(root)
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
            theme_id = theme_ids[number - 1]
            theme_units: list[str] = []
            for match in UNIT_RE.finditer(theme_text):
                unit_id, title, block = match.groups()
                if unit_id not in i18n:
                    raise ValueError(f"missing zh-TW i18n: {unit_id}")
                metadata, body = parse_block(block, ("ประเภท：", "สถานการณ์：", "ตัวละคร：", "ผู้ส่งและผู้รับ："))
                zh = i18n[unit_id]
                mappings = unit_mapping.get(unit_id, [])
                units.append(
                    {
                        "id": unit_id,
                        "theme_id": theme_id,
                        "theme_number": number,
                        "title": title.strip(),
                        "type": metadata.get("ประเภท", "เนื้อหา"),
                        "setting": metadata.get("สถานการณ์", ""),
                        "roles": metadata.get("ตัวละคร", metadata.get("ผู้ส่งและผู้รับ", "")),
                        "body": body,
                        "zh_tw": {
                            "title": zh["title"],
                            "type": zh["metadata"].get("類型", "內容"),
                            "setting": zh["metadata"].get("情境", ""),
                            "roles": zh["metadata"].get("角色", zh["metadata"].get("傳送者與接收者", "")),
                            "body": zh["body"],
                        },
                        "teaching_targets": sum(item["kind"] == "teaching_target" for item in mappings),
                        "richness_rows": sum(item["kind"] == "richness_row" for item in mappings),
                    }
                )
                theme_units.append(unit_id)
            theme_coverage = [row for row in denominator_rows if row["theme_id"] == theme_id]
            themes.append(
                {
                    "number": number,
                    "name": theme_match.group(2).strip(),
                    "id": theme_id,
                    "unit_ids": theme_units,
                    "evidenced": sum(row["status"] == "evidenced" for row in theme_coverage),
                    "genuine_gaps": sum(row["status"] == "genuine_gap" for row in theme_coverage),
                }
            )

    source_ids = {unit["id"] for unit in units}
    i18n_ids = set(i18n)
    if len(units) != 136 or len(source_ids) != 136:
        raise ValueError(f"expected 136 unique Thai units, found {len(units)} / {len(source_ids)}")
    if source_ids != i18n_ids:
        raise ValueError(f"Thai / zh-TW ID mismatch: source_only={source_ids-i18n_ids}, i18n_only={i18n_ids-source_ids}")
    if len(denominator_rows) != 218:
        raise ValueError(f"expected 218 coverage rows, found {len(denominator_rows)}")
    if sum(row["kind"] == "teaching_target" for row in denominator_rows) != 101:
        raise ValueError("expected exactly 101 teaching targets")
    if sum(row["kind"] == "richness_row" for row in denominator_rows) != 117:
        raise ValueError("expected exactly 117 richness rows")

    source_text = {unit["id"]: "\n".join(unit["body"]) for unit in units}
    for row in denominator_rows:
        unknown_ids = set(row["unit_ids"]) - source_ids
        if unknown_ids:
            raise ValueError(f"coverage row {row['id']} references unknown units: {unknown_ids}")
        if row["status"] == "evidenced":
            if not row["quote"] or not row["unit_ids"]:
                raise ValueError(f"evidenced row {row['id']} lacks quote or unit IDs")
            if not any(row["quote"] in source_text[unit_id] for unit_id in row["unit_ids"]):
                raise ValueError(f"evidence quote for {row['id']} is absent from cited Thai units")
        elif row["status"] == "genuine_gap":
            if row["quote"] or row["unit_ids"] or not row["gap_reason"]:
                raise ValueError(f"genuine gap {row['id']} has evidence or lacks a reason")
        else:
            raise ValueError(f"unexpected coverage status on {row['id']}: {row['status']}")

    return {
        "schema_version": "th_a1_curriculum_explorer.v1",
        "status": {
            "review": "needs_review",
            "native": "native_pending",
            "production": False,
            "thai_semantic_review": "pass_native_pending",
            "zh_tw_i18n_review": "pass_native_pending",
        },
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
        "window.TH_A1_CURRICULUM = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
