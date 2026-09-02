# Anki Decks

Personal Japanese-learning decks for Anki (desktop, AnkiMobile iOS, AnkiWeb).

## What's here

| File | Notes | Cards | Level |
|---|---|---|---|
| `GENKI II Vocab.apkg` | ~589 | ~1178 | GENKI 2 (intermediate) |
| `JLPT N4.apkg` | ~1150 | ~2300 | JLPT N4 |
| `Quartet I Vocab.apkg` | 92 | 184 | Quartet I (early-intermediate; L1 so far) |
| `Intermediate 5.apkg` | 120 | 240 | Class deck |
| `Intermediate 5 + 6.apkg` | ~240 | ~480 | Class deck (merged) |
| `Intermediate 6.apkg` | 121 | 242 | Class deck |

Every deck is self-contained. All media (audio, images) is bundled inside the `.apkg`. No extra setup, no external files to download.

## Install

### Desktop Anki (macOS / Windows / Linux)

1. Clone or download this repo
2. In Anki, `File → Import` and select any `.apkg`
3. Repeat per deck

If a deck already exists in your collection, Anki merges by note `guid` and your review scheduling is preserved.

### AnkiMobile (iPhone / iPad)

Two options:

1. Sync via AnkiWeb after importing on desktop. Simplest. Cards, media, and templates all sync.
2. Direct import: put the `.apkg` in Files on iOS, tap it, choose "Open in AnkiMobile".

### AnkiWeb

Import the `.apkg` on the AnkiWeb site. Media is included in the file, no extra upload needed.

## What's in the decks

### Kanji breakdowns

Every note with kanji has an expandable "Kanji breakdown" section built from KANJIDIC2. Each kanji entry shows a stat row (stroke count and JLPT level as value-over-label columns), then:

- English meanings
- On'yomi (音読み) in katakana
- Kun'yomi (訓読み) in hiragana with okurigana in parens
- Radical (with English name)
- Components (with English gloss for each)

### Nihongo iOS app deep links

Tappable links throughout the breakdown open the [Nihongo](https://apps.apple.com/us/app/japanese-dictionary-nihongo/id881697245) iOS dictionary app to the exact entry:

- Tap the big kanji character → `nihongo-app.com/dictionary/kanji/<char>` (kanji detail page)
- Tap the radical or a component → `.../kanji-element/<char>` (element page)
- Tap the part-of-speech pill (Ichidan Verb, い-Adjective, etc.) → `.../word/<word>` (full word entry)

Links are universal links, so if Nihongo isn't installed they fall through to the mobile web page with an install prompt. On Android or desktop Anki they open the same web page in a browser.

### Audio

- Every word has an audio recording (`{{WordAudio}}`), rendered as a hidden player triggered by tapping the reading.
- Every example sentence has audio (`{{ExampleAudio}}`), triggered by tapping the Japanese sentence line.
- Filenames are ASCII-safe hashes so iOS media resolution never breaks on non-ASCII characters.

### Verb classification

Verb POS labels are broken out by conjugation class using JMdict:

- Ichidan Verb (v1)
- Godan Verb (v5* subtypes)
- Suru Verb (vs / vs-i / vs-s)
- Kuru Verb (vk)
- Irregular Verb (vz / vn / vr)

### Card templates

Two card templates per note:

- **Recognition** (Japanese → English): front shows the word in Japanese, back shows reading + English + POS + example + kanji breakdown.
- **Production** (English → Japanese): front shows the English gloss + POS pill, back shows the Japanese word with audio.

## Compatibility

- macOS / Windows / Linux desktop Anki: full support
- AnkiMobile iOS: full support (recommended platform, this is what the templates are optimized for)
- AnkiDroid: works, but Nihongo deep links open the mobile web page since Nihongo is iOS-only
- AnkiWeb: works, no deep link handling

## Data sources

- Kanji data: [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) via [jamdict](https://github.com/neocl/jamdict)
- Component decomposition: KRADFILE / RADKFILE (Jim Breen / EDRDG)
- Word POS classification: [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) via jamdict
- Word and example sentence audio: [gTTS](https://github.com/pndurette/gTTS) (Japanese voice)
- Deep link target: [Nihongo](https://nihongo-app.com) by Serpenti Sei LLC

## Notes

- Decks are for personal study. Content includes editable JMdict / KANJIDIC data (public domain / CC).
- `backups/` directory is local-only (gitignored); do not commit backup snapshots.
- `.apkg` files are binary (SQLite + zip); `git diff` won't show meaningful changes.
