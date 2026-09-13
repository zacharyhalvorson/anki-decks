# Anki Decks

Personal Japanese-learning decks for Anki (desktop, AnkiMobile iOS, AnkiWeb).

## What's here

| File | Notes | Cards | Level |
|---|---|---|---|
| `GENKI I Vocab.apkg` | 66 | 132 | GENKI 1 (beginner; L1 so far) |
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

Every note with kanji has a "Kanji breakdown" card on the back, built from KANJIDIC2. It is always visible, styled like the example-sentence card with a green left border (Nihongo green, to match the app the links open), and lists every kanji in the word in one card separated by hairlines. Each kanji entry shows:

- A dotted grid box with the kanji drawn from [KanjiVG](https://kanjivg.tagaini.net) stroke data (handwritten-style, the same source the Nihongo app uses). Tap the box or its play badge to replay the stroke order Nihongo-style: a grey ghost of the character, strokes inked in order, and a green cursor riding the pen tip. Kanji arrive fully drawn when the card flips.
- On'yomi (音読み) in katakana and kun'yomi (訓読み) in hiragana with okurigana in parens, beside the box
- A green 語 link to the kanji's Nihongo page, the stroke count (画) and the JLPT level (omitted when the kanji has none), stacked at the right
- English meanings below

(Radical and component decomposition are still stored in the field but no longer shown; the layout is applied by the template script, so the field markup is unchanged.)

### Nihongo iOS app deep links

Tappable links open the [Nihongo](https://apps.apple.com/us/app/japanese-dictionary-nihongo/id881697245) iOS dictionary app to the exact entry:

- Tap the green 語 on a kanji entry → `nihongo-app.com/dictionary/kanji/<char>` (kanji detail page)
- Tap the grey 語 in the part-of-speech row → `.../word/<word>` (full word entry)

Links are universal links, so if Nihongo isn't installed they fall through to the mobile web page with an install prompt. On Android or desktop Anki they open the same web page in a browser.

### Audio

- Every word has an audio recording (`{{WordAudio}}`), rendered as a hidden player. Tap anywhere on the word / furigana / meaning block to play it.
- Every example sentence has audio (`{{ExampleAudio}}`), triggered by tapping anywhere on the example card.
- Audio taps never trigger Anki's tap-to-advance gestures.
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

- **Recognition** (Japanese → English): front shows the word in Japanese; back shows the same word with its reading as furigana above it, the English meaning, a part-of-speech row, the example sentence, and the kanji breakdown.
- **Production** (English → Japanese): front shows the English gloss; back adds the Japanese word (with furigana), part of speech, example, and kanji breakdown.

Template sources live in `templates/` (`card.css`, `recognition_back.html`, `production_back.html`, `runtime.js`) and the stroke-data asset in `assets/_kanji_strokes.js` (KanjiVG paths for every kanji that appears in the decks, embedded in each `.apkg` as a `_`-prefixed media file). `python3 scripts/apply_templates.py <tag>` backs up every deck and re-applies the templates and asset — see `CLAUDE.md` for the invariants it respects. Fronts are untouched by that script.

## Compatibility

- macOS / Windows / Linux desktop Anki: full support
- AnkiMobile iOS: full support (recommended platform, this is what the templates are optimized for)
- AnkiDroid: works, but Nihongo deep links open the mobile web page since Nihongo is iOS-only
- AnkiWeb: works, no deep link handling

## Data sources

- Kanji data: [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) via [jamdict](https://github.com/neocl/jamdict)
- Stroke order: [KanjiVG](https://kanjivg.tagaini.net) (CC BY-SA 3.0, Ulrich Apel)
- Component decomposition: KRADFILE / RADKFILE (Jim Breen / EDRDG)
- Word POS classification: [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) via jamdict
- Word and example sentence audio: [gTTS](https://github.com/pndurette/gTTS) (Japanese voice)
- Deep link target: [Nihongo](https://nihongo-app.com) by Serpenti Sei LLC

## Notes

- Decks are for personal study. Content includes editable JMdict / KANJIDIC data (public domain / CC).
- `backups/` directory is local-only (gitignored); do not commit backup snapshots.
- `.apkg` files are binary (SQLite + zip); `git diff` won't show meaningful changes.
