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
