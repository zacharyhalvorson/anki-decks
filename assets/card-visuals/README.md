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
