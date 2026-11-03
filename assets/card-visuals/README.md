# Reviewed card illustrations

The catalog contains 1,763 exact word/reading entries and 1,754 distinct illustrations. Images were generated and visually reviewed for their intended vocabulary sense and transparent appearance on a dark card. Nine entries share artwork for matching meanings. The 37 intentionally text-only grammatical entries are recorded in `coverage.json`.

- `manifest.json`: accepted artwork, accessible descriptions, and matching rationale.
- `images/`: source PNG artwork, including earlier revisions retained for provenance.
- `coverage.json`: full vocabulary inventory and illustration decisions.
- `generation-queue.json` and `generation-prompts.json`: generation jobs and provenance.
- `review/`: generation checkpoints and review/correction records.
- `optimized/`: rebuildable transparent WebP cache; ignored by Git.

Run `python3 scripts/apply_templates.py` from the repo root to package the catalog and shared transitions into the five canonical exports. This requires Python and `cwebp`. Review utilities additionally use Pillow. The build preserves note identities, scheduling, schema, audio, original media and kanji markup, and checks each output before replacing it.

Images are packaged at 1,200px wide as WebP and displayed at no more than 480 CSS pixels. Original PNGs are retained. Content-hashed filenames avoid stale media when importing updated decks. No external image service is required for studying the exported decks.

Run `python3 scripts/visual_coverage.py` to compare catalog coverage with actual packaged illustrations. The browser preview and its checks are documented in `../../experiments/card-visuals/README.md`.

## N4 semantic review — November 3, 2026

Reviewed all 1,150 N4 entries (1,137 illustrated and 13 intentionally text-only) using labeled contact sheets. Eight illustrations were corrected, with seven newly generated images and one reused arrival scene. See `review/n4-2026-11-03/corrections.html` for before/after comparisons and `audit.json` for per-entry decisions.

`sense-overrides.json` takes precedence over the legacy catalog using an exact `(Word, Reading, Meaning)` match. This keeps homographs such as つく (arrive versus turn on) and する (do versus decide on) separate. If a meaning field changes, review its override too; unmatched meanings fall back to the legacy catalog. The new sources retain their transparent PNGs and receive content-hashed WebP names during packaging. This pass rebuilds only `JLPT N4.apkg`; other exports are unchanged. Run `python3 Anki/scripts/test_visual_senses.py` to check sense separation.

The arrival note was subsequently corrected from つく to 着く. Both sense keys are retained in the override file so rebuilding an older export cannot restore the lamp image.
