// Anki can evaluate card scripts without a currentScript inside the card.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const templates = path.resolve(__dirname, '../../templates');
for (const detached of [null, {closest: () => null}, {closest: () => ({querySelector: () => ({textContent: 'outer-body-key'})})}]) {
  for (const file of ['visual_front.js', 'visuals.js']) {
    let answerVisited = false;
    const rect = {top: 10, height: 20, left: 0, width: 100};
    const heading = {getBoundingClientRect: () => rect};
    const hint = {...heading, textContent: 'Question'};
    const key = {textContent: '運ぶ|はこぶ', closest: selector => { assert.equal(selector, 'div.card'); return root; }};
    const root = {
      isConnected: true,
      closest: () => null,
      classList: {contains: () => false},
      addEventListener() {},
      querySelector(selector) {
        if (selector === '.visual-key') return key;
        if (selector === '.hint') return hint;
        if (selector === '.front-english, .front-word') return heading;
        if (selector === '.vocab-visual') answerVisited = true;
        return null;
      }
    };
    const window = {};
    vm.runInNewContext(fs.readFileSync(path.join(templates, file), 'utf8'), {
      document: {currentScript: detached, querySelectorAll: () => [key], body: {classList: {remove() {}}}},
      window, requestAnimationFrame: fn => fn(), getComputedStyle: () => ({font: '16px sans-serif'})
    });
    if (file === 'visual_front.js') assert.equal(window.ankiVisualQuestion.key, key.textContent);
    else assert.ok(answerVisited, 'Answer initialization must find the actual card');
  }
}
const css = fs.readFileSync(path.join(templates, 'visuals.css'), 'utf8');
assert.ok(!/visibility\s*:\s*hidden/.test(css), 'CSS must not hide cards while awaiting JavaScript');
assert.ok(!css.includes('body.vocab-visual-page'), 'Flipping must not change Anki body margins');
assert.match(css, /animation: visual-prepare-fallback 700ms step-end both/);
assert.match(css, /@keyframes visual-prepare-fallback \{ from \{ opacity: 0; \} to \{ opacity: 1; \} \}/);
assert.match(css, /\.card\.visual-ready \.vocab-visual img \{\s*animation: visual-entrance/);
console.log('PASS: detached Anki script contexts, bounded preparation fallback, and entrance gated on ready.');
