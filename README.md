# Thai A1 Theme Viewer Report

Public, read-only review build for the Thai A1 source-theme package. It uses the
existing production lesson surface and includes Thai TTS controls for both each
sentence and each manually reviewed atom row.

- 18 canonical themes / 90 content items / 481 source rows
- Separate blocked reference section: 59 non-theme items, marked DO NOT USE.
- All 481 viewer rows now have manual segmentation; the viewer shows no
  `segmentation pending` rows.
- The blocked section is retained only for taxonomy/reference review; its
  content was previously found problematic and is not accepted learner content.
- This is a review report, not a release package: native status remains
  `native_pending` and production promotion remains disabled.
- Source viewer build: `lingo-frontend-web-th-a1-debug`, commit `f2c6b1fa`

Open the deployed report at the GitHub Pages URL published for this repository.

## Thai Sentence Atlas

`sentences.html` is a separate, read-only explorer for the complete Gemini Thai
sentence reference corpus. It presents one chapter at a time, with a
corpus-inferred guide to that chapter's topics, reusable sentence patterns,
grammar, and communicative functions. Book/Chapter selectors and bottom
Previous/Next controls move through all 70 chapters; search is scoped to the
current chapter. Every sentence retains source-line lineage, copy controls, and
browser Thai TTS. The corpus and chapter guides are reference material only and
are not presented as native-reviewed, CEFR-approved, learner-ready, or
production content.

Rebuild its static data from the source Markdown with:

```powershell
python tools/build_sentence_data.py `
  D:\Githubs\lingo\content-th\docs\gemini\sentences.md `
  sentence-explorer\sentences-data.js
```

The browser-ready chapter guide is generated from the reviewed JSON segments:

```powershell
python tools/build_chapter_notes.py <reviewed-json-files...> `
  --output sentence-explorer\chapter-notes.js
```

`grammar.html` projects every chapter-level sentence-pattern and grammar
observation into a searchable master index. Each entry expands its source-line
evidence into the matching Thai and English sentence rows. The grouped view is
label-normalized navigation only and does not claim canonical deduplication.

## zh-TW A1 Curriculum

`zh-a1-curriculum.html` is the user-review-ready explorer for the first complete
Taiwan Traditional Chinese A1 curriculum draft. It presents 123 independent
learner-facing units under 12 themes, plus the post-content mapping for all 101
teaching targets and 117 richness rows. Evidence quotes link back to content
units; 26 rows remain visibly marked as genuine gaps rather than being padded
with unnatural content. Native status remains `native_pending` and production
promotion remains disabled.

Rebuild the browser payload from the committed `content-zh` review package with:

```powershell
python tools\build_zh_a1_curriculum_data.py `
  D:\Githubs\lingo\content-zh\content\review\zh_tw_a1_theme_curriculum_v1_20260715 `
  sentence-explorer\zh-a1-curriculum-data.js
```

## Thai A1 Curriculum

`th-a1-curriculum.html` presents the independently authored Thai A1 curriculum:
136 natural Thai source units, their per-unit Taiwan Traditional Chinese i18n,
and post-content evidence mapping for all 101 teaching targets and 117 richness
rows. All 218 denominator rows now have reviewed exact Thai evidence; the
explorer displays zero remaining genuine gaps while preserving the package state
as `needs_review`, `native_pending`, and `production=false`.

Rebuild the browser payload from the committed `content-th` review package with:

```powershell
python tools\build_th_a1_curriculum_data.py `
  D:\Githubs\lingo\content-th\content\review\th_a1_theme_curriculum_v1_20260715 `
  sentence-explorer\th-a1-curriculum-data.js
```

## Thai 5,000 Vocabulary Taxonomy

`th-vocab.html` is a read-only explorer for the current audited Thai taxonomy
projection. It shows all 5,000 candidates, the 10 parent domains and 159 small
categories, effective primary memberships, final sense routes for the bounded
739-row adjudication scope, and the 733 currently available zh-TW word i18n
rows. Pending classification and missing i18n remain visible. Nothing on this
surface changes `needs_review`, `native_pending`, or production promotion.

Rebuild its browser payload from the control-tower closeout artifacts with:

```powershell
python tools\build_th_vocab_taxonomy_data.py `
  D:\Githubs\lingo\release-aggregator\docs\tasks `
  sentence-explorer\th-vocab-data.js
```
