#!/usr/bin/env python3
"""Build GENKI I lessons 1–12 from the reviewed, local-textbook vocabulary PSV.

Run with the dependencies in assets/genki1/README.md. No live Anki writes.
"""
from pathlib import Path
import argparse, collections, hashlib, html, json, re, sqlite3, time, zipfile
ROOT = Path(__file__).resolve().parents[1]
DECK_DIR = ROOT / 'decks'
DATA = ROOT / 'assets/genki1'
WORK = ROOT / '_to_delete/genki1-build'
BOOK = ROOT.parent / 'GENKI ' / 'GENKI 1 (3rd Edition).pdf'
SEPARATOR = '<hr class="ex-sep">'
VOCAB_PAGES = {1:38,2:58,3:84,4:104,5:130,6:148,7:168,8:188,9:212,10:232,11:256,12:274}

def read_deck(path):
    z = zipfile.ZipFile(path)
    c = sqlite3.connect(':memory:')
    c.deserialize(z.read('collection.anki21'))
    return z, c, json.loads(z.read('media'))

def render():
    import pypdfium2 as pdf
    from PIL import Image, ImageDraw
    WORK.mkdir(parents=True, exist_ok=True)
    doc = pdf.PdfDocument(BOOK)
    for lesson, page in VOCAB_PAGES.items():
        images = []
        for p in range(page, page+3):
            im = doc[p+7].render(scale=1.65).to_pil()
            im.save(WORK / f'l{lesson:02}-p{p}.png')
            images.append(im)
        sheet = Image.new('RGB', (images[0].width*3, images[0].height), 'white')
        for i, im in enumerate(images): sheet.paste(im,(i*im.width,0))
        sheet.save(WORK / f'lesson-{lesson:02}.png')
    print(WORK)

def inventory():
    WORK.mkdir(parents=True, exist_ok=True)
    examples = collections.defaultdict(list)
    for path in DECK_DIR.glob('*.apkg'):
        z,c,m=read_deck(path)
        for tags,flds in c.execute('select tags,flds from notes'):
            f=flds.split(chr(31))
            examples[f[0]].append({'reading':f[1],'meaning':f[2],'pos':f[3], 'ja':f[4].split(SEPARATOR),'furigana':f[5].split(SEPARATOR),'en':f[6].split(SEPARATOR),'deck':path.name})
        z.close();c.close()
    (WORK/'examples.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n')
    print(len(examples),'distinct words')

POS = {'noun':'Noun','u-verb':'Godan Verb','ru-verb':'Ichidan Verb','irregular-verb':'Irregular Verb','i-adjective':'い-Adjective','na-adjective':'な-Adjective','adverb-expression':'Adverb / Expression','counter':'Counter','number':'Number','suffix':'Suffix'}
KANJI = re.compile(r'[一-龯]')

def hira(s):
    return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s)

def plain_ruby(s):
    return re.sub(r'([^\s\[\]<>]+)\[([^\]]+)\]',r'\1',s).replace(' ','')

def spoken_ruby(s):
    return hira(re.sub(r'([^\s\[\]<>]+)\[([^\]]+)\]',r'\2',s).replace(' ',''))

def normalize_word(s):
    s=re.sub(r'[（(].*?[)）]','',s)
    return re.sub(r'[〜～\s]','',s).replace('/','、').replace('／','、')

