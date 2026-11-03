// Run the actual preview controller without a browser; catch missing packaged image files.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const page = fs.readFileSync(path.join(__dirname, 'build/preview.html'), 'utf8');
const script = page.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements = Object.fromEntries(['word', 'direction', 'images', 'night', 'card', 'flip'].map(id => [id, { value: '', checked: false, add() {} }]));
elements.direction.value = 'Recognition';
elements.images.checked = true;
vm.runInNewContext(script, {
  document: { getElementById: id => elements[id] },
  Image: function() {},
  Option: function(text, value) { this.value = value; }
});
let count = 0;
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, '../../assets/card-visuals/manifest.json'), 'utf8'));
for (const word of [...new Set(manifest.filter(e => page.includes('\"word\": \"' + e.word + '\"')).map(e => e.word)), '落ち込む']) {
  for (const direction of ['Recognition', 'Production']) {
    elements.word.value = word;
    elements.direction.value = direction;
    elements.word.onchange();
    assert(!elements.card.srcdoc.includes('<figure class="vocab-visual">'));
    elements.flip.onclick();
    const doc = elements.card.srcdoc;
    const image = doc.match(/<figure class="vocab-visual"><img src="([^"]+)"/);
    if (word === '落ち込む') {
      assert.equal(image, null);
    } else {
      assert(image, word);
      const bytes = fs.readFileSync(path.join(__dirname, 'build/media', image[1]));
      assert.equal(bytes.subarray(0, 4).toString(), 'RIFF');
      assert.equal(bytes.subarray(8, 12).toString(), 'WEBP');
      assert(bytes.length > 1000);
      count++;
    }
  }
}
console.log(`PASS: ${count} illustrated answers reference valid packaged WebPs; all fronts and both control answers have no images.`);
