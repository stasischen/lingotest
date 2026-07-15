import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_payload() -> dict[str, object]:
    text = (ROOT / "sentence-explorer/th-vocab-data.js").read_text(encoding="utf-8")
    prefix = "window.TH_VOCAB_TAXONOMY = "
    assert text.startswith(prefix) and text.endswith(";\n")
    return json.loads(text[len(prefix) : -2])


def test_payload_counts_and_gates() -> None:
    payload = load_payload()
    assert payload["summary"] == {
        "total_words": 5000,
        "categorized_words": 2353,
        "unclassified_words": 2647,
        "pending_words": 2647,
        "taxonomy_pending_words": 2624,
        "reviewed_unmapped_words": 23,
        "primary_memberships": 2704,
        "big_categories": 10,
        "small_categories": 159,
        "used_small_categories": 154,
        "zh_tw_i18n": 5000,
        "missing_zh_tw_i18n": 0,
        "reviewed_zh_tw_i18n": 733,
        "candidate_zh_tw_i18n": 4267,
    }
    assert len(payload["words"]) == 5000
    assert len({word["id"] for word in payload["words"]}) == 5000
    assert all(word["review_status"] == "needs_review" for word in payload["words"])
    assert all(word["native_status"] == "native_pending" for word in payload["words"])
    assert not any(word["production_promotion_allowed"] for word in payload["words"])
    assert all(word["zh_tw"].strip() for word in payload["words"])
    assert sum(bool(word["source_translation_en"]) for word in payload["words"]) == 4267


def test_category_memberships_are_bound_to_scope() -> None:
    payload = load_payload()
    small_ids = {row["id"] for row in payload["small_categories"]}
    assert len(payload["big_categories"]) == 10
    assert sum(row["small_category_count"] for row in payload["big_categories"]) == 159
    assert sum(row["primary_memberships"] for row in payload["big_categories"]) == 2704
    assert all(set(word["primary_category_ids"]) <= small_ids for word in payload["words"])
    assert all(set(word["secondary_category_ids"]) <= small_ids for word in payload["words"])


def test_shared_navigation_links_to_thai_vocabulary_viewer() -> None:
    navigation = (ROOT / "sentence-explorer/mobile-nav.js").read_text(encoding="utf-8")
    assert '["th-vocab.html", "Thai Vocab 5K"]' in navigation
