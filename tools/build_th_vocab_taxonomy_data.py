#!/usr/bin/env python3
"""Build the static Thai 5,000-word taxonomy review payload."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


BIG_LABELS = {
    "01": "核心語法與造句骨架",
    "02": "泰國飲食與點餐文化",
    "03": "人際、身分與社會關係",
    "04": "旅遊、交通與地理",
    "05": "日常生活、購物與科技",
    "06": "時間、自然與環境",
    "07": "健康、醫療與安全",
    "08": "工作、教育與經濟",
    "09": "治理、法律與公共事務",
    "10": "文化、宗教與休閒",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_i18n(merged: Path, rechecked: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for path in (merged, rechecked):
        for row in read_tsv(path):
            candidate_id = row["source_candidate_id"]
            if not candidate_id:
                raise ValueError(f"blank source_candidate_id in {path}")
            rows[candidate_id] = row
    return rows


def load_candidate_i18n(packet_dir: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    author_paths = sorted(packet_dir.glob("th_vocab_zh_tw_author_packet_*.tsv"))
    if len(author_paths) != 3:
        raise ValueError(f"expected 3 zh-TW author packets in {packet_dir}")
    for author_path in author_paths:
        suffix = author_path.stem.rsplit("_", 1)[1]
        review_path = packet_dir / f"th_vocab_zh_tw_review_packet_{suffix}.tsv"
        author_rows = read_tsv(author_path)
        review_rows = read_tsv(review_path)
        if [row["source_candidate_id"] for row in author_rows] != [
            row["source_candidate_id"] for row in review_rows
        ]:
            raise ValueError(f"author/review ID order mismatch for packet {suffix}")
        for author, review in zip(author_rows, review_rows, strict=True):
            if review["current_translation_zh_tw"] != author["translation_zh_tw_candidate"]:
                raise ValueError(f"review current text mismatch on {author['source_candidate_id']}")
            if review["verdict"] == "PASS":
                text = author["translation_zh_tw_candidate"]
            else:
                raise ValueError(f"unresolved review verdict on {author['source_candidate_id']}")
            if not text.strip():
                raise ValueError(f"blank reviewed candidate on {author['source_candidate_id']}")
            rows[author["source_candidate_id"]] = {
                "source_candidate_id": author["source_candidate_id"],
                "i18n_zh_tw": text,
                "learner_note_zh_tw": "Yaitron 英文來源義轉譯候選；尚待母語／owner 審查。",
                "i18n_status": "semantic_pass_native_pending",
                "source_translation_en": author["translation_en"],
            }
    return rows


def split_ids(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def build_payload(tasks: Path, candidate_packet_dir: Path | None = None) -> dict[str, object]:
    projection_path = tasks / "TH_VOCAB_TAXONOMY_5000_EPHEMERAL_V160_DELTA_PROJECTION_20260715.tsv"
    scope_path = tasks / "TH_VOCAB_TAXONOMY_A1_B2_V2_REFINED_SCOPE_MAP_20260713.tsv"
    i18n_root = tasks / "TH_KNOWLEDGE_LANES_20260710"
    projection = read_tsv(projection_path)
    scope = read_tsv(scope_path)
    i18n = load_i18n(
        i18n_root / "TH_A1_ZH_TW_REVIEWED_SIDECAR_MERGED_20260711.tsv",
        i18n_root / "TH_A1_ZH_TW_RECHECKED_SIDECAR_20260711.tsv",
    )
    reviewed_i18n_count = len(i18n)
    candidate_i18n = load_candidate_i18n(candidate_packet_dir) if candidate_packet_dir else {}
    overlap = set(i18n) & set(candidate_i18n)
    if overlap:
        raise ValueError(f"reviewed/candidate i18n overlap: {sorted(overlap)[:5]}")
    i18n.update(candidate_i18n)

    if len(projection) != 5000 or len({row["source_candidate_id"] for row in projection}) != 5000:
        raise ValueError("projection must contain exactly 5,000 unique candidates")
    if len(scope) != 159 or len({row["row_id"] for row in scope}) != 159:
        raise ValueError("scope map must contain exactly 159 unique small categories")
    expected_i18n = 5000 if candidate_packet_dir else 733
    if len(i18n) != expected_i18n:
        raise ValueError(f"expected {expected_i18n} unique zh-TW i18n rows, found {len(i18n)}")

    scope_by_id = {row["row_id"]: row for row in scope}
    leaf_members: dict[str, set[str]] = defaultdict(set)
    big_members: dict[str, set[str]] = defaultdict(set)
    words: list[dict[str, object]] = []

    for row in projection:
        candidate_id = row["source_candidate_id"]
        final_senses = json.loads(row["final_sense_routes"] or "[]")
        if row["final_adjudication_in_scope"] == "true":
            primary_ids = sorted({sense["primary_category_id"] for sense in final_senses if sense["primary_category_id"]})
            secondary_ids = sorted({item for sense in final_senses for item in sense["secondary_category_ids"]})
            status = row["final_taxonomy_disposition"].lower()
        else:
            primary_ids = [row["primary_category_id"]] if row["primary_category_id"] else []
            secondary_ids = split_ids(row["secondary_category_ids"])
            status = row["draft_classification_status"]

        unknown_primary = set(primary_ids) - set(scope_by_id)
        if unknown_primary:
            raise ValueError(f"unknown primary taxonomy IDs on {candidate_id}: {sorted(unknown_primary)}")
        legacy_secondary_annotations = sorted(set(secondary_ids) - set(scope_by_id))
        secondary_ids = sorted(set(secondary_ids) & set(scope_by_id))
        for category_id in primary_ids:
            leaf_members[category_id].add(candidate_id)
            big_members[scope_by_id[category_id]["parent_domain_no"]].add(candidate_id)

        sidecar = i18n.get(candidate_id)
        words.append(
            {
                "id": candidate_id,
                "rank": int(candidate_id.rsplit("-", 1)[1]),
                "lemma": row["normalized_lemma"],
                "pos": row["candidate_pos"],
                "cefr": row["cefr_classification"],
                "status": status,
                "classified": bool(primary_ids),
                "primary_category_ids": primary_ids,
                "secondary_category_ids": secondary_ids,
                "legacy_secondary_annotations": legacy_secondary_annotations,
                "identity_structure": row["final_identity_structure"],
                "senses": [
                    {
                        "entry": sense["entry_no"],
                        "sense": sense["sense_no"],
                        "denotation_en": sense["denotation"],
                        "primary_category_id": sense["primary_category_id"],
                        "secondary_category_ids": sense["secondary_category_ids"],
                    }
                    for sense in final_senses
                ],
                "zh_tw": sidecar["i18n_zh_tw"] if sidecar else "",
                "zh_tw_note": sidecar["learner_note_zh_tw"] if sidecar else "",
                "source_translation_en": sidecar.get("source_translation_en", "") if sidecar else "",
                "i18n_status": sidecar["i18n_status"] if sidecar else "missing",
                "review_status": "needs_review",
                "native_status": "native_pending",
                "production_promotion_allowed": False,
            }
        )

    small_categories = []
    for row in sorted(scope, key=lambda item: (item["parent_domain_no"], item["row_id"])):
        small_categories.append(
            {
                "id": row["row_id"],
                "label": row["category_label_zh"],
                "big_no": row["parent_domain_no"],
                "big_id": row["parent_domain_id"],
                "big_label": BIG_LABELS[row["parent_domain_no"]],
                "word_count": len(leaf_members[row["row_id"]]),
                "status": row["row_status"],
                "level_range": row["level_range"],
                "scope_note": row["scope_note"],
            }
        )

    big_categories = []
    for number, label in BIG_LABELS.items():
        children = [row for row in small_categories if row["big_no"] == number]
        big_categories.append(
            {
                "no": number,
                "id": next(row["big_id"] for row in children),
                "label": label,
                "word_count": len(big_members[number]),
                "primary_memberships": sum(row["word_count"] for row in children),
                "small_category_count": len(children),
                "used_small_category_count": sum(row["word_count"] > 0 for row in children),
            }
        )

    categorized = sum(word["classified"] for word in words)
    reviewed_unmapped = sum(
        not word["classified"] and "reviewed_unmapped" in word["status"] for word in words
    )
    taxonomy_pending = len(words) - categorized - reviewed_unmapped
    memberships = sum(len(word["primary_category_ids"]) for word in words)
    return {
        "schema_version": "th_vocab_taxonomy_viewer.v1",
        "source": {
            "taxonomy_closeout_commit": "937ea1b2",
            "v160_sha256": "2cb92e607a67487a9a977b5ad3e153b14b9fe63daa3bdd50d405bad692c7dca5",
            "projection": projection_path.name,
            "scope_map": scope_path.name,
        },
        "status": {
            "review": "needs_review",
            "native": "native_pending",
            "production": False,
            "surface": "read_only_review",
        },
        "summary": {
            "total_words": len(words),
            "categorized_words": categorized,
            "unclassified_words": len(words) - categorized,
            "pending_words": len(words) - categorized,
            "taxonomy_pending_words": taxonomy_pending,
            "reviewed_unmapped_words": reviewed_unmapped,
            "primary_memberships": memberships,
            "big_categories": len(big_categories),
            "small_categories": len(small_categories),
            "used_small_categories": sum(row["word_count"] > 0 for row in small_categories),
            "zh_tw_i18n": len(i18n),
            "missing_zh_tw_i18n": len(words) - len(i18n),
            "reviewed_zh_tw_i18n": reviewed_i18n_count,
            "candidate_zh_tw_i18n": len(candidate_i18n),
        },
        "big_categories": big_categories,
        "small_categories": small_categories,
        "words": words,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate-packet-dir", type=Path)
    args = parser.parse_args()
    payload = build_payload(args.tasks_dir, args.candidate_packet_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "window.TH_VOCAB_TAXONOMY = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
