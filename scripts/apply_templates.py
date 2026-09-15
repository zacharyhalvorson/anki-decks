#!/usr/bin/env python3
"""Apply templates/ + assets/ to every .apkg in the repo (import-merge safe).

- replaces the note type's CSS and both back templates (fronts untouched)
- embeds assets/_kanji_strokes.js as a template media file
- bumps model mod/usn and col.mod so Anki's import picks the change up
- verifies note count, guids and media references before replacing the deck
"""
import json, os, re, shutil, sqlite3, time, zipfile, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECKS = ["GENKI I Vocab", "GENKI II Vocab", "JLPT N4", "Quartet I Vocab"]
ASSET = "_kanji_strokes.js"

def rd(p): return open(p, encoding="utf8").read()
runtime = rd(f"{ROOT}/templates/runtime.js").strip()
css = rd(f"{ROOT}/templates/card.css")
afmt = {
    "Recognition": rd(f"{ROOT}/templates/recognition_back.html").replace("__RUNTIME__", runtime),
    "Production": rd(f"{ROOT}/templates/production_back.html").replace("__RUNTIME__", runtime),
}
asset_bytes = open(f"{ROOT}/assets/{ASSET}", "rb").read()

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

    # media map: replace an existing asset entry or append a new one
    idx = next((k for k, v in media.items() if v == ASSET), None)
    if idx is None:
        idx = str(max([int(k) for k in media] + [-1]) + 1)
        media[idx] = ASSET
    out = f"{work}/out.apkg"
    with zipfile.ZipFile(out, "w") as zout:
        for n in names:
            if n in ("collection.anki21", "media", idx): continue
            data = zin.read(n)
            comp = zipfile.ZIP_STORED if media.get(n, "").endswith(".mp3") else zipfile.ZIP_DEFLATED
            zout.writestr(n, data, comp)
        zout.write(db, "collection.anki21", zipfile.ZIP_DEFLATED)
        zout.writestr("media", json.dumps(media, ensure_ascii=False), zipfile.ZIP_DEFLATED)
        zout.writestr(idx, asset_bytes, zipfile.ZIP_DEFLATED)
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
    assert media2[idx] == ASSET and zchk.read(idx) == asset_bytes
    m2 = json.loads(sqlite3.connect(f"{work}/chk/collection.anki21").execute("select models from col").fetchone()[0])
    assert all(m["css"] == css for m in m2.values())
    zchk.close()

    with open(src, "wb") as f, open(out, "rb") as g: shutil.copyfileobj(g, f)
    shutil.rmtree(work, ignore_errors=True)
    print(f"ok {deck}: notes={len(after_notes)} media={len(media2)} asset member={idx} size={os.path.getsize(src)//1024} KB")
