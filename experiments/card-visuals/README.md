# Card image preview

The approved illustration catalog lives in `../../assets/card-visuals/`. Shared card layouts and reveal motion live in `../../templates/` and are applied to all five canonical decks by `scripts/apply_templates.py`.

From the repository root:

```sh
python3 experiments/card-visuals/build.py
node experiments/card-visuals/check_preview.cjs
python3 -m http.server 8765 --bind 127.0.0.1 --directory experiments/card-visuals/build
```

Open `http://127.0.0.1:8765/preview.html`. The responsive preview includes up to 40 illustrated GENKI II words, both card directions, image and night-mode toggles, audio, and stroke animations. 落ち込む deliberately has its image hidden in this preview as a control; its canonical deck illustration is unaffected. The gallery shows every illustrated GENKI II entry.

Images are optimized transparent WebPs served from `build/media/`. All preview images begin loading immediately, with 運ぶ requested at high priority first. Late image decoding fades in. The preview uses the packaged templates and fields, with a small substitute for Anki field/furigana rendering.

The generated pilot package retains GENKI II note and model identities, so importing it updates the existing deck. Use a temporary Anki profile for isolated comparison. The builder does not import anything.

The build verifies note/card counts, IDs/GUIDs, scheduling, field schema, original media, image/audio references, SQLite integrity, ZIP CRCs, and image-free questions. Its report is `build/verification.json`. Native AnkiMobile motion and gestures still require device testing.

## Illustration and motion design

Illustrations appear after answering, with transparent backgrounds and generous internal space. The image stays within a 480px maximum width inside the 600px content area. It translates down, fades, and scales into place while the answer content moves together; the word becomes smaller, the Production cue becomes gray, and the outgoing question hint moves and fades. Reduced-motion preferences show the final state immediately.

Artwork is a memory cue for the intended sense, not a replacement for the definition. Exact word and reading matching prevents accidental homophone reuse. Distinct actions and abstract situations get their own artwork; shared meanings may explicitly reuse an image.
