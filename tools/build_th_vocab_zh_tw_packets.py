#!/usr/bin/env python3
"""Build bounded zh-TW authoring packets from the frozen Thai 5,000 ledger."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


FIELDS = [
    "source_candidate_id",
    "normalized_lemma",
    "pos",
    "yaitron_entry_id",
    "translation_en",
    "similar_translations_en",
    "headword_entry_count",
    "headword_pos_values",
    "translation_zh_tw_candidate",
    "candidate_status",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_reviewed(tasks: Path) -> set[str]:
    root = tasks / "TH_KNOWLEDGE_LANES_20260710"
    ids: set[str] = set()
    for name in (
        "TH_A1_ZH_TW_REVIEWED_SIDECAR_MERGED_20260711.tsv",
        "TH_A1_ZH_TW_RECHECKED_SIDECAR_20260711.tsv",
    ):
        ids.update(row["source_candidate_id"] for row in read_tsv(root / name))
    return ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks_dir", type=Path)
    parser.add_argument("content_th", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--packets", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    ledger_path = args.content_th / (
        "content/review/th_5000_selection_candidate_planning_20260708/"
        "th_5000_candidate_ledger_20260708.tsv"
    )
    yaitron_path = args.content_th / (
        "content/review/th_phase_a_source_pool_20260708/"
        "source_cache/Yaitron/data/yaitron.ndjson"
    )
    ledger = read_tsv(ledger_path)
    reviewed = load_reviewed(args.tasks_dir)

    entries: dict[str, dict[str, object]] = {}
    by_headword: dict[str, list[dict[str, object]]] = {}
    with yaitron_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            entries[str(row["entry_id"])] = row
            by_headword.setdefault(str(row["headword"]), []).append(row)

    missing_rows: list[dict[str, object]] = []
    for row in ledger:
        if row["candidate_id"] in reviewed:
            continue
        match = re.search(r"yaitron:entry_id=(\d+)", row["source_signal_refs"])
        if not match or match.group(1) not in entries:
            raise ValueError(f"missing Yaitron entry for {row['candidate_id']}")
        entry = entries[match.group(1)]
        translation = entry.get("translation") or {}
        if translation.get("lang") != "en" or not str(translation.get("text", "")).strip():
            raise ValueError(f"missing English translation for {row['candidate_id']}")
        family = by_headword[row["normalized_lemma"]]
        missing_rows.append(
            {
                "source_candidate_id": row["candidate_id"],
                "normalized_lemma": row["normalized_lemma"],
                "pos": row["pos"],
                "yaitron_entry_id": match.group(1),
                "translation_en": translation["text"],
                "similar_translations_en": "; ".join(
                    str(item.get("text", ""))
                    for item in entry.get("similar_translations", [])
                    if item.get("lang") == "en" and item.get("text")
                ),
                "headword_entry_count": len(family),
                "headword_pos_values": ";".join(sorted({str(item.get("pos", "")) for item in family})),
                "translation_zh_tw_candidate": "",
                "candidate_status": "needs_authoring",
            }
        )

    if len(ledger) != 5000 or len(reviewed) != 733 or len(missing_rows) != 4267:
        raise ValueError(
            f"unexpected counts: ledger={len(ledger)} reviewed={len(reviewed)} "
            f"missing={len(missing_rows)}"
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index in range(args.packets):
        packet_rows = missing_rows[index:: args.packets]
        path = args.output_dir / f"th_vocab_zh_tw_author_packet_{index + 1:02d}.tsv"
        if path.exists() and not args.force:
            raise FileExistsError(f"refusing to overwrite existing author packet: {path}")
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(packet_rows)
        print(f"{path}: {len(packet_rows)} rows")


if __name__ == "__main__":
    main()
