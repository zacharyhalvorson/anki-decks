(function(){
  var NS = 'http://www.w3.org/2000/svg';
  var KANJI_RE = /[㐀-鿿豈-﫿々]/;
  function el(tag, attrs){ var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function txt(n){ return n ? (n.textContent || '').replace(/\s+/g, ' ').trim() : ''; }
  function stop(e){ e.stopPropagation(); }
  function guard(node){ node.addEventListener('click', stop, false); node.addEventListener('touchend', stop, false); }
  // scope everything to the card this script lives in (falls back to the last card on the page)
  var root = null, cs = document.currentScript;
  if (cs && cs.closest) root = cs.closest('.card');
  if (!root) { var cards = document.querySelectorAll('.card'); root = cards.length ? cards[cards.length - 1] : document; }

  /* ---- align a kana reading to the kanji runs of a word: お願いします + おねがいします -> お<ruby>願<rt>ねが</rt></ruby>います ---- */
  function toHira(s){ return s.replace(/[ァ-ヶ]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 0x60); }); }
  function isKanji(c){ return KANJI_RE.test(c); }
  function isKana(c){ return /[ぁ-ゟ゠-ヿ]/.test(c); }
  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function alignFurigana(word, reading){
    reading = (reading || '').replace(/\s+/g, '');
    if (word.indexOf('(') < 0) reading = reading.replace(/[（(][^)）]*[)）]/g, '');
    if (word.indexOf('/') < 0 && reading.indexOf('/') >= 0) reading = reading.split('/')[0];
    var hira = toHira(reading);
    // split the word into runs: kanji / kana / other
    var runs = [], i, c, t, cur = null;
    for (i = 0; i < word.length; i++) {
      c = word.charAt(i); t = isKanji(c) ? 'k' : (isKana(c) ? 'a' : 'o');
      if (c === '々' && cur && cur.t === 'k') t = 'k';
      if (cur && cur.t === t) cur.s += c; else { cur = {t:t, s:c}; runs.push(cur); }
    }
    var kanjiRuns = 0; for (i = 0; i < runs.length; i++) if (runs[i].t === 'k') kanjiRuns++;
    if (!kanjiRuns) return null;
    var pat = '^';
    for (i = 0; i < runs.length; i++) {
      if (runs[i].t === 'k') pat += '(.+?)';
      else if (runs[i].t === 'a') pat += esc(toHira(runs[i].s));
      else pat += '(?:' + esc(runs[i].s) + ')?';
    }
    pat += '$';
    var m = hira.match(new RegExp(pat));
    if (!m) return null;
    var out = [], gi = 1, pos = 0;
    for (i = 0; i < runs.length; i++) {
      if (runs[i].t === 'k') {
        // take the kana slice from the original reading (keeps katakana if it was katakana)
        var idx = hira.indexOf(m[gi], pos); if (idx < 0) return null;
        out.push({kanji: runs[i].s, kana: reading.substr(idx, m[gi].length)});
        pos = idx + m[gi].length; gi++;
      } else { out.push({text: runs[i].s}); if (runs[i].t === 'a') pos += runs[i].s.length; }
    }
    return out;
  }
  function renderFurigana(container, word, reading){
    var parts = alignFurigana(word, reading);
    if (!parts) return false;
    while (container.firstChild) container.removeChild(container.firstChild);
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].kanji) {
        var rb = document.createElement('ruby'); rb.appendChild(document.createTextNode(parts[i].kanji));
        var rt = document.createElement('rt'), sp = document.createElement('span'); sp.textContent = parts[i].kana; rt.appendChild(sp); rb.appendChild(rt);
        container.appendChild(rb);
      } else container.appendChild(document.createTextNode(parts[i].text));
    }
    return true;
  }
  function wrapRt(rt){ if (rt && !rt.querySelector('span')) { var sp = document.createElement('span'); sp.textContent = rt.textContent; while (rt.firstChild) rt.removeChild(rt.firstChild); rt.appendChild(sp); } }

  /* ---- 1. furigana over the word: only over the kanji; dropped entirely when it adds nothing ---- */
  var ruby = root.querySelector('.front-word-ruby ruby');
  if (ruby) {
    var rt = ruby.querySelector('rt'), base = '', c;
    for (c = ruby.firstChild; c; c = c.nextSibling) if (!(c.nodeType === 1 && c.tagName === 'RT')) base += c.textContent || '';
    base = base.trim();
    var reading = txt(rt);
    if (!rt || !KANJI_RE.test(base) || reading === base || !reading) { if (rt) rt.parentNode.removeChild(rt); }
    else if (!renderFurigana(ruby.parentNode, base, reading)) { wrapRt(rt); /* couldn't align: keep the whole-word reading, centred */ }
  }

  /* ---- 2. audio tap targets must never reach the card's tap gestures ---- */
  var taps = root.querySelectorAll('.tap-play, .tap-play-ex, .wordinfo-nih');
  for (var i = 0; i < taps.length; i++) guard(taps[i]);

  /* ---- 3. re-lay out each kanji breakdown entry (field markup stays unchanged) ---- */
  var kb = root.querySelector('.kanji-breakdown');
  if (kb && !kb.classList.contains('kb-v2')) {
    var brks = kb.querySelectorAll('.k-brk');
    for (var b = 0; b < brks.length; b++) relayout(brks[b]);
    kb.classList.add('kb-v2');
  }

  function relayout(brk){
    var ch = txt(brk.querySelector('.k-char'));
    if (!ch) return;
    var link = brk.querySelector('.k-head a');
    var href = (link && link.getAttribute('href')) || ('https://nihongo-app.com/dictionary/kanji/' + ch);
    var strokes = '', jlpt = '';
    var stats = brk.querySelectorAll('.k-stat');
    for (var s = 0; s < stats.length; s++) {
      var lab = txt(stats[s].querySelector('.k-stat-l')).toLowerCase(), v = txt(stats[s].querySelector('.k-stat-v'));
      if (lab.indexOf('stroke') === 0) strokes = v; else if (lab.indexOf('jlpt') === 0) jlpt = v;
    }
    var meanText = txt(brk.querySelector('.k-mean'));
    var readings = brk.querySelectorAll('.k-reading');

    var head = document.createElement('div'); head.className = 'k-head2';
    var box = document.createElement('div'); box.className = 'k-box'; box.setAttribute('data-kanji', ch); box.setAttribute('role', 'button');
    var fb = document.createElement('span'); fb.className = 'k-fallback'; fb.textContent = ch; box.appendChild(fb);
    var play = document.createElement('span'); play.className = 'k-play';
    play.innerHTML = '<svg viewBox="0 0 12 12"><path d="M3.6 2.2 L10 6 L3.6 9.8 Z" fill="currentColor"/></svg>';
    box.appendChild(play);
    head.appendChild(box);

    var col = document.createElement('div'); col.className = 'k-readings';
    var st = document.createElement('span'); st.className = 'k-stats2';
    var nih = document.createElement('a'); nih.className = 'k-nih'; nih.href = href; nih.textContent = '語'; st.appendChild(nih);
    if (strokes) { var sv = document.createElement('span'); sv.className = 'k-sv'; sv.innerHTML = strokes + '<span class="k-unit">画</span>'; st.appendChild(sv); }
    if (jlpt) { var jv = document.createElement('span'); jv.className = 'k-sv'; jv.textContent = jlpt; st.appendChild(jv); }
    col.appendChild(st);
    for (var r = 0; r < readings.length; r++) {
      var src = readings[r], label = src.querySelector('.k-label');
      var row = document.createElement('div'); row.className = 'k-reading2';
      var lab2 = document.createElement('span'); lab2.className = 'k-lab'; lab2.textContent = txt(label).replace(/:$/, ''); row.appendChild(lab2);
      var vals = document.createElement('span'); vals.className = 'k-vals';
      var n = src.firstChild;
      while (n) { var next = n.nextSibling; if (n !== label) vals.appendChild(n); n = next; }
      row.appendChild(vals); col.appendChild(row);
    }
    head.appendChild(col);

    var mean = document.createElement('div'); mean.className = 'k-mean2'; mean.textContent = meanText;

    while (brk.firstChild) brk.removeChild(brk.firstChild);
    brk.appendChild(head); brk.appendChild(mean);
    guard(box); guard(nih);
    box.addEventListener('click', function(){ animate(box); }, false);
  }

  /* ---- 4. stroke-order boxes (KanjiVG paths from _kanji_strokes.js) ---- */
  function buildBox(box){
    var strokes = window.KANJI_STROKES[box.getAttribute('data-kanji')];
    if (!strokes || !strokes.length) return;
    var svg = el('svg', {viewBox:'-7 -7 123 123', 'class':'k-svg', 'aria-hidden':'true'});
    var grid = el('g', {'class':'k-grid'});
    grid.appendChild(el('line', {x1:54.5, y1:-5, x2:54.5, y2:114}));
    grid.appendChild(el('line', {x1:-5, y1:54.5, x2:114, y2:54.5}));
    svg.appendChild(grid);
    var ghost = el('g', {'class':'k-ghost'}), ink = el('g', {'class':'k-ink'}), paths = [];
    for (var i = 0; i < strokes.length; i++) {
      ghost.appendChild(el('path', {d:strokes[i]}));
      var p = el('path', {d:strokes[i]}); ink.appendChild(p); paths.push(p);
    }
    svg.appendChild(ghost); svg.appendChild(ink);
    var dot = el('circle', {'class':'k-dot', r:5.2, cx:-20, cy:-20});
    svg.appendChild(dot);
    box.insertBefore(svg, box.firstChild);
    box.classList.add('has-svg');
    box._k = {paths:paths, dot:dot, raf:0, timer:0};
  }
  function cancel(box){
    var s = box._k; if (!s) return;
    if (s.raf) cancelAnimationFrame(s.raf); s.raf = 0;
    if (s.timer) clearTimeout(s.timer); s.timer = 0;
    box.classList.remove('animating'); box.classList.remove('done');
  }
  function animate(box){
    var s = box._k; if (!s) return;
    cancel(box);
    var lens = [], i, p;
    for (i = 0; i < s.paths.length; i++) { lens.push(s.paths[i].getTotalLength()); }
    for (i = 0; i < s.paths.length; i++) { p = s.paths[i]; p.style.strokeDasharray = lens[i] + ' ' + lens[i]; p.style.strokeDashoffset = lens[i]; }
    box.classList.add('animating');
    var idx = 0, t0 = 0, GAP = 70;
    function dur(len){ return Math.max(170, 90 + len * 4.6); }
    function ease(t){ return 1 - Math.pow(1 - t, 1.5); }
    function step(ts){
      if (!t0) t0 = ts;
      var q = s.paths[idx], len = lens[idx], t = Math.min(1, (ts - t0) / dur(len)), e = ease(t);
      q.style.strokeDashoffset = len * (1 - e);
      var pt = q.getPointAtLength(len * e);
      s.dot.setAttribute('cx', pt.x); s.dot.setAttribute('cy', pt.y);
      if (t < 1) { s.raf = requestAnimationFrame(step); return; }
      idx++; t0 = 0;
      if (idx < s.paths.length) {
        s.timer = setTimeout(function(){ s.timer = 0; s.raf = requestAnimationFrame(step); }, GAP);
      } else {
        box.classList.remove('animating'); box.classList.add('done');
        s.timer = setTimeout(function(){ s.timer = 0; box.classList.remove('done'); }, 650);
      }
    }
    var p0 = s.paths[0].getPointAtLength(0); s.dot.setAttribute('cx', p0.x); s.dot.setAttribute('cy', p0.y);
    s.raf = requestAnimationFrame(step);
  }
  var tries = 0;
  function fill(){
    if (window.KANJI_STROKES) {
      var boxes = root.querySelectorAll('.k-box:not(.has-svg)');
      for (var i = 0; i < boxes.length; i++) buildBox(boxes[i]);
    } else if (tries++ < 30) { setTimeout(fill, 100); }   // external asset may still be loading
  }
  fill();
})();
