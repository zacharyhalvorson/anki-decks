# CLAUDE.md — Anki deck repo

Personal Japanese-study Anki decks, edited programmatically and re-imported into
Anki (AnkiMobile iOS is the primary platform) via import-merge. Zach studies at
~N4 / Genki L23 level. See README.md for the user-facing feature overview.

## What's here

- `GENKI I Vocab.apkg` — 66 notes (L1 so far; tags `genki-01` + part of speech)
- `GENKI II Vocab.apkg` — 589 notes, GENKI II lessons 13–23
- `JLPT N4.apkg` — 1150 notes
- `JLPT N5.apkg` — 751 notes (built Sep 2026; see "JLPT N5 deck" below)
- `Quartet I Vocab.apkg` — 175 notes (L1–L2 so far; tags `lesson-1`, `lesson-2`)
- `templates/`, `assets/`, `scripts/` — template sources, stroke-data asset and the
  apply script (see the stroke-order pass below)
- No backup snapshots — every deck version is in git history (`git show
  <rev>:"JLPT N4.apkg" > old.apkg` to recover one).
- `.apkg` files are binary (zip); `git diff` is meaningless on them.

## .apkg format (legacy packaging — keep it)

Each `.apkg` is a zip containing:

- `collection.anki21` — the real SQLite DB (589 / 1150 notes). Edit this one.
- `collection.anki2` — 1-note "please update Anki" stub. Copy through unchanged.
- `meta` — copy through unchanged.
- `media` — JSON map of zip member name → filename (`{"0": "n4_wd_….mp3", …}`).
  Media files themselves are stored under numeric member names (`0`, `1`, …).

Rebuild by rezipping the same structure (mp3s can be STORED, rest DEFLATED).

## Note model (same in both decks)

`Vocab+Furigana+Audio`, fields in order (0-indexed, `\x1f`-separated in `notes.flds`):

0 Word · 1 Reading · 2 Meaning · 3 PartOfSpeech · 4 ExampleJA ·
5 FuriganaExample · 6 ExampleEN · 7 KanjiBreakdown · 8 WordAudio · 9 ExampleAudio

- WordAudio format: `[sound:<deck>_wd_<16hex>.mp3]` (deck prefix `genki2` / `n4`)
- ExampleAudio format: `<audio src="…mp3" preload="none"></audio>`
- Two templates per note: Recognition (JA→EN) and Production (EN→JA). Audio is
  played by tap targets in the templates — don't change the field HTML shapes.
- KanjiBreakdown HTML comes from KANJIDIC2/JMdict via jamdict, with Nihongo app
  deep links (`nihongo-app.com/dictionary/...`). Follow existing markup classes
  when adding entries. Since Aug 2026 restyle: each `k-brk` has a `k-head`
  (kanji link + `k-stats` stat columns: `k-stat` > `k-stat-v`/`k-stat-l` for
  strokes and JLPT — no `k-meta` span, no grade), a `k-mean` line with NO
  "Meanings:" prefix, and `k-radical`/`k-components` labels wrapped in
  `<span class="k-label">`. Kanji entries are separated by CSS rules
  (`.k-brk + .k-brk` border-top), not boxes; tap affordance is dotted
  underlines. Match this shape for any new entry.
- Template wrapper (Sep 2026): the breakdown is rendered inside
  `<div class="kanji-breakdown"><div class="kb-content">…</div></div>` — a plain
  always-open div, no `<details>`/`<summary>`, `.example`-style card with a
  Nihongo-green left border.
