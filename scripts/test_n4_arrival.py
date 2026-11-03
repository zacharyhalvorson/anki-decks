"""Validate the corrected arrival card in the packaged N4 deck."""
import hashlib, json, re, sqlite3, tempfile, unittest, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class ArrivalPackage(unittest.TestCase):
    def test_packaged_card_and_templates(self):
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(ROOT/'JLPT N4.apkg') as z:
            z.extract('collection.anki21',tmp)
            con=sqlite3.connect(Path(tmp)/'collection.anki21')
            flds,sfld,csum=con.execute('select flds,sfld,csum from notes where id=1776868953041').fetchone()
            f=flds.split('\x1f')
            self.assertEqual(f[:3],['着く','つく','to arrive; reach'])
            for i in (4,5):
                self.assertIn('着きました。',f[i]);self.assertIn('に着きます。',f[i]);self.assertNotIn('につきます。',f[i])
            self.assertIn('<span class="k-char">着</span>',f[7])
            self.assertEqual(sfld,'着く')
            self.assertEqual(csum,int(hashlib.sha1('着く'.encode()).hexdigest()[:8],16))
            self.assertEqual(f[8],'[sound:n4_wd_ea4f686b77736126.mp3]')
            self.assertEqual(con.execute('select count(*) from notes').fetchone()[0],1150)
            self.assertEqual(con.execute('select count(*) from cards where nid=1776868953041').fetchone()[0],2)
            models=json.loads(con.execute('select models from col').fetchone()[0])
            for model in models.values():
                for t in model['tmpls']:
                    self.assertIn('word/1422970',t['afmt'])
                    self.assertIn('class="dictionary-key"',t['afmt'])
                    self.assertNotIn('__DICTIONARY_LINKS__',t['afmt'])
            media=set(json.loads(z.read('media')).values())
            for ref in re.findall(r'(?:src="|\[sound:)([^"\]]+)',flds): self.assertIn(ref,media)
            con.close()

if __name__ == '__main__': unittest.main()
