#!/usr/bin/env python3
"""Build the static cross-language review/reference payload deterministically."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
DEFAULT_AGGREGATOR = HERE.parents[2] / "release-aggregator"
DEFAULT_OUTPUT = HERE.parents[1] / "sentence-explorer/cross-language-data.v1.json"
TASK = "docs/tasks/A1_B2_CROSS_LANGUAGE_GEMINI_RICHNESS_CURRICULUM_20260712/cross_language_trial"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def split(value: str) -> list[str]:
    return [] if value in {"", "none"} else value.split(" || ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregator", type=Path, default=DEFAULT_AGGREGATOR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    trial = args.aggregator / TASK

    common = read_tsv(trial / "common_decisions.v1.tsv")
    adaptations = read_tsv(trial / "language_adaptations.v1.tsv")
    children = read_tsv(trial / "language_specific_children.v1.tsv")
    owners = read_tsv(trial / "knowledge_owners.v1.tsv")
    coverage = read_tsv(trial / "coverage_matrix.v1.tsv")
    baseline = read_tsv(trial / "th_family_routing_baseline.v1.tsv")
    routing = read_tsv(trial / "th_knowledge_owner_routing_dispositions.v1.tsv")
    projections = read_tsv(trial / "canonical_target_projection.v1.tsv")
    countertests = read_tsv(trial / "countertest_evidence.v1.tsv")
    blocker_rows = read_tsv(trial / "countertest_evidence_blockers.v1.tsv")
    source_dispositions = read_tsv(trial / "source_family_dispositions.v1.tsv")

    by_common: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in adaptations: by_common[row["common_decision_id"]]["adaptations"].append(row)
    for row in children: by_common[row["parent_common_decision_id"]]["children"].append(row)
    for row in owners: by_common[row["common_decision_id"]]["owners"].append(row)
    for row in coverage: by_common[row["common_decision_id"]]["coverage"].append(row)
    for row in countertests:
        if row["language_child_id"] == "none": by_common[row["common_decision_id"]]["countertests"].append(row)

    common_items = []
    for row in common:
        cid = row["common_decision_id"]
        common_items.append({
            **row,
            "adaptations": sorted(by_common[cid]["adaptations"], key=lambda x: x["language"]),
            "children": sorted(by_common[cid]["children"], key=lambda x: (x["language"], x["language_child_id"])),
            "owners": sorted(by_common[cid]["owners"], key=lambda x: x["knowledge_owner_id"]),
            "coverage": sorted(by_common[cid]["coverage"], key=lambda x: x["language"]),
            "countertests": sorted(by_common[cid]["countertests"], key=lambda x: x["language"]),
        })

    routing_by_id = {row["semantic_family_id"]: row for row in routing}
    family_items = []
    for row in baseline:
        route = routing_by_id[row["semantic_family_id"]]
        family_items.append({
            "semantic_family_id": row["semantic_family_id"],
            "semantic_family_label": row["semantic_family_label"],
            "primary_lane": row["primary_lane"], "level_floor": row["level_floor"],
            "routing_disposition": route["routing_disposition"],
            "routing_rationale": route["routing_rationale"],
            "knowledge_owner_ids": route["knowledge_owner_ids"],
            "common_decision_id": route["common_decision_id"],
            "non_admission_code": route["non_admission_code"],
            "source_labels": split(row["source_labels"]),
            "learner_decisions": split(row["learner_decisions"]),
            "source_observation_ids": split(row["source_observation_ids"]),
            "example_lines": split(row["example_lines"]),
            "example_thai": split(row["example_thai"]),
            "example_english": split(row["example_english"]),
            "member_family_ids": split(row["member_family_ids"]),
            "review_status": row["review_status"],
        })

    blockers = []
    blocker_by_id = {row["countertest_evidence_id"]: row for row in blocker_rows}
    for row in countertests:
        blockers.append({**row, "blocker": blocker_by_id.get(row["countertest_evidence_id"], {})})

    relationship_counts = Counter(row["reconciliation_relationship"] for row in source_dispositions)
    routing_counts = Counter(row["routing_disposition"] for row in routing)
    terminal_family_ids = {row["normalized_family_id"] for row in source_dispositions}
    observation_ids = {oid for row in source_dispositions for oid in row["source_observation_ids"].split(";")}
    assert len(source_dispositions) == 831 and len(terminal_family_ids) == 831
    assert len(observation_ids) == 1669
    assert len(family_items) == 657 and len({x["semantic_family_id"] for x in family_items}) == 657
    assert len(projections) == 309 and len(common_items) == 7
    assert routing_counts == Counter({"defer": 648, "owner_created": 8, "split_required": 1})
    assert relationship_counts == Counter({"owner": 626, "contrast": 31, "variant": 162, "umbrella": 10, "invalid": 2})
    assert len(blockers) == 87
    assert {x["language"] for x in adaptations} == {"th", "en", "ko", "zh-TW"}

    architecture_findings = [
        {"status":"NEEDS_FIXES","finding":"Claude architecture review remains NEEDS_FIXES","impact":"The cross-language architecture is not accepted; this UI is evidence navigation only.","evidence_ref":"ZH_TW_EXPANSION_ARCHITECTURE_REVIEW.md"},
        {"status":"BLOCKING","finding":"Self-test canaries are tautological","impact":"22/22 named canaries do not exercise true validator mutation paths; real mutation-path coverage is zero.","evidence_ref":"scripts/validate_cross_language_trial.py --self-test"},
        {"status":"NEEDS_FIXES","finding":"28 adaptations retain template-generated decision prose","impact":"Language adaptation text is candidate scaffolding, not independently reviewed linguistic analysis.","evidence_ref":"language_adaptations.v1.tsv"},
        {"status":"DEFER","finding":"648 TH semantic families are untyped defer","impact":"They have no reviewed common/child/lane classification and cannot be treated as curriculum gaps already resolved.","evidence_ref":"th_knowledge_owner_routing_dispositions.v1.tsv"},
        {"status":"NEEDS_FIXES","finding":"119-row A1 deferred grammar parent batch failed review","impact":"Template boundaries, Thai surface leakage, overmerges, and missing countertest evidence block parent materialization.","evidence_ref":"TH_A1_DEFERRED_GRAMMAR_PARENT_CANDIDATE_REVIEW.md"},
        {"status":"PENDING","finding":"Owner and domain repair has not received a fresh semantic recheck","impact":"Mechanical full-stage PASS is not owner/domain adequacy approval.","evidence_ref":"FULL_STAGE_TRIAL_READBACK.md"},
        {"status":"BLOCKED","finding":"87 countertest rows are blocker records, not linguistic evidence","impact":"All are reviewed_na/defer; cross-language naturalness and applicability remain unresolved.","evidence_ref":"COUNTERTEST_EVIDENCE_BLOCKER_READBACK.md"},
    ]

    payload = {
        "schema_version": "cross_language_reference_ui.v1",
        "status": {"review_status": "needs_review", "native_status": "native_pending", "product_readiness": False},
        "summary": {
            "source_observations": len(observation_ids), "normalized_families": len(terminal_family_ids), "semantic_families": 657,
            "common_decisions": 7, "canonical_targets": 309,
            "routing": dict(sorted(routing_counts.items())),
            "relationships": dict(sorted(relationship_counts.items())),
            "lane_counts": dict(sorted(Counter(x["primary_lane"] for x in family_items).items())),
            "level_counts": dict(sorted(Counter(x["level_floor"] for x in family_items).items())),
            "countertest_blockers": len(blockers),
        },
        "common_decisions": common_items,
        "families": family_items,
        "source_terminals": sorted(source_dispositions, key=lambda x: x["normalized_family_id"]),
        "canonical_projection": sorted(projections, key=lambda x: x["canonical_target_id"]),
        "countertest_blockers": sorted(blockers, key=lambda x: x["countertest_evidence_id"]),
        "architecture_findings": architecture_findings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS output={args.output} families=657 common=7 targets=309 blockers={len(blockers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
