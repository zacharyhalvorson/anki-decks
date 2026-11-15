# Deck guide

[Download the decks](../README.md)


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
- Every note has two example sentences (the second shows the word with the words it normally goes with, at the grammar level of its source lesson). Each sentence is its own row in the example card and has its own audio: tap anywhere on a row to play it.
- Every on'yomi and kun'yomi in the kanji breakdown is tappable (dotted underline) and plays that reading.
- Audio taps never trigger Anki's tap-to-advance gestures.

### Taps never answer a card

On AnkiMobile a tap on the question shows the answer, and on the answer side a tap on the left or right answers the card and moves to the next one. These decks keep the first and switch off the second: tapping the question still flips the card, but once the answer is showing, a tap anywhere on the card area, including the empty space around a short card, does nothing unless it lands on something made to be tapped (audio, stroke order, readings, the 語 links). The only way to rate a card and move on is the buttons under the card. Scrolling and swipes are unchanged, and other note types in the same collection keep their normal tap behaviour.
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

- **Recognition** (Japanese → English): front shows the word in Japanese; back shows the same word with its reading as furigana above the kanji (aligned per kanji run, e.g. お願[ねが]いします), the English meaning, a part-of-speech row, the two example sentences, and the kanji breakdown.
- **Production** (image or English → Japanese): 235 reviewed concrete-vocabulary cards show an image-only prompt. Other cards keep the English gloss. Image answers shrink to the normal compact banner and show the Japanese word, reading, English meaning, both example sentences, and kanji breakdown. Word audio uses Anki’s normal automatic answer playback; tapping the word replays it. Existing card identities and schedules are preserved; no third card is added.

Template sources live in `templates/` (`card.css`, `recognition_front.html`, `production_front.html`, `recognition_back.html`, `production_back.html`, `runtime.js`, `tap_guard.js`) and the stroke-data asset in `assets/_kanji_strokes.js` (KanjiVG paths for every kanji that appears in the decks, embedded in each `.apkg` as a `_`-prefixed media file). `python3 scripts/apply_templates.py` re-applies the templates and asset — see `CLAUDE.md` for the invariants it respects. It writes all four templates (both fronts, both backs).

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
- Word, reading and example sentence audio: [gTTS](https://github.com/pndurette/gTTS) (Japanese voice); GENKI II example sentences use Microsoft `ja-JP-NanamiNeural`
- Deep link target: [Nihongo](https://nihongo-app.com) by Serpenti Sei LLC

## Notes

- Decks are for personal study. Content includes editable JMdict / KANJIDIC data (public domain / CC).
- `.apkg` files are binary (SQLite + zip); `git diff` won't show meaningful changes.

## Card illustrations

`assets/card-visuals/manifest.json` maps exact word/readings to reusable transparent artwork. Shared meanings can explicitly reuse an image; spelling or grammatical reading variants are listed separately so coverage is reviewable. `coverage.json` inventories the vocabulary and marks completed entries. The reviewed catalog covers 1,883 word/readings with 1,822 distinct general illustrations, plus 11 exact-sense overrides. Matching spellings and grammatical variants explicitly reuse artwork. GENKI I has 596 illustrated notes and 64 deliberately text-only notes; its [complete review list](../assets/genki1/text-only-notes.md) explains those choices.

Run `python3 scripts/apply_templates.py` to apply the catalog and shared templates to all five deck exports. It keeps note identities, scheduling, audio, fields, and original media intact, and verifies the output before replacing each package. Importing the packages into Anki is a separate step.

`templates/visuals.css`, `visuals.js`, and `visual_front.js` implement the image slide/fade/scale, moving answer block, word resizing, Production cue color change, outgoing hint movement/fade, late-image fade, and reduced-motion behavior. Front-side geometry is captured when the client retains its WebView; other clients use a calculated fallback. Actual AnkiMobile transition verification remains outstanding.

The feedback preview remains under `experiments/card-visuals/`; canonical artwork and motion now live under `assets/` and `templates/`. The interactive preview selects up to 40 catalog entries present in GENKI II, and its gallery includes all illustrated GENKI II words.

## Image-first production selection

`assets/card-visuals/image-production.json` is the reviewed allowlist: 134 exact word/reading/meaning entries, producing 235 cards across the decks. GENKI I has 44, GENKI II 37, JLPT N4 89, JLPT N5 63, and Quartet I 2. Eligibility depends on the exact sense and reviewed artwork; abstract concepts, social roles, and pictures with unclear targets retain English prompts.

Eligibility also requires the reviewed artwork hash to match. Changing selected artwork requires reviewing it again. `templates/image_production.js` handles the prompt and compact reveal; existing Recognition and nonselected Production behavior remains. `python3 scripts/test_image_production.py` verifies packaged eligibility, media, audio placement, and the unchanged two-card schema. The apply script additionally checks existing card rows and scheduling, note identity, full answer content, media integrity, and package CRCs.

Import the updated `.apkg` files into your existing collection normally, then sync. No fields or card types were added, so note-type merging is not required for this change. The files have been rebuilt and browser-checked; native AnkiMobile transition behavior still needs device verification.

To inspect actual packaged templates locally, run `python3 experiments/image-production/build_packaged.py` and serve `experiments/image-production/`; open `packaged.html`. The original motion study remains at `index.html`.

## Working with a local clone

Install Git LFS and run `git lfs install` before cloning the repository. In an existing clone, run `git lfs pull` to download the deck packages and illustration sources. The [deck download table](../README.md) also provides each complete package individually.