def annotate(text):
    """Fully annotate kanji using UniDic, retaining kana outside each kanji run."""
    from fugashi import Tagger
    if not hasattr(annotate,'tagger'): annotate.tagger=Tagger()
    override={'日本':'にほん','明後日':'あさって','箱':'はこ','私':'わたし','母':'はは','父':'ちち','兄':'あに','姉':'あね','人':'ひと','方':'かた','家':'いえ','町':'まち','何':'なに','時':'とき','後':'あと','今年':'ことし','明日':'あした','昨日':'きのう','今日':'きょう','今朝':'けさ','一日':'いちにち','毎日':'まいにち','二十歳':'はたち','今度':'こんど','上手':'じょうず','下手':'へた','人気':'にんき','空':'そら','四人':'よにん','何人':'なんにん','一人':'ひとり','二人':'ふたり','大人':'おとな','二三日':'にさんにち'}
    # Pin irregular counters before tokenization. The private markers are restored below.
    protected={}
    if not hasattr(annotate,'lexicon'):
        lexicon={}
        for r in source_rows():
            if len(r['word'])>1 and KANJI.search(r['word']) and not re.search(r'[〜～／/]',r['word']+r['reading']):
                lexicon[r['word']]=normalize_word(r['reading'])
        for note in json.loads((DATA/'baseline.json').read_text())['notes']:
            f=note[6].split(chr(31))
            if len(f[0])>1 and KANJI.search(f[0]) and not re.search(r'[〜～／/]',f[0]+f[1]):lexicon[f[0]]=normalize_word(f[1])
        annotate.lexicon=lexicon
    lexicon=dict(annotate.lexicon)
    lexicon.update({'富士山':'ふじさん','一か月':'いっかげつ','六か月':'ろっかげつ','三人':'さんにん','五人':'ごにん','三日後':'みっかご','一時間後':'いちじかんご','二日酔い':'ふつかよい','お母さん':'おかあさん','お父さん':'おとうさん','お姉さん':'おねえさん','お兄さん':'おにいさん'})
    if 'りんごを十ください' in text or '卵が十あります' in text:lexicon['十']='とお'
    lexicon.update({'二時':'にじ','三時':'さんじ','五時':'ごじ','六時':'ろくじ','八時':'はちじ','十時':'じゅうじ','十一時':'じゅういちじ','何です':'なんです','何の':'なんの','何時':'なんじ','何年生':'なんねんせい','四年生':'よねんせい','七時':'しちじ','九時':'くじ','四時':'よじ','十二時':'じゅうにじ','三十分':'さんじゅっぷん','十分':'じゅっぷん','五分':'ごふん','二本':'にほん','一日':'いちにち','一人':'ひとり','二人':'ふたり','四人':'よにん','何人':'なんにん','一時間':'いちじかん','二十歳':'はたち','二三日':'にさんにち','一つ':'ひとつ','二つ':'ふたつ','三つ':'みっつ','四つ':'よっつ','五つ':'いつつ','六つ':'むっつ','七つ':'ななつ','八つ':'やっつ','九つ':'ここのつ','二十日':'はつか'})
    for surface,reading in sorted(lexicon.items(),key=lambda item:len(item[0]),reverse=True):
        if surface in text:
            marker=chr(0xE000+len(protected));protected[marker]=' '+ruby(surface,reading);text=text.replace(surface,marker)
    result=[]
    for token in annotate.tagger(text):
        surface=token.surface
        if not KANJI.search(surface):result.append(surface);continue
        reading=override.get(surface) or hira(token.feature.kana or '')
        if not reading or reading=='*':raise ValueError(('Missing reading',surface,text))
        # A kanji token with okurigana: 食べ -> 食[た]べ. More complex tokens remain intact.
        m=re.fullmatch(r'([一-龯々]+)([ぁ-ゖ]+)',surface)
        if m and reading.endswith(m[2]):result.append(' '+m[1]+'['+reading[:-len(m[2])]+']'+m[2])
        else:result.append(' '+surface+'['+reading+']')
    result=''.join(result)
    for marker,markup in protected.items():result=result.replace(marker,markup)
    assert plain_ruby(result)==text.translate(str.maketrans({k:plain_ruby(v) for k,v in protected.items()})), (text,result)
    return result.strip()

def source_rows():
    rows=[]
    for n,line in enumerate((DATA/'vocabulary.psv').read_text().splitlines(),1):
        if not line or line.startswith('#'):continue
        f=line.split('|');assert len(f)==9,(n,len(f),line)
        lesson,word,reading,meaning,pos,a,b,c,d=f
        assert pos in POS and 1<=int(lesson)<=12
        assert a!=c and b and d
        rows.append(dict(lesson=int(lesson),word=word,reading=reading,meaning=meaning,pos=pos,ja=[a,c],en=[b,d]))
    return rows

