# CLAUDE.md — Anki deck repo

Personal Japanese-study Anki decks, edited programmatically and re-imported into
Anki (AnkiMobile iOS is the primary platform) via import-merge. Zach studies at
~N4 / Genki L23 level. See README.md for the user-facing feature overview.

## What's here

- `GENKI II Vocab.apkg` — 589 notes, GENKI II lessons 13–23
- `JLPT N4.apkg` — 1150 notes
- `backups/` — local-only snapshots, gitignored. Before modifying a deck, copy
  the current `.apkg` into `backups/` with a date suffix.
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
  (`k-brk`, `k-head`, `k-link`, …) when adding entries.

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

1. Back up the current `.apkg` into `backups/`.
2. Unzip, edit `collection.anki21`, regenerate media as needed.
3. Rezip; verify before delivering: note count and guids unchanged, every
   `[sound:]` / `src="…"` reference resolves to a media entry, example audio
   untouched unless intentionally changed.
4. Write the new `.apkg` back here, update README.md if features changed,
   git commit with a conventional message (`fix:`/`feat:`/`docs:`) — but only
   commit when Zach asks; he also works on this repo from another computer.
5. Zach then imports the `.apkg` in Anki (merge by guid) and runs Check Media
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
