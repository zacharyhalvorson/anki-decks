const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const sense='椅子|いす|chair';
const source=fs.readFileSync(path.resolve(__dirname,'../../templates/image_production.js'),'utf8').replace('__IMAGE_PRODUCTION_RULES__',JSON.stringify({[sense]:'chair.webp'}));
for(const config of [{question:true},{question:false,narrow:true},{question:true,reduced:true}]) {
 const calls=[],hooks=[],classes=new Set(['prod']);let released=false,removedBreakdown=false;
 const breakdown={textContent:config.reduced?'chair kanji':'  ',querySelector:()=>config.reduced?{}:null,remove:()=>{removedBreakdown=true;}};
 const bounds={top:20,left:24,width:351,height:117};
 const image={getBoundingClientRect:()=>bounds,animate:(frames,options)=>calls.push({target:'image',frames,options})};
 const visual={tagName:'FIGURE',style:{},querySelector:()=>image};
 const english={},word={appendChild(){}},key={textContent:sense};
 const content={appendChild(){},animate:(frames,options)=>calls.push({target:'content',frames,options})};
 const root={isConnected:true,children:[visual,word,english],firstChild:visual,
  classList:{contains:x=>classes.has(x),add:(...xs)=>xs.forEach(x=>classes.add(x)),remove:x=>classes.delete(x)},
  querySelector:s=>({'.kanji-breakdown':breakdown,'.dictionary-key':key,'.vocab-visual':visual,'.front-english':english,'.word-block':word}[s]),insertBefore(){}};
 const start={key:sense,top:230,left:24,width:351,height:280,time:Date.now()};
 vm.runInNewContext(source,{document:{querySelectorAll:()=>[{closest:()=>root}],createElement:()=>content},
  window:{ankiImageQuestion:config.question?start:null,require:()=>({onShownHook:hooks}),
   matchMedia:q=>({matches:q.includes('reduced-motion')?!!config.reduced:!!config.narrow}),
   ankiVisualBridge:()=>{assert.ok(config.reduced||calls.length===3,'Install motion before releasing question');released=true;}},
  getComputedStyle:()=>({padding:'14px 21px'})});
 assert.equal(removedBreakdown,!config.reduced,'Remove empty kana breakdown; preserve populated kanji section');
 assert.equal(calls.length,0,'Wait for Anki shown hook');assert.equal(released,false);hooks[0]();assert.ok(released);
 if(config.reduced){assert.equal(calls.length,0);continue;}
 const picture=calls[0],block=calls[1];assert.equal(block.target,'content');
 const expected=config.question?373:187; // (question bottom - final image bottom)
 assert.equal(block.frames[0].transform,`translateY(${expected}px)`);
 assert.equal(block.frames[1].transform,'translateY(0)');
 assert.equal(block.options.duration,picture.options.duration);assert.equal(block.options.easing,picture.options.easing);assert.equal(block.options.delay,undefined);
 assert.equal(calls[2].frames[0].opacity,0);assert.equal(calls[2].frames[1].opacity,1);
}
console.log('PASS: complete answer follows image bottom on shared timeline; mobile fallback, reduced motion and handoff verified.');
