#!/usr/bin/env python3
"""Apply templates/ + assets/ to every .apkg in the repo (import-merge safe).

- replaces the note type's CSS and all four templates (both fronts, both backs)
- inlines templates/runtime.js and templates/tap_guard.js into the backs (answer side ignores card taps; fronts still flip on tap)
- embeds assets/_kanji_strokes.js as a template media file
- embeds the on/kun reading clips (assets/kr/_kr_<hex>.mp3) that the deck's kanji breakdowns need
- bumps model mod/usn and col.mod so Anki's import picks the change up
- verifies note count, guids and media references before replacing the deck
"""
import json, os, re, shutil, sqlite3, sys, time, zipfile, tempfile
from card_visuals import apply_visuals, FIGURE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECKS = sys.argv[1:] or ["GENKI I Vocab", "GENKI II Vocab", "JLPT N4", "JLPT N5", "Quartet I Vocab"]  # optional: deck names as arguments
# The stroke asset is embedded under a content-hashed name (`_kanji_strokes_<md5[:8]>.js`): Anki's import does not
# reliably replace a media file that already exists under the same name, so a deck imported before kanji were added
# kept the old file and those kanji fell back to the plain glyph. A new name per content sidesteps that.
ASSET_SRC = "_kanji_strokes.js"

def rd(p): return open(p, encoding="utf8").read()
runtime = rd(f"{ROOT}/templates/runtime.js").strip() + "\n" + rd(f"{ROOT}/templates/visuals.js").strip()
link_entries = json.loads(rd(f"{ROOT}/assets/dictionary/nihongo-links.json"))
link_rules = {'|'.join(e[k] for k in ('word', 'reading', 'meaning')): e['target'] for e in link_entries}
assert len(link_rules) == len(link_entries), 'duplicate dictionary sense keys'
link_script = rd(f"{ROOT}/templates/dictionary_links.js").replace('__DICTIONARY_LINKS__', json.dumps(link_rules, ensure_ascii=True).replace('</', '<\\/'))
runtime += '\n' + link_script
tap_guard = rd(f"{ROOT}/templates/tap_guard.js").strip()
css = rd(f"{ROOT}/templates/card.css") + "\n" + rd(f"{ROOT}/templates/visuals.css")
def tmpl(name): return rd(f"{ROOT}/templates/{name}.html").replace("__VISUAL_FRONT__", rd(f"{ROOT}/templates/visual_front.js")).replace("__RUNTIME__", runtime).replace("__TAP_GUARD__", tap_guard)
afmt = {"Recognition": tmpl("recognition_back"), "Production": tmpl("production_back")}
qfmt = {"Recognition": tmpl("recognition_front"), "Production": tmpl("production_front")}
# answer side only: card taps must never trigger AnkiMobile's tap zones there (see templates/tap_guard.js).
# The question side must stay unguarded so a tap still flips the card.
for side in list(afmt.values()) + list(qfmt.values()):
    assert "__TAP_GUARD__" not in side and "__RUNTIME__" not in side, "unfilled placeholder in a template"
for side in afmt.values():
    assert "data-notap" in side and "tap-shield" in side and tap_guard in side, "back template is missing the tap guard"
for side in qfmt.values():
    assert "data-notap" not in side and "tap-shield" not in side and "tappable" not in side, "front template must not carry the tap guard"
asset_bytes = open(f"{ROOT}/assets/{ASSET_SRC}", "rb").read()
import hashlib
ASSET = f"_kanji_strokes_{hashlib.md5(asset_bytes).hexdigest()[:8]}.js"
for k in afmt: afmt[k] = afmt[k].replace(f'src="{ASSET_SRC}"', f'src="{ASSET}"')
assert all(f'src="{ASSET}"' in v for v in afmt.values()), "back templates must load _kanji_strokes.js"
KR_DIR = f"{ROOT}/assets/kr"

