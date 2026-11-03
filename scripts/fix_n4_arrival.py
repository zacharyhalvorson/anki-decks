#!/usr/bin/env python3
"""Repair the existing arrival note without changing its GUID or review cards."""
import copy, hashlib, json, os, re, sqlite3, tempfile, time, zipfile
from pathlib import Path
from card_visuals import FIGURE
ROOT = Path(__file__).resolve().parents[1]
NOTE_ID = 1776868953041
DONOR_ID = 1776868954027

def repair(path):
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / 'collection.anki21'
        with zipfile.ZipFile(path) as src:
            db.write_bytes(src.read(db.name))
            con = sqlite3.connect(db)
            before = con.execute('select * from notes order by id').fetchall()
            cards = con.execute('select * from cards order by id').fetchall()
            row = con.execute('select flds, mod from notes where id=?', (NOTE_ID,)).fetchone()
            fields = row[0].split('\x1f')
            assert fields[:3] in [['つく', 'つく', 'to arrive; reach'], ['着く', 'つく', 'to arrive; reach']]
            donor = con.execute('select flds from notes where id=?', (DONOR_ID,)).fetchone()[0].split('\x1f')
            assert donor[:2] == ['着く', 'つく']
            fields[0] = '着く'
            for index in (4, 5):
                fields[index] = fields[index].replace('につきます。', 'に着きます。')
                assert 'につきます' not in fields[index] and '着きます' in fields[index]
            # Reuse the existing reviewed kanji data; retain this note's arrival illustration.
            fields[7] = ''.join(FIGURE.findall(fields[7])) + FIGURE.sub('', donor[7])
            updated = '\x1f'.join(fields)
            if updated == row[0]:
                con.close()
                print('Arrival spelling already corrected')
                return
            models = json.loads(con.execute('select models from col').fetchone()[0])
            mid = con.execute('select mid from notes where id=?', (NOTE_ID,)).fetchone()[0]
            assert models[str(mid)].get('sortf', 0) == 0
            checksum = int(hashlib.sha1(fields[0].encode()).hexdigest()[:8], 16)
            con.execute('update notes set flds=?, sfld=?, csum=?, mod=?, usn=-1 where id=?',
                        (updated, fields[0], checksum, max(int(time.time()), row[1]+1), NOTE_ID))
            con.execute('update col set mod=?', (int(time.time()*1000),))
            con.commit()
            after = con.execute('select * from notes order by id').fetchall()
            assert con.execute('pragma integrity_check').fetchone()[0] == 'ok'
            assert cards == con.execute('select * from cards order by id').fetchall()
            for old, new in zip(before, after):
                if old[0] != NOTE_ID:
                    assert old == new
                    continue
                assert all(old[i] == new[i] for i in (0,1,2,5,9,10))
                a,b = old[6].split('\x1f'), new[6].split('\x1f')
                assert all(a[i] == b[i] for i in (1,2,3,6,8,9)), 'reading/meaning/audio changed'
                assert a[4].replace('につきます。','に着きます。') == b[4]
                assert a[5].replace('につきます。','に着きます。') == b[5]
            con.close()
            staged = path.with_suffix('.apkg.tmp')
            with zipfile.ZipFile(staged, 'w') as dest:
                for info in src.infolist():
                    dest.writestr(copy.copy(info), db.read_bytes() if info.filename==db.name else src.read(info.filename))
            with zipfile.ZipFile(staged) as check:
                assert check.testzip() is None
                for info in src.infolist():
                    if info.filename != db.name: assert check.read(info.filename) == src.read(info.filename)
        os.replace(staged, path)
        print('Corrected 着く, both display fields for sentence two, and the kanji breakdown; identity and scheduling preserved')

if __name__ == '__main__': repair(ROOT / 'JLPT N4.apkg')
