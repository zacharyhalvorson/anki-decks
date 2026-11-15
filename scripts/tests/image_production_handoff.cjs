// A retained question overlay is appended after #qa on Desktop Anki.
// It must not steal initialization from the live answer.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const templates = path.resolve(__dirname, '../../templates');
const sense = '椅子|いす|chair';
let visitedAnswer = false;
const answerKey = {textContent:sense};
const answer = {
  classList:{contains:name => name === 'prod'},
  querySelector(selector) {
    if (selector === '.dictionary-key') return answerKey;
    if (selector === '.vocab-visual') {visitedAnswer=true;return null;}
    throw Error('Unexpected selector '+selector);
  }
};
const overlayKey = {textContent:sense,closest:() => {throw Error('Cloned question selected instead of live answer');}};
const source = fs.readFileSync(path.join(templates,'image_production.js'),'utf8')
  .replace('__IMAGE_PRODUCTION_RULES__',JSON.stringify({[sense]:'chair.webp'}));
vm.runInNewContext(source,{
  document:{querySelectorAll:selector => selector === '.visual-key'
    ? [{closest:() => answer}]
    : [answerKey,overlayKey]},
});
assert.ok(visitedAnswer,'Initialize live answer while question overlay remains');
const front=fs.readFileSync(path.join(templates,'visual_front.js'),'utf8');
assert.match(front,/querySelectorAll\('script, \.visual-key, \.dictionary-key'\)/);
console.log('PASS: retained question overlay cannot steal image answer initialization.');