def prepare():
    WORK.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((DATA/'baseline.json').read_text())
    old={tuple(n[6].split(chr(31))[:2]):(n[0],n[6].split(chr(31))) for n in baseline['notes']}
    rows=source_rows()
    for r in rows:
        if KANJI.search(r['word']) and not re.search(r'[〜～／/]',r['word']+r['reading']):
            assert spoken_ruby(ruby(r['word'],normalize_word(r['reading'])))==hira(normalize_word(r['reading'])),r['word']
    # Preserve earliest lesson of existing repeated family/country vocabulary.
    rows=[r for r in rows if (r['word'],r['reading']) not in old]
    keys=[(r['word'],r['reading'],r['meaning']) for r in rows]
    assert len(keys)==len(set(keys)), 'duplicate source sense'
    corrections={
      '学生':('田中さんは大学の学生です。','Tanaka is a university student.'),
      '工学':('たけしさんの専攻は工学ですか。',"Is Takeshi's major engineering?"),
      '政治':('父は政治の先生です。','My father is a politics teacher.'),
      '看護師':('姉は病院の看護師です。','My older sister is a nurse at a hospital.'),
      '高校生':('弟は日本の高校生です。','My younger brother is a high school student in Japan.')}
    for (word,reading),(nid,f) in old.items():
        if word not in corrections:continue
        ja=f[4].split(SEPARATOR);en=f[6].split(SEPARATOR)
        ja[1],en[1]=corrections[word]
        rows.append(dict(lesson=1,word=word,reading=reading,meaning=f[2],pos=None,ja=ja,en=en,nid=nid))
    for row in rows:
        row['furigana']=[annotate(t) for t in row['ja']]
        row['tts']=[spoken_ruby(t).replace('Ｔ','ティー').replace('Ｌ','エル') for t in row['furigana']]
        assert all(not re.search(r'[一-龯々A-Za-zＡ-Ｚａ-ｚ0-9]',t) for t in row['tts']),row
    (WORK/'prepared.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    # Tracked review artifact; audio inputs are explicit and can be checked before synthesis.
    (DATA/'reading-review.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print('Prepared',len(rows),'notes;',dict(sorted(collections.Counter(r['lesson'] for r in rows).items())),flush=True)
    return rows

def audio():
    from gtts import gTTS
    rows=prepare();cache=WORK/'audio';cache.mkdir(exist_ok=True)
    jobs={}
    for r in rows:
        if not r.get('nid'):
            t=normalize_word(r['reading']);jobs['genki1_wd_'+hashlib.md5(('gtts-ja:'+t).encode()).hexdigest()[:16]+'.mp3']=t
        for t in r['tts']:jobs['genki1_ex_'+hashlib.md5(('gtts-ja:'+t).encode()).hexdigest()[:16]+'.mp3']=t
    z,_,media=read_deck(DECK_DIR/'GENKI I Vocab.apkg')
    for member,name in media.items():
        if name in jobs and not (cache/name).exists():(cache/name).write_bytes(z.read(member))
    z.close()
    todo=[(fn,t) for fn,t in jobs.items() if not (cache/fn).exists()]
    print('Audio clips:',len(jobs),'total,',len(todo),'to generate',flush=True)
    for i,(fn,t) in enumerate(todo,1):
        for attempt in range(5):
            try:
                blob=gTTS(t,lang='ja',timeout=30).write_to_fp
                import io
                buf=io.BytesIO();blob(buf);data=buf.getvalue()
                assert len(data)>500 and (data.startswith(b'ID3') or data[0]==255)
                (cache/fn).write_bytes(data);break
            except Exception as e:
                if attempt==4:raise
                print('retry',fn,type(e).__name__,flush=True);time.sleep(2**attempt)
        if i%20==0 or i==len(todo):print('Generated',i,'/',len(todo),flush=True)
        time.sleep(.25)
    print('Audio ready',flush=True)

def ruby(surface,reading):
    reading=hira(reading)
    prefix=re.match(r'^[^一-龯々]*',surface)[0]
    suffix=re.search(r'[^一-龯々]*$',surface)[0]
    if prefix and reading.startswith(hira(prefix)):
        surface=surface[len(prefix):];reading=reading[len(prefix):]
    else:prefix=''
    if suffix and reading.endswith(hira(suffix)):
        surface=surface[:-len(suffix)];reading=reading[:-len(suffix)]
    else:suffix=''
    return prefix+(' ' if prefix else '')+surface+'['+reading+']'+suffix

def kanji_resources():
    result={}
    for path in DECK_DIR.glob('*.apkg'):
        z,c,_=read_deck(path)
        for f, in c.execute('select flds from notes'):
            f=f.split(chr(31))
            for chunk in f[7].split('<div class="k-brk">')[1:]:
                char=re.search(r'<span class="k-char">(.*?)</span>',chunk)
                if char:result.setdefault(char[1],'<div class="k-brk">'+chunk.strip())
        z.close();c.close()
    import unicodedata
    for char,d in json.loads((DATA/'new-kanji.json').read_text()).items():
        def span(cls,text):return '<span class="'+cls+'">'+html.escape(str(text))+'</span>'
        def stat(value,label):return span('k-stat', '__RAW__').replace('__RAW__',span('k-stat-v',value)+span('k-stat-l',label))
        stats=stat(d['stroke_count'],'Strokes')+(stat('N'+str(d['jlpt']),'JLPT') if d['jlpt'] else '')
        head='<div class="k-head"><a class="k-link" href="https://nihongo-app.com/dictionary/kanji/'+char+'">'+span('k-char',char)+'</a><span class="k-stats">'+stats+'</span></div>'
        readings=[x for group in d['rm'] for x in group['readings']]
        meanings=[x['value'] for group in d['rm'] for x in group['meanings'] if not x['m_lang'] or x['m_lang']=='en']
        lines=['<div class="k-brk">',head,'<div class="k-mean">'+html.escape(', '.join(meanings))+'</div>']
        for typ,label in [('ja_on','On:'),('ja_kun','Kun:')]:
            values=[span('k-r',x['value']) for x in readings if x['type']==typ]
            if values:lines.append('<div class="k-reading">'+span('k-label',label)+' '+', '.join(values)+'</div>')
        radical=next(x['value'] for x in d['radicals'] if x['type']=='classical')
        rad=unicodedata.normalize('NFKC',chr(0x2f00+int(radical)-1))
        link=lambda x:'<a class="k-link" href="https://nihongo-app.com/dictionary/kanji-element/'+x+'">'+x+'</a>'
        lines.append('<div class="k-radical">'+span('k-label','Radical:')+' '+link(rad)+'</div>')
        if d.get('components'):lines.append('<div class="k-components">'+span('k-label','Components:')+' '+', '.join(link(x) for x in d['components'])+'</div>')
        lines.append('</div>');result[char]='\n'.join(lines)
    return result

def readings():
    """Generate any new shared on/kun clips using the existing kr_name contract."""
    from gtts import gTTS
    import io
    k=kanji_resources();needed=set()
    for r in prepare():
        for ch in KANJI.findall(r['word']):
            assert ch in k,ch
            for reading in re.findall(r'<span class="k-r">(.*?)</span>',k[ch]):
                sp=hira(re.sub(r'[-.()（）\s‐－]','',reading))
                if re.fullmatch(r'[ぁ-ゖー]+',sp):needed.add(sp)
    count=0
    for sp in sorted(needed):
        fn='_kr_'+''.join('%04x'%ord(c) for c in sp)+'.mp3';p=ROOT/'assets/kr'/fn
        if p.exists():continue
        text=sp
        if sp.endswith(('は','へ')):text=''.join(chr(ord(c)+96) if 'ぁ'<=c<='ゖ' else c for c in sp)
        for attempt in range(5):
            try:
                buf=io.BytesIO();gTTS(text,lang='ja',timeout=30).write_to_fp(buf);blob=buf.getvalue()
                assert len(blob)>500 and (blob.startswith(b'ID3') or blob[0]==255)
                p.write_bytes(blob);break
            except Exception:
                if attempt==4:raise
                time.sleep(2**attempt)
        count+=1;time.sleep(.25)
    print('Added',count,'on/kun clips',flush=True)

def refs(fields):
    return set(re.findall(r'(?:src="|\[sound:)([^"\]]+)',fields))

def build():
    from card_visuals import apply_visuals
    reuse_packaged_artwork()
    rows=prepare();path=DECK_DIR/'GENKI I Vocab.apkg';z,c,media=read_deck(path)
    before_cards=c.execute('select * from cards order by id').fetchall()
    before_notes={n[0]:n for n in c.execute('select * from notes')}
    now=int(time.time());models=json.loads(c.execute('select models from col').fetchone()[0]);mid=1800000000003;did=1800000000004
    assert str(mid) in models and len(models[str(mid)]['flds'])==10
    kanji=kanji_resources();added={};names=set(media.values())
    def add_audio(filename):
        if filename not in names:
            blob=(WORK/'audio'/filename).read_bytes();assert len(blob)>500
            index=str(max(map(int,media),default=-1)+1);media[index]=filename;names.add(filename);added[index]=blob
        return filename
    max_due=c.execute('select max(due) from cards where type=0').fetchone()[0] or 0
    existing={n[1]:n[0] for n in before_notes.values()};inserted=changed=0
    for row in rows:
        if row.get('nid'):
            nid=row['nid'];f=before_notes[nid][6].split(chr(31))
        else:
            guid=hashlib.md5(('genki1:'+str(row['lesson'])+':'+row['word']+':'+row['reading']+':'+row['meaning']).encode()).hexdigest()[:10]
            nid=existing.get(guid,1810000000000+int(hashlib.sha256(guid.encode()).hexdigest()[:10],16))
            pos=POS[row['pos']]
            if row['pos']=='irregular-verb':pos='Suru Verb' if row['reading'].endswith('する') else 'Kuru Verb' if row['reading'].endswith('くる') else pos
            f=[row['word'],row['reading'],row['meaning'],pos,'','','','','','']
            f[7]=before_notes[nid][6].split(chr(31))[7] if nid in before_notes else '\n'.join(kanji[ch] for ch in dict.fromkeys(KANJI.findall(row['word'])))
            t=normalize_word(row['reading']);fn='genki1_wd_'+hashlib.md5(('gtts-ja:'+t).encode()).hexdigest()[:16]+'.mp3'
            f[8]='[sound:'+add_audio(fn)+']'
        for index,key in [(4,'ja'),(5,'furigana'),(6,'en')]:f[index]=SEPARATOR.join(row[key])
        audio=[]
        for t in row['tts']:
            fn='genki1_ex_'+hashlib.md5(('gtts-ja:'+t).encode()).hexdigest()[:16]+'.mp3'
            audio.append('<audio src="'+add_audio(fn)+'" preload="none"></audio>')
        f[9]=''.join(audio);fields=chr(31).join(f)
        if nid in before_notes:
            if fields!=before_notes[nid][6]:
                c.execute('update notes set flds=?,mod=?,usn=-1 where id=?',(fields,max(now,before_notes[nid][3]+1),nid));changed+=1
        else:
            tags=' genki-%02d %s '%(row['lesson'],row['pos'])
            csum=int(hashlib.sha1(f[0].encode()).hexdigest()[:8],16)
            c.execute('insert into notes values (?,?,?,?,?,?,?,?,?,?,?)',(nid,guid,mid,now,-1,tags,fields,f[0],csum,0,''))
            for ordinal in [0,1]:
                max_due+=1;cid=nid*2+ordinal
                c.execute('insert into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(cid,nid,did,ordinal,now,-1,0,0,max_due,0,0,0,0,0,0,0,0,''))
            inserted+=1
    image_add,illustrated,_=apply_visuals(c,media,str(ROOT),now);added.update(image_add)
    # Explicitly retain template media while pruning obsolete field media.
    needed=set()
    for f, in c.execute('select flds from notes'):needed.update(refs(f))
    media={k:v for k,v in media.items() if v.startswith('_') or v in needed}
    tags=json.loads(c.execute('select tags from col').fetchone()[0])
    for n in range(1,13):tags['genki-%02d'%n]=now
    c.execute('update col set mod=?,tags=?',(now*1000,json.dumps(tags)));c.commit()
    assert all(tuple(card)==tuple(c.execute('select * from cards where id=?',(card[0],)).fetchone()) for card in before_cards)
    staged=WORK/'candidate.apkg'
    with zipfile.ZipFile(staged,'w') as out:
        for key in ['collection.anki2','meta']:out.writestr(key,z.read(key),zipfile.ZIP_DEFLATED)
        out.writestr('collection.anki21',c.serialize(),zipfile.ZIP_DEFLATED)
        out.writestr('media',json.dumps(media,ensure_ascii=False),zipfile.ZIP_DEFLATED)
        for key,filename in media.items():
            out.writestr(key,added[key] if key in added else z.read(key),zipfile.ZIP_STORED if filename.endswith(('.mp3','.webp')) else zipfile.ZIP_DEFLATED)
    z.close();c.close()
    check(staged,write_report=False)
    import os,shutil
    temp=path.with_suffix('.apkg.tmp');shutil.copyfile(staged,temp);os.replace(temp,path)
    print('Built:',inserted,'new notes,',changed,'updated;',illustrated,'illustrated',flush=True)
    check(path)

def check(path=None,write_report=True):
    path=path or DECK_DIR/'GENKI I Vocab.apkg';z,c,media=read_deck(path)
    assert z.testzip() is None and c.execute('pragma integrity_check').fetchone()[0]=='ok'
    notes=c.execute('select * from notes order by id').fetchall();cards=c.execute('select * from cards order by id').fetchall()
    baseline=json.loads((DATA/'baseline.json').read_text());old={n[0]:n for n in baseline['notes']};by_id={n[0]:n for n in notes}
    assert len(notes)==660 and len(cards)==1320,(len(notes),len(cards))
    assert len({n[1] for n in notes})==len(notes)
    for n in old.values():
        after=by_id[n[0]]
        assert all(n[i]==after[i] for i in [0,1,2,5,7,8,9,10]),('identity',n[0])
        a,b=n[6].split(chr(31)),after[6].split(chr(31))
        assert all(a[i]==b[i] for i in [0,1,2,3,8]),('original content',a[0])
        if a[0] not in {'学生','工学','政治','看護師','高校生'}:
            assert all(a[i]==b[i] for i in [4,5,6,9]),('existing examples changed',a[0])
    by_card={x[0]:x for x in cards}
    for card in baseline['cards']:assert list(by_card[card[0]])==card,('scheduling changed',card[0])
    for nid,count,ords in c.execute('select nid,count(*),group_concat(ord) from cards group by nid'):
        assert count==2 and set(ords.split(','))=={'0','1'} and nid in by_id
    models=json.loads(c.execute('select models from col').fetchone()[0])
    for key,m in baseline['models'].items():
        model=models[key];assert model['id']==m['id'] and model['name']==m['name']
        assert [f['name'] for f in model['flds']]==m['fields']
        assert [[t['name'],t['ord']] for t in model['tmpls']]==m['templates']
    assert {card[2] for card in cards}=={baseline['deck_id']}
    files=set(media.values());assert len(files)==len(media) and all(k in z.namelist() for k in media)
    assert all(name.isascii() for name in files)
    lessons=collections.Counter();packaged={}
    for n in notes:
        tags=n[5].split();lt=[t for t in tags if t.startswith('genki-')]
        assert len(lt)==1 and re.fullmatch(r'genki-(0[1-9]|1[012])',lt[0]),tags
        assert not any(t.startswith('lesson-') for t in tags)
        assert any(t in POS for t in tags),tags
        f=n[6].split(chr(31));assert len(f)==10
        lessons[lt[0]]+=1;packaged[tuple(f[:3])]=f
        assert len(f[4].split(SEPARATOR))==len(f[5].split(SEPARATOR))==len(f[6].split(SEPARATOR))==2
        assert f[4].split(SEPARATOR)[0]!=f[4].split(SEPARATOR)[1]
        assert len(re.findall(r'<audio src="',f[9]))==2
        assert refs(n[6])<=files,(f[0],refs(n[6])-files)
        for ja,fu in zip(f[4].split(SEPARATOR),f[5].split(SEPARATOR)):
            assert plain_ruby(fu)==ja,(f[0],ja,fu)
            assert not KANJI.search(re.sub(r'[^\s\[\]<>]+\[[^\]]+\]','',fu)),('missing furigana',f[0],fu)
        chars=set(KANJI.findall(f[0]));bk=set(re.findall(r'<span class="k-char">(.*?)</span>',f[7]));assert chars<=bk,(f[0],chars-bk)
    for r in source_rows():
        # Repeated entries use the existing earliest-lesson note, preserving its gloss.
        key=(r['word'],r['reading'],r['meaning'])
        if any(n[6].split(chr(31))[:2]==[r['word'],r['reading']] for n in old.values()):continue
        f=packaged[key];assert f[4]==SEPARATOR.join(r['ja']) and f[6]==SEPARATOR.join(r['en'])
    assert set(lessons)=={'genki-%02d'%n for n in range(1,13)}
    report={'notes':len(notes),'cards':len(cards),'lessons':dict(sorted(lessons.items())),'original_notes_preserved':len(old),'original_card_rows_unchanged':len(baseline['cards']),'two_examples_per_note':True,'all_furigana_round_trips':True,'all_media_resolve':True,'schema_and_ids_unchanged':True,'illustrated_notes':sum('vocab-visual' in n[6] for n in notes),'size_bytes':path.stat().st_size}
    if write_report:(DATA/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True);z.close();c.close()

def reuse_packaged_artwork():
    """Reuse accepted WebPs already in exports, avoiding iCloud-only cache reads."""
    import card_visuals
    lookup,senses=card_visuals.visual_lookup(ROOT/'assets/card-visuals')
    index={}
    for path in DECK_DIR.glob('*.apkg'):
        z,c,m=read_deck(path);members={v:k for k,v in m.items()}
        for f, in c.execute('select flds from notes'):
            f=f.split(chr(31));entry=card_visuals.select_visual(lookup,senses,f)
            match=re.search(r'<figure class="vocab-visual"><img src="([^"]+)"',f[7])
            if entry and not entry['image'].startswith('genki1-') and match and match[1] in members:
                index.setdefault(entry['image'],(path,members[match[1]],match[1]))
        z.close();c.close()
    original=card_visuals.image_bytes
    def cached(catalog,entry):
        if entry['image'] not in index:return original(catalog,entry)
        path,member,name=index[entry['image']]
        with zipfile.ZipFile(path) as archive:blob=archive.read(member)
        assert blob[:4]==b'RIFF' and blob[8:12]==b'WEBP'
        assert name=='vocab_visual_'+hashlib.sha256(blob).hexdigest()[:16]+'.webp'
        return blob
    card_visuals.image_bytes=cached
    print('Reusing',len(index),'accepted packaged illustrations',flush=True)

def hydrate():
    """Stage checksum-verified accepted artwork when iCloud originals are offline."""
    import requests,stat,concurrent.futures
    target=WORK/'templates/assets/card-visuals/images';target.mkdir(parents=True,exist_ok=True)
    entries=json.loads((ROOT/'assets/card-visuals/image-production.json').read_text())['entries']
    def one(e):
        dest=target/e['image'];expected=e['image_sha256']
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()==expected:return
        source=ROOT/'assets/card-visuals/images'/e['image']
        if not source.stat().st_flags & getattr(stat,'SF_DATALESS',0x40000000):
            data=source.read_bytes();assert hashlib.sha256(data).hexdigest()==expected,('Changed selected artwork',e['image'])
        else:
            url='https://media.githubusercontent.com/media/zacharyhalvorson/anki-decks/main/assets/card-visuals/images/'+e['image']
            response=requests.get(url,timeout=40);response.raise_for_status();data=response.content
            assert hashlib.sha256(data).hexdigest()==expected,('Downloaded artwork differs from reviewed hash',e['image'])
        dest.write_bytes(data)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(one,entries))
    print('Verified',len(entries),'selected source PNGs in template staging area',flush=True)

def stage_reading_audio():
    """Recover existing shared clips byte-for-byte when local iCloud files are offline."""
    import shutil
    target=WORK/'templates/assets/kr'
    if target.is_symlink():target.unlink()
    target.mkdir(parents=True,exist_ok=True)
    clips={}
    for path in DECK_DIR.glob('*.apkg'):
        with zipfile.ZipFile(path) as archive:
            media=json.loads(archive.read('media'))
            for key,name in media.items():
                if not name.startswith('_kr_'):continue
                blob=archive.read(key)
                assert name not in clips or clips[name]==blob,('Conflicting shared reading audio',name)
                clips[name]=blob
    for source in (ROOT/'assets/kr').glob('*.mp3'):
        if source.name not in clips:clips[source.name]=source.read_bytes()
    for name,blob in clips.items():(target/name).write_bytes(blob)
    print('Staged',len(clips),'shared reading clips without changing their bytes',flush=True)

def templates():
    import runpy,sys,os,shutil
    hydrate();stage_reading_audio();reuse_packaged_artwork()
    for source in (ROOT/'assets/card-visuals/images').glob('genki1-*.png'):
        shutil.copyfile(source,WORK/'templates/assets/card-visuals/images'/source.name)
        digest=hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        cache=ROOT/'assets/card-visuals/optimized'/(digest+'.webp')
        if cache.exists():
            target=WORK/'templates/assets/card-visuals/optimized';target.mkdir(exist_ok=True)
            shutil.copyfile(cache,target/cache.name)
    stage=WORK/'templates';(stage/'scripts').mkdir(exist_ok=True)
    (stage/'decks').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'scripts/apply_templates.py',stage/'scripts/apply_templates.py')
    links={'templates':ROOT/'templates','assets/dictionary':ROOT/'assets/dictionary','assets/_kanji_strokes.js':ROOT/'assets/_kanji_strokes.js'}
    for name in ['manifest.json','sense-overrides.json','image-production.json']:
        links['assets/card-visuals/'+name]=ROOT/'assets/card-visuals'/name
    for name,source in links.items():
        dest=stage/name
        if not dest.exists():dest.symlink_to(source,target_is_directory=source.is_dir())
    for path in DECK_DIR.glob('*.apkg'):
        dest=stage/'decks'/path.name
        if dest.exists():dest.unlink()
        os.link(path,dest)
    sys.argv=[str(stage/'scripts/apply_templates.py')]
    runpy.run_path(sys.argv[0],run_name='__main__')
    # The unmodified shared builder checks everything before each staged output.
    for path in DECK_DIR.glob('*.apkg'):
        pending=path.with_suffix('.apkg.tmp');shutil.copyfile(stage/'decks'/path.name,pending);os.replace(pending,path)
    shutil.copyfile(stage/'assets/card-visuals/image-production-report.json',ROOT/'assets/card-visuals/image-production-report.json')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['render','inventory','prepare','audio','readings','build','check','templates','hydrate'])
    args=parser.parse_args()
    globals()[args.command]()