- **Stroke-order pass (Sep 13 2026)** — presentation now comes from the
  template, not the field. Sources are tracked in `templates/` and applied with
  `python3 scripts/apply_templates.py` (patches all four decks,
  verifies guids/media, replaces in place). Do NOT hand-edit the CSS/templates
  inside an `.apkg`; edit `templates/` and re-run the script.
  - `templates/runtime.js` (inlined into both back templates) re-lays out each
    `.k-brk` at render time into `.k-head2` (`.k-box` grid box + `.k-readings`
    with `.k-reading2` On/Kun rows and a floated `.k-stats2` column: green `語`
    kanji deep link, `N画` stroke count, JLPT level only if present) and
    `.k-mean2`; radical/components are dropped from view. It adds `kb-v2` on
    `.kanji-breakdown` when done, so the `.kb-v2` CSS only applies after the
    script has run and the old `.k-brk` CSS remains as a no-JS fallback. The
    field markup shape is therefore UNCHANGED — keep generating entries exactly
    as before (`k-head` > `k-link` > `k-char`, `k-stats` with `k-stat-v`/
    `k-stat-l` labelled "Strokes"/"JLPT", `k-mean`, `k-reading` On/Kun with
    `k-label` + `k-r` spans, `k-radical`, `k-components`).
  - Stroke data: `assets/_kanji_strokes.js` sets `window.KANJI_STROKES`
    (kanji → KanjiVG path list, viewBox 0 0 109 109) for every kanji in the
    four decks (857). It is embedded in each `.apkg` as a `_`-prefixed media
    file and loaded by `<script src="_kanji_strokes.js">` at the top of the back
    templates. Adding notes with a kanji not in the map just shows the plain
    glyph in the box (`.k-fallback`); to extend, fetch
    `raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/<5-hex codepoint>.svg`,
    take the `<path d>` values in stroke order, add them to the map, re-run the
    apply script. Animation: ghost `#bdbdbd`, ink `#1f1f1f`, cursor `#49c248`
    (sampled from Nihongo), 90 ms + 4.6 ms/unit per stroke, 70 ms gap.
  - Back templates: Recognition = `word-block` (`.front-word-ruby` word with
    furigana + `.meaning`; the whole block taps to click the hidden WordAudio
    button; no furigana when the word has no kanji or reading == word) → `.wordinfo` (POS text + grey `語` word deep link;
    gradient rises behind the meaning) → `.example` (whole card taps to play
    the sentence `<audio>`) → breakdown. Production = `front-english` on top,
    then the same blocks (card gets class `prod`). Fronts unchanged. Every audio
    / play tap calls `stopPropagation` on click + touchend so it never reaches
    Anki's tap gestures. The old `.reading` line and `.pos-tag` pill are gone
    from the templates (CSS kept).
  - Furigana over the word: no `<ruby>`. The template emits
    `<span class="fw-base">{{Word}}</span><span class="fw-read">{{Reading}}</span>`
    and `runtime.js` rewrites it into `.fk` spans (kanji run + absolutely
    positioned `.fr` kana centred above it). The word is split into kanji/kana
    runs, kana runs are matched literally against the (hiragana-normalised)
    Reading, and each kanji run gets the kana in between — お願いします →
    お願[ねが]いします. Readings with okurigana parens / `a/b` alternates / `〜`
    are normalised first; if no match, the whole reading sits over the whole
    word. `.front-word-ruby` keeps the front word's exact box (margin
    24px/-10px, line-height 1.6) so the word does not move on flip; the
    furigana hangs in the top margin out of flow.
  - `@media (max-width: 480px)`: `body` side margins 0 and `.card` padding
    `14px 12px 24px`, so on iPhone the side margin equals the 12px gap between
    sections; wider screens keep max-width 600 + 20px padding.

## Invariants for import-merge (do not break)

- NEVER change note `guid`s or the model/deck IDs — Anki merges by guid and
  preserves the review scheduling on Zach's devices.
- For every note you modify: set `mod` = current epoch seconds and `usn = -1`,
  or the merge will not pick up the change. Also bump `col.mod` (milliseconds).
- Media filenames must be ASCII-safe hashes (iOS media resolution breaks on
  non-ASCII names). When replacing a media file, give it a NEW name and update
  the field reference — same-name replacement is unreliable on import.
- When rebuilding, drop media files no longer referenced by any field (keep
  `_`-prefixed files, which are template assets). Old audio left in the zip
  bloats every import.

## Audio conventions (as of Aug 2026)

- ALL audio — word and example sentence — is gTTS Japanese (`gTTS(text, lang="ja")`),
  one consistent voice. Do not use macOS `say`/Kyoko or other TTS (a Kyoko pass
  happened once only because a proxy blocked gTTS; it has been fully replaced).
- Word audio is generated from the **Reading** field (kana), not the kanji Word
  field, normalized first: strip `〜`/`～`, drop parenthesized parts
  (`しあわせ(な)` → `しあわせ`), turn `/`-separated alternate readings into a
  pause (`し/よん` → `し、よん`), strip whitespace. Fall back to Word if empty.
- Example audio is generated from ExampleJA (plain sentence, no furigana markup).
- Filenames: `<deck>_wd_<md5("gtts-ja:"+text)[:16]>.mp3` — deterministic, so
  identical texts dedupe and reruns are idempotent.
- Rate-limit gTTS: ~0.25 s between calls, retry with backoff; sanity-check each
  file is > 500 bytes and starts with an ID3/MPEG header.
- gTTS may be blocked from some machines (proxy). The Claude cloud container
  can reach it; generate there if the local machine can't.

## Workflow

1. Unzip, edit `collection.anki21`, regenerate media as needed.
2. Rezip; verify before delivering: note count and guids unchanged, every
   `[sound:]` / `src="…"` reference resolves to a media entry, example audio
   untouched unless intentionally changed.
3. Write the new `.apkg` back here, update README.md if features changed,
   git commit with a conventional message (`fix:`/`feat:`/`docs:`) — but only
   commit when Zach asks; he also works on this repo from another computer.
4. Zach then imports the `.apkg` in Anki (merge by guid) and runs Check Media
   to purge superseded audio.

## Cowork/cloud session notes

- The device→cloud write cap is 20 MB per file: an `.apkg` over that must be
  split into <20 MB chunks, committed, then `cat` together on-device and
  md5-verified (chunks named `*.tmp` are gitignored; stash leftovers in
  `_to_delete/`).