def hira(s): return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
def kr_name(reading):
    """same rule as krFile() in templates/runtime.js"""
    sp = hira(re.sub(r"[-.()（）\s‐－]", "", reading))
    if not sp or not re.fullmatch(r"[ぁ-ゖー]+", sp): return None
    return "_kr_" + "".join("%04x" % ord(c) for c in sp) + ".mp3"
def kr_needed(dbpath):
    con = sqlite3.connect(dbpath); need = set()
    for (flds,) in con.execute("select flds from notes"):
        for r in re.findall(r'<span class="k-r">(.*?)</span>', flds.split("\x1f")[7]):
            n = kr_name(r)
            if n: need.add(n)
    con.close(); return need

def snapshot(dbpath):
    con = sqlite3.connect(dbpath)
    notes = con.execute("select id, guid, flds from notes").fetchall()
    refs = set()
    for _, _, flds in notes:
        refs.update(re.findall(r"\[sound:([^\]]+)\]", flds))
        refs.update(re.findall(r'src="([^"]+\.mp3)"', flds))
    con.close()
    return {(i, g) for i, g, _ in notes}, refs

for deck in DECKS:
    src = f"{ROOT}/{deck}.apkg"
    if not os.path.exists(src):
        print(f"-- {deck}: not found, skipping"); continue

    work = tempfile.mkdtemp(prefix="apkg-")
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    media = json.loads(zin.read("media"))
    zin.extract("collection.anki21", work)
    db = f"{work}/collection.anki21"
    before_notes, refs = snapshot(db)

    con = sqlite3.connect(db)
    models = json.loads(con.execute("select models from col").fetchone()[0])
    original_notes = con.execute("select * from notes order by id").fetchall()
    original_cards = con.execute("select * from cards order by id").fetchall()
    original_schema = {k: (m["flds"], [(t["name"], t["ord"]) for t in m["tmpls"]]) for k, m in models.items()}
    now = int(time.time())
    image_add, illustrated, images_changed = apply_visuals(con, media, ROOT, now)
    for m in models.values():
        m["css"] = css
        for t in m["tmpls"]:
            if t["name"] in afmt: t["afmt"] = afmt[t["name"]]
            if t["name"] in qfmt: t["qfmt"] = qfmt[t["name"]]
        m["mod"] = max(now, m["mod"] + 1); m["usn"] = -1
    con.execute("update col set models = ?, mod = ?", (json.dumps(models), now * 1000))
    con.commit(); con.close()

    # media map: drop every other stroke-asset version, then reuse or add the entry for this one
    stale = [k for k, v in media.items() if re.fullmatch(r"_kanji_strokes(_[0-9a-f]{8})?\.js", v) and v != ASSET]
    for k in stale: del media[k]
    idx = next((k for k, v in media.items() if v == ASSET), None)
    if idx is None:
        idx = str(max([int(k) for k in media] + [-1]) + 1)
        media[idx] = ASSET
    # reading clips this deck needs and does not have yet
    have = set(media.values()); kr_add = {}; kr_missing = []
    nxt = max([int(k) for k in media] + [-1]) + 1
    for fn in sorted(kr_needed(db)):
        if fn in have: continue
        if not os.path.exists(f"{KR_DIR}/{fn}"): kr_missing.append(fn); continue
        kr_add[str(nxt)] = fn; media[str(nxt)] = fn; nxt += 1
    if kr_missing: print(f"   !! {deck}: {len(kr_missing)} reading clips missing from assets/kr, e.g. {kr_missing[:3]}")
    out = f"{work}/out.apkg"
    with zipfile.ZipFile(out, "w") as zout:
        for n in names:
            if n in ("collection.anki21", "media", idx) or n in kr_add or n in stale or n in image_add: continue
            data = zin.read(n)
            comp = zipfile.ZIP_STORED if media.get(n, "").endswith(".mp3") else zipfile.ZIP_DEFLATED
            zout.writestr(n, data, comp)
        zout.write(db, "collection.anki21", zipfile.ZIP_DEFLATED)
        zout.writestr("media", json.dumps(media, ensure_ascii=False), zipfile.ZIP_DEFLATED)
        zout.writestr(idx, asset_bytes, zipfile.ZIP_DEFLATED)
        for k, blob in image_add.items(): zout.writestr(k, blob, zipfile.ZIP_STORED)
        for k, fn in kr_add.items(): zout.write(f"{KR_DIR}/{fn}", k, zipfile.ZIP_STORED)
    zin.close()

    # verify
    zchk = zipfile.ZipFile(out)
    zchk.extract("collection.anki21", f"{work}/chk")
    after_notes, refs2 = snapshot(f"{work}/chk/collection.anki21")
    media2 = json.loads(zchk.read("media"))
    files = set(media2.values()); members = set(zchk.namelist())
    assert before_notes == after_notes, "note ids/guids changed"
    assert refs == refs2, "audio references changed"
    missing = [r for r in refs2 if r not in files]
    assert not missing, f"unresolved media refs: {missing[:5]}"
    assert all(k in members for k in media2), "media map points at a missing member"
    assert len(files) == len(media2), "duplicate media names"
    assert all(fn in files for fn in kr_add.values())
    assert media2[idx] == ASSET and zchk.read(idx) == asset_bytes
    assert not [v for v in files if v.startswith("_kanji_strokes") and v != ASSET], "stale stroke asset left in media"
    m2 = json.loads(sqlite3.connect(f"{work}/chk/collection.anki21").execute("select models from col").fetchone()[0])
    assert all(f'src="{ASSET}"' in t["afmt"] for m in m2.values() for t in m["tmpls"]), "template does not load the embedded asset"
    assert all(m["css"] == css for m in m2.values())
    assert all(t["qfmt"] == qfmt[t["name"]] and t["afmt"] == afmt[t["name"]] for m in m2.values() for t in m["tmpls"]), "templates not applied"
    chk = sqlite3.connect(f"{work}/chk/collection.anki21")
    assert chk.execute("pragma integrity_check").fetchone()[0] == "ok"
    assert original_cards == chk.execute("select * from cards order by id").fetchall(), "card scheduling changed"
    assert original_schema == {k: (m["flds"], [(t["name"], t["ord"]) for t in m["tmpls"]]) for k, m in m2.items()}, "schema changed"
    after_rows = chk.execute("select * from notes order by id").fetchall()
    assert len(original_notes) == len(after_rows)
    for old, new in zip(original_notes, after_rows):
        assert all(old[i] == new[i] for i in range(len(old)) if i not in (3, 4, 6)), "note identity/metadata changed"
        a, b = old[6].split("\x1f"), new[6].split("\x1f")
        assert all(a[i] == b[i] for i in range(len(a)) if i != 7), "non-image field changed"
        assert FIGURE.sub('', a[7]) == FIGURE.sub('', b[7]), "kanji breakdown changed"
        assert len(FIGURE.findall(b[7])) <= 1, "duplicate illustration"
        for ref in re.findall(r'(?:src="|\[sound:)([^"\]]+)', new[6]):
            assert ref in files, f"missing media {ref}"
    chk.close()
    assert zchk.testzip() is None
    with zipfile.ZipFile(src) as original:
        for info in original.infolist():
            if info.filename not in ("collection.anki21", "media") and info.filename not in stale and info.filename != idx:
                assert original.read(info.filename) == zchk.read(info.filename), "original media/stub changed"
    zchk.close()

    staged = src + ".tmp"
    shutil.copyfile(out, staged)
    os.replace(staged, src)
    shutil.rmtree(work, ignore_errors=True)
    print(f"ok {deck}: notes={len(after_notes)} media={len(media2)} images={illustrated} (changed {images_changed}, added {len(image_add)}) (+{len(kr_add)} reading clips) asset={ASSET} member={idx} dropped={len(stale)} size={os.path.getsize(src)//1024} KB")
