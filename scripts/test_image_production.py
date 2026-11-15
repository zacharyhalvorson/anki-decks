"""Verify curated prompts and eligibility in every packaged deck."""
import hashlib,json,re,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ImageProductionTest(unittest.TestCase):
 def test_packages(self):
  entries=json.loads((ROOT/'assets/card-visuals/image-production.json').read_text())['entries']
  selected={'|'.join(e[k] for k in ('word','reading','meaning')) for e in entries}
  report=json.loads((ROOT/'assets/card-visuals/image-production-report.json').read_text())
  for d in report['decks']:
   with self.subTest(deck=d['deck']),zipfile.ZipFile(ROOT/'decks'/(d['deck']+'.apkg')) as z,tempfile.TemporaryDirectory() as tmp:
    z.extract('collection.anki21',tmp);db=sqlite3.connect(tmp+'/collection.anki21');models=json.loads(db.execute('select models from col').fetchone()[0]);media={v:k for k,v in json.loads(z.read('media')).items()};count=0
    for model in models.values():
     self.assertEqual([(t['name'],t['ord']) for t in model['tmpls']],[('Recognition',0),('Production',1)])
     self.assertEqual(len(model['flds']),10)
     rec,prod=model['tmpls'];self.assertNotIn('var rules =',rec['qfmt'])
     front=json.loads(re.search(r'var rules = (.*?);\n',prod['qfmt'])[1]);back=json.loads(re.search(r'var rules = (.*?);\n',prod['afmt'])[1]);self.assertEqual(front,back);self.assertEqual(set(front),selected)
     self.assertIn('{{WordAudio}}',prod['afmt']);self.assertNotIn('{{WordAudio}}',prod['qfmt']);self.assertNotIn('__IMAGE_PRODUCTION',prod['qfmt'])
     for raw, in db.execute('select flds from notes where mid=?',(model['id'],)):
      f=raw.split('\x1f');key='|'.join(f[:3])
      if key not in selected:continue
      count+=1;filename=front[key];self.assertIn(filename,media);self.assertIn('src="'+filename+'"',f[7]);blob=z.read(media[filename]);self.assertEqual(blob[:4],b'RIFF');self.assertEqual(blob[8:12],b'WEBP')
      self.assertTrue(f[8].startswith('[sound:'));self.assertIn('<hr class="ex-sep">',f[4])
    self.assertEqual(count,d['image_production_cards']);self.assertEqual(db.execute('select count(*) from cards').fetchone()[0],d['total_cards']);db.close()
 def test_reviewed_images(self):
  for e in json.loads((ROOT/'assets/card-visuals/image-production.json').read_text())['entries']:
   self.assertEqual(hashlib.sha256((ROOT/'assets/card-visuals/images'/e['image']).read_bytes()).hexdigest(),e['image_sha256'])
if __name__=='__main__':unittest.main()