- File deletion is blocked in device shells — `mv` cruft into `_to_delete/`
  instead. A failed git op can leave `.git/index.lock`; move it to
  `_to_delete/` too.

## Content preferences

- Furigana in study material only on first occurrence of harder words; common
  N4-level words need none.
- Example sentences should stay at Genki-level grammar (class is at L23).
- Per-deck override for Quartet decks: example sentences match the source
  book's lesson level (Quartet I is early-intermediate, roughly N3-adjacent),
  not Genki L23. Use patterns like 〜ば / 〜ように / 〜ために / 〜そう /
  〜ばかり / 〜ながら / 〜のに / 〜ても / 〜わけ / 〜たびに / 〜ところ where
  they fit, and don't shy away from compound sentences. Base kanji usage
  matches Quartet's assumed reader (little furigana in ExampleJA), but
  FuriganaExample still supplies furigana for kanji outside Genki 1-2 so a
  beginner could still parse it. Same rule for future Quartet lessons.
- Quartet vocab source: the textbook's 単語リスト appendix (Quartet I 1st ed. PDF
  pages 290–293 = L1, 294–297 = L2, four pages per lesson; book page = PDF page − 26;
  the PDF is a scan with no text layer, so render pages and read/OCR them).
  The deck takes the 読み物1 + 読み物2 lists, skipping proper nouns (names, titles)
  and bare grammar patterns; (お)-words are stored with the お (お花見/お弁当/お酒).
  Meanings lead with the textbook gloss. L2 added Sep 2026 (83 notes; POS labels
  added for it: Conjunction, Suffix, Counter, の-Adjective). New kanji get
  breakdowns from KANJIDIC2/KRADFILE (JLPT shown as "N"+old KANJIDIC level, same
  as jamdict) and strokes from KanjiVG, appended to `assets/_kanji_strokes.js`,
  then `scripts/apply_templates.py` embeds the asset in every deck.

## Tag conventions

- GENKI decks: one lesson tag per note, `genki-NN` zero-padded to two digits
  (`genki-01` … `genki-12` in GENKI I, `genki-13` … `genki-23` in GENKI II), plus a
  lowercase part-of-speech tag (`noun`, `u-verb`, `ru-verb`, `irregular-verb`,
  `i-adjective`, `na-adjective`, `adverb-expression`, `counter`, `number`, `suffix`).
  GENKI I used `lesson-1` until Sep 19 2026 — that collided with Quartet's `lesson-N`
  tags inside one Anki collection, so new GENKI I lessons must use `genki-NN`.
- Quartet: `lesson-N`. JLPT decks: `JLPT-N4` / `JLPT-N5` + POS + topic tags.

## JLPT N5 deck (Sep 19 2026)

- Source list: the 718-entry community N5 list (tanos.co.uk-derived, via
  `jamsinclair/open-anki-jlpt-decks` `src/n5.csv`, MIT). There is no official list —
  this is the old Level-4 test spec that every N5 resource uses. 有る/在る, 掛ける/かける
  and the two 九 rows were merged (715 notes), archaic kanji spellings were modernised
  (綺麗→きれい, 沢山→たくさん, 眼鏡→めがね, 醤油→しょうゆ, 鞄→かばん …), plus 36
  everyday words the list omits (greetings, months, 彼/彼女/僕, 日本/日本語 …) tagged
  `supplement`.
- ~540 notes reuse the wording of the `JLPT-N5`-tagged notes in `JLPT N4.apkg`, but
  every FuriganaExample was regenerated (every kanji run gets furigana) and checked
  against a morphological analyser; duplicate example sentences were rewritten. The
  N5 notes have their OWN guids (`md5("jlptn5:"+word+":"+reading)[:10]`), model
  `Vocab+Furigana+Audio (JLPT N5)` id 1800000000005, deck id 1800000000006, so the
  same word can exist in both JLPT decks.
- Audio: gTTS for words (from the kana reading) and sentences. Sentences were
  verified with whisper forced to kana output; the ones gTTS misread from kanji
  (時々, 二十歳, 角, 開きました, 木の下, 花瓶, 歌を, 私=わたくし, 十分 …) were
  synthesised from kana / digits instead, so the filename hash is of the text that
  was actually synthesised, not always of ExampleJA.
- New-card order is topical (greetings → pronouns → numbers/counters → time →
  family → daily life → …), not gojūon order.

## Audio reality check (Sep 19 2026 audit)

- GENKI II: word clips are gTTS (`genki2_wd_*`), but the ~586 example-sentence clips
  are still the original edge-tts `ja-JP-NanamiNeural` −10% clips
  (`genki2-<md5(voice+"|"+text)[:24]>.mp3`), NOT gTTS as the section above says.
  edge-tts cannot be reached from the cloud container (the proxy blocks WebSockets)
  but works from the on-device shell (`pip install --user edge-tts`).
- Verifying audio: whisper `small` via faster-whisper with a hiragana
  `initial_prompt` and kanji/digit tokens suppressed gives kana transcripts that can
  be diffed against the card reading; normal whisper output hides misreadings
  behind kanji.
