#!/usr/bin/env python3
"""Apply templates/ + assets/ to every .apkg in the repo (import-merge safe).

- replaces the note type's CSS and both back templates (fronts untouched)
- embeds assets/_kanji_strokes.js as a template media file
- embeds the on/kun reading clips (assets/kr/_kr_<hex>.mp3) that the deck's kanji breakdowns need
- bumps model mod/usn and col.mod so Anki's import picks the change up
- verifies note count, guids and media references before replacing the deck
"""
import json, os, re, shutil, sqlite3, sys, time, zipfile, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECKS = sys.argv[1:] or ["GENKI I Vocab", "GENKI II Vocab", "JLPT N4", "JLPT N5", "Quartet I Vocab"]  # optional: deck names as arguments
# The stroke asset is embedded under a content-hashed name (`_kanji_strokes_<md5[:8]>.js`): Anki's import does not
# reliably replace a media file that already exists under the same name, so a deck imported before kanji were added
# kept the old file and those kanji fell back to the plain glyph. A new name per content sidesteps that.
ASSET_SRC = "_kanji_strokes.js"

def rd(p): return open(p, encoding="utf8").read()
runtime = rd(f"{ROOT}/templates/runtime.js").strip()
css = rd(f"{ROOT}/templates/card.css")
afmt = {
    "Recognition": rd(f"{ROOT}/templates/recognition_back.html").replace("__RUNTIME__", runtime),
    "Production": rd(f"{ROOT}/templates/production_back.html").replace("__RUNTIME__", runtime),
}
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
    now = int(time.time())
    for m in models.values():
        m["css"] = css
        for t in m["tmpls"]:
            if t["name"] in afmt: t["afmt"] = afmt[t["name"]]
        m["mod"] = now; m["usn"] = -1
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
            if n in ("collection.anki21", "media", idx) or n in kr_add or n in stale: continue
            data = zin.read(n)
            comp = zipfile.ZIP_STORED if media.get(n, "").endswith(".mp3") else zipfile.ZIP_DEFLATED
            zout.writestr(n, data, comp)
        zout.write(db, "collection.anki21", zipfile.ZIP_DEFLATED)
        zout.writestr("media", json.dumps(media, ensure_ascii=False), zipfile.ZIP_DEFLATED)
        zout.writestr(idx, asset_bytes, zipfile.ZIP_DEFLATED)
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
    zchk.close()

    with open(src, "wb") as f, open(out, "rb") as g: shutil.copyfileobj(g, f)
    shutil.rmtree(work, ignore_errors=True)
    print(f"ok {deck}: notes={len(after_notes)} media={len(media2)} (+{len(kr_add)} reading clips) asset={ASSET} member={idx} dropped={len(stale)} size={os.path.getsize(src)//1024} KB")
