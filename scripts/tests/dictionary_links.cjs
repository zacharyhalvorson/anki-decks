const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const entries = JSON.parse(fs.readFileSync(path.join(root, 'assets/dictionary/nihongo-links.json')));
const rules = Object.fromEntries(entries.map(e => [[e.word,e.reading,e.meaning].join('|'),e.target]));
const source = fs.readFileSync(path.join(root,'templates/dictionary_links.js'),'utf8').replace('__DICTIONARY_LINKS__', JSON.stringify(rules));
function run(key, fallback=false) {
  let href = 'original';
  const link = {setAttribute(k,v) { assert.equal(k,'href'); href=v; }};
  const card = {querySelector(s) { return s === '.dictionary-key' ? {textContent:key} : link; }};
  const document = {currentScript:fallback?null:{closest:()=>card},querySelectorAll:()=>[card]};
  vm.runInNewContext(source, {document,encodeURIComponent});
  return href;
}
for (const e of entries) {
  const [route,...value] = e.target.split('/');
  for (const fallback of [false,true]) assert.equal(run([e.word,e.reading,e.meaning].join('|'),fallback),`https://nihongo-app.com/dictionary/${route}/${encodeURIComponent(value.join('/'))}`);
}
assert.equal(run('着く|つく|to arrive; reach'),'https://nihongo-app.com/dictionary/word/1422970');
assert.equal(run('つく|つく|(something) turns on (〜が)'),'original');
assert.equal(run('いる|いる|to exist (animate)'),'https://nihongo-app.com/dictionary/word/1577980');
assert.equal(run('やめる|やめる|to quit; stop'),'https://nihongo-app.com/dictionary/search/'+encodeURIComponent('やめる'));
for (const side of ['recognition_back','production_back']) assert.match(fs.readFileSync(path.join(root,`templates/${side}.html`),'utf8'),/class="dictionary-key" hidden>\{\{Word\}\}\|\{\{Reading\}\}\|\{\{Meaning\}\}/);
console.log(`PASS: ${entries.length} exact sense rules, both WebView contexts, both answer templates, and homograph isolation`);
