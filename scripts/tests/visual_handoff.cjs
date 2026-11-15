const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = name => fs.readFileSync(path.resolve(__dirname, '../../templates', name), 'utf8');
let observer, timeout, copy, disconnected = false;
const rect = {left: 20, top: 30, width: 640, height: 180};
const qa = {style: {opacity: '1'}};
const heading = {getBoundingClientRect: () => rect};
const key = {textContent: '渡る|わたる', closest: () => root};
const root = {
  isConnected: true, closest: () => qa,
  getBoundingClientRect: () => rect, addEventListener() {},
  querySelector: s => s === '.visual-key' ? key : s === '.front-english' ? null : heading,
  cloneNode() { return {style: {}, querySelectorAll: () => [], setAttribute() {}, remove() {this.removed = true;}}; }
};
const window = {MutationObserver: true};
vm.runInNewContext(source('visual_front.js'), {
  window, document: {querySelectorAll: () => [key], body: {appendChild: n => copy = n}},
  MutationObserver: class {constructor(fn) {observer = fn;} observe() {} disconnect() {disconnected = true;}},
  setTimeout: fn => {timeout = fn; return 1;}, clearTimeout() {},
  requestAnimationFrame: fn => fn(), getComputedStyle: () => ({font: '46px sans-serif'})
});
assert.equal(copy.style.visibility, 'hidden');
assert.equal(copy.style.width, '640px');
assert.equal(copy.style.maxWidth, 'none');
qa.style.opacity = '0'; observer();
assert.equal(copy.style.visibility, 'visible', 'Question persists while Anki hides #qa');
root.isConnected = false; observer();
assert.ok(!copy.removed, 'Replacement of the question must not remove the bridge');
window.ankiVisualBridge();
assert.ok(copy.removed && disconnected);
assert.equal(window.ankiVisualBridge, null);

// Run the actual answer initializer with Anki's shown-hook lifecycle.
const classes = new Set();
let released = false;
const hooks = [];
const visual = {tagName: 'FIGURE', querySelector: () => null};
const answerHeading = {getBoundingClientRect: () => ({top: 100, height: 40})};
const content = {appendChild() {}, querySelector: () => answerHeading};
const answerKey = {textContent: '渡る|わたる', closest: () => answer};
const answer = {
  isConnected: true, children: [visual], firstChild: visual,
  classList: {contains: c => classes.has(c), add: c => classes.add(c)},
  querySelector: s => s === '.visual-key' ? answerKey : s === '.vocab-visual' ? visual : null,
  insertBefore() {}, getBoundingClientRect: () => ({top: 0}), style: {setProperty() {}}
};
vm.runInNewContext(source('visuals.js'), {
  window: {require: () => ({onShownHook: hooks}), ankiVisualBridge: () => {released = true;}},
  document: {querySelectorAll: () => [answerKey], createElement: () => content},
  getComputedStyle: () => ({paddingTop: '24'})
});
assert.equal(classes.has('visual-ready'), false, 'Do not animate under Anki hidden container');
assert.equal(released, false, 'Keep question visible until answer is shown');
assert.equal(hooks.length, 1);
hooks[0]();
assert.ok(classes.has('visual-ready') && released, 'Visible answer and bridge release happen together');
// Simulate script failure: bridge expires independently of answer initialization.
timeout();
assert.ok(copy.removed);
console.log('PASS: Anki hide/replace/show handoff retains question, delays reveal, and cleans up safely.');
