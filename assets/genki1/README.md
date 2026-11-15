# GENKI I build sources

The deck covers lessons 1–12 of GENKI I, third edition: 660 notes and 1,320 cards. The original 66 lesson-one notes keep their GUIDs and IDs, and all 132 original card rows remain unchanged. The ten-field note model and two card templates are unchanged. No live collection was imported or synced.

## Textbook and content

Vocabulary was checked against the local scanned `../GENKI /GENKI 1 (3rd Edition).pdf`, including the additional vocabulary and lesson-four location words. Printed vocabulary-page starts are L1 38, L2 58, L3 84, L4 104, L5 130, L6 148, L7 168, L8 188, L9 212, L10 232, L11 256, L12 274; each review spans three pages. Zero-based PDF index is printed page + 7. The textbook PDF and rendered pages are not copied into this repository.

`vocabulary.psv` has 600 source rows for lessons 2–12: lesson, word, reading, meaning, POS tag, first Japanese/English example, second Japanese/English example. Six repeated word/readings already exist in lesson one and reuse that earliest note; 594 notes are new. Each packaged note has exactly one lesson tag plus a POS tag.

| Lesson | Notes |
|---|---:|
| 01 | 66 |
| 02 | 48 |
| 03 | 56 |
| 04 | 62 |
| 05 | 52 |
| 06 | 47 |
| 07 | 52 |
| 08 | 55 |
| 09 | 55 |
| 10 | 55 |
| 11 | 60 |
| 12 | 52 |

Both examples are original study examples, checked for the lesson's grammar, with a distinct situation or typical collocation. Every kanji receives furigana. Five original lesson-one second sentences (学生, 工学, 政治, 看護師, 高校生) were simplified to avoid lesson-two negative grammar. `reading-review.json` preserves the exact furigana and kana synthesis inputs. Word clips use normalized Reading; sentence clips use the reviewed kana readings to avoid TTS misreadings. Audio is cached by the existing deterministic gTTS convention.

`baseline.json` records the original notes, card rows and schema identifiers for merge-safety verification. `new-kanji.json` records the 18 added KANJIDIC2 entries and KanjiVG/component provenance; the shared stroke asset now covers 901 characters. Fifteen additional shared on/kun clips are in `assets/kr/`.

## Illustration review

`visual-audit.json` records a decision for all 660 notes: 474 existing illustrations reviewed, 70 new scenes reviewed, 52 newly registered matching reuses (including two aliases of new scenes), and 64 deliberately text-only entries. There are 596 illustrated notes. Text-only reasons are explicit, including counters, grammatical attachments, discourse expressions and diagnoses that a generic illness image would not identify.

The new scenes include verbs, adjectives, expressions and occupations, as well as objects. The exact-sense overrides for 前 and 取る fix mismatched artwork. Answer-side mnemonic scenes retain English Production questions. Only スマホ, ピザ, トマト, ハンバーガー, すし and 新幹線 were newly approved as image-only cues; together with matching existing approved senses, GENKI I has 44 image-first Production cards.

All new artwork was generated with `image_gen` from the style in `AGENTS.md`, using the inspected chair and cat references. PNGs are saved in `assets/card-visuals/images/`; actual prompts, references and source/output provenance are in the shared `generation-prompts.json`. `generated-records.json` also retains unsuccessful/superseded attempts; `visual-decisions.json` pins reviewed SHA-256 hashes. Every accepted image was inspected at about 390 × 130 on white and charcoal. Two hazy scenes were edited and reviewed again. Review sheets are reproducible and ignored; `samples/` contains actual packaged card screenshots.

## Rebuild

Canonical exports live in `decks/`; run these commands from the repository root.

Use a Python environment with Pillow, fugashi, unidic-lite, gTTS, requests and pypdfium2; `cwebp` must be on PATH.

```sh
python scripts/build_genki1.py prepare
python scripts/build_genki1.py audio
python scripts/build_genki1.py readings
python scripts/build_genki1.py build
python scripts/build_genki1.py templates
python scripts/build_genki1.py check
python experiments/image-production/build_packaged.py
node scripts/preview_genki1.cjs
```

The normal shared `python scripts/apply_templates.py` works when source artwork is local. The GENKI `templates` wrapper supports offline iCloud placeholders by staging checksum-verified selected PNGs and reusing byte-identical, content-hash-verified WebPs already in packages. Its canonical apply script verifies every deck before atomic replacement. New PNGs always use the standard converter.

`audit_genki1_visuals.py` and `visual-scenes.psv` were planning inputs; the completed audit and hash-pinned decisions are the review record. `save_genki1_images.py` saves outputs and actual prompts; `finalize_genki1_visuals.py sheets` creates review sheets and `register` registers accepted decisions. Never infer acceptance from generation success alone.

`build-report.json` records content/identity/media checks; the shared `image-production-report.json` records final per-deck prompt eligibility. Browser previews verify rendering and media loading; native AnkiMobile behavior remains a device check.
