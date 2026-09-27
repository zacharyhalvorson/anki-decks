(function(){
  var NS = 'http://www.w3.org/2000/svg';
  var KANJI_RE = /[㐀-鿿豈-﫿々]/;
  function el(tag, attrs){ var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function txt(n){ return n ? (n.textContent || '').replace(/\s+/g, ' ').trim() : ''; }
  function stop(e){ e.stopPropagation(); }
  function guard(node){ node.addEventListener('click', stop, false); node.addEventListener('touchend', stop, false); }
  /* run fn on a tap. iOS drops the click after a touch that stops a momentum scroll or that it takes for a double-tap,
     so on touch devices we act on touchend of an unmoved touch and suppress the synthetic click; mouse/desktop use click */
  function tap(node, fn){
    var sx = 0, sy = 0, moved = true, handled = false;
    node.addEventListener('touchstart', function(e){ var t = e.touches[0]; if (!t || e.touches.length > 1) { moved = true; return; } sx = t.clientX; sy = t.clientY; moved = false; handled = false; }, {passive: true});
    node.addEventListener('touchmove', function(e){ var t = e.touches[0]; if (!t || Math.abs(t.clientX - sx) > 12 || Math.abs(t.clientY - sy) > 12) moved = true; }, {passive: true});
    node.addEventListener('touchend', function(e){ if (moved) return; moved = true; handled = true; if (e.cancelable) e.preventDefault(); fn(); }, {passive: false});
    node.addEventListener('touchcancel', function(){ moved = true; }, {passive: true});
    node.addEventListener('click', function(){ if (handled) { handled = false; return; } fn(); }, false);
  }
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
  function fk(kanji, kana){
    var s = document.createElement('span'); s.className = 'fk'; s.appendChild(document.createTextNode(kanji));
    var r = document.createElement('span'); r.className = 'fr'; r.textContent = kana; s.appendChild(r);
    return s;
  }
  function renderFurigana(container, word, reading){
    var parts = alignFurigana(word, reading);
    if (!parts) return false;
    while (container.firstChild) container.removeChild(container.firstChild);
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].kanji) container.appendChild(fk(parts[i].kanji, parts[i].kana));
      else container.appendChild(document.createTextNode(parts[i].text));
    }
    return true;
  }
  function renderWhole(container, word, reading){
    while (container.firstChild) container.removeChild(container.firstChild);
    if (reading) container.appendChild(fk(word, reading)); else container.appendChild(document.createTextNode(word));
  }

  /* ---- 1. furigana over the word: only over the kanji, hung above the glyphs so the word sits exactly where it does on the front ---- */
  var fw = root.querySelector('.front-word-ruby');
  if (fw) {
    var baseEl = fw.querySelector('.fw-base'), readEl = fw.querySelector('.fw-read');
    var base = txt(baseEl), reading = txt(readEl);
    if (!KANJI_RE.test(base) || reading === base || !reading) renderWhole(fw, base, '');
    else if (!renderFurigana(fw, base, reading)) renderWhole(fw, base, reading);
  }

  /* ---- 2. audio tap targets must never reach the card's tap gestures ---- */
  var taps = root.querySelectorAll('.tap-play, .tap-play-ex, .wordinfo-nih');
  for (var i = 0; i < taps.length; i++) guard(taps[i]);

  /* ---- 2b. example sentences: the fields may hold two sentences separated by <hr class="ex-sep">.
     Re-lay them out as list items (.ex-item = Japanese + English + its own clip); the WHOLE item,
     padding included, is the tap target, and nothing inside the red card ever reaches Anki's tap gestures ---- */
  var ex = root.querySelector('.example');
  if (ex && !ex.classList.contains('ex-v2')) {
    var splitAtHr = function(node){
      var groups = [[]]; if (!node) return groups;
      var n = node.firstChild;
      while (n) { var nx = n.nextSibling; if (n.nodeType === 1 && n.tagName === 'HR') groups.push([]); else groups[groups.length - 1].push(n); n = nx; }
      return groups;
    };
    var jaG = splitAtHr(ex.querySelector('.example-ja')), enG = splitAtHr(ex.querySelector('.example-en'));
    var auds = ex.querySelectorAll('audio'), items = [], g, k;
    for (g = 0; g < jaG.length; g++) {
      var item = document.createElement('div'); item.className = 'ex-item'; item.setAttribute('role', 'button');
      var ja = document.createElement('div'); ja.className = 'example-ja';
      for (k = 0; k < jaG[g].length; k++) ja.appendChild(jaG[g][k]);
      item.appendChild(ja);
      if (enG[g]) { var en = document.createElement('div'); en.className = 'example-en'; for (k = 0; k < enG[g].length; k++) en.appendChild(enG[g][k]); item.appendChild(en); }
      if (auds[g]) item.appendChild(auds[g]);
      items.push(item);
    }
    while (ex.firstChild) ex.removeChild(ex.firstChild);
    ex.removeAttribute('onclick'); ex.onclick = null;
    ex.classList.remove('tap-play-ex'); ex.classList.add('ex-v2');
    var playItem = function(item){
      var all = ex.querySelectorAll('audio'), mine = item.querySelector('audio');
      for (var a = 0; a < all.length; a++) if (all[a] !== mine) { try { all[a].pause(); all[a].currentTime = 0; } catch (e) {} }
      if (mine) { try { mine.currentTime = 0; } catch (e) {} var pr = mine.play(); if (pr && pr.catch) pr.catch(function(){}); }
    };
    for (g = 0; g < items.length; g++) {
      ex.appendChild(items[g]); guard(items[g]);
      (function(it){ tap(it, function(){ playItem(it); }); })(items[g]);
    }
  }

  /* ---- 3. re-lay out each kanji breakdown entry (field markup stays unchanged) ---- */
  var kb = root.querySelector('.kanji-breakdown');
  if (kb && !kb.classList.contains('kb-v2')) {
    var brks = kb.querySelectorAll('.k-brk');
    for (var b = 0; b < brks.length; b++) relayout(brks[b]);
    kb.classList.add('kb-v2');

    /* ---- 3b. tappable on/kun readings: each .k-r plays `_kr_<hex of the hiragana reading>.mp3`
       (a _-prefixed template media file; okurigana marks, dots and hyphens are dropped, katakana -> hiragana).
       The whole head row swallows taps so a near miss never flips the card. ---- */
    var krAudio = null;
    var krFile = function(t){
      var sp = toHira(t.replace(/[-.()（）\s‐－]/g, '')), hex = '';
      if (!sp || !/^[ぁ-ゖー]+$/.test(sp)) return null;
      for (var i = 0; i < sp.length; i++) hex += ('0000' + sp.charCodeAt(i).toString(16)).slice(-4);
      return '_kr_' + hex + '.mp3';
    };
    var playKr = function(node, file){
      if (!krAudio) { krAudio = document.createElement('audio'); krAudio.setAttribute('preload', 'none'); krAudio.style.display = 'none'; root.appendChild(krAudio); }
      var others = root.querySelectorAll('.example audio');
      for (var o = 0; o < others.length; o++) { try { others[o].pause(); } catch (e) {} }
      var on = kb.querySelectorAll('.k-r.playing'); for (var q = 0; q < on.length; q++) on[q].classList.remove('playing');
      node.classList.add('playing'); setTimeout(function(){ node.classList.remove('playing'); }, 700);
      try { krAudio.pause(); krAudio.src = file; krAudio.currentTime = 0; } catch (e) {}
      var pr = krAudio.play(); if (pr && pr.catch) pr.catch(function(){});
    };
    var krs = kb.querySelectorAll('.k-r');
    for (var r2 = 0; r2 < krs.length; r2++) (function(node){
      var file = krFile(txt(node)); if (!file) return;
      node.classList.add('k-r-tap'); node.setAttribute('role', 'button');
      guard(node); tap(node, function(){ playKr(node, file); });
    })(krs[r2]);
    var heads = kb.querySelectorAll('.k-head2'); for (var h2 = 0; h2 < heads.length; h2++) guard(heads[h2]);
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
    tap(box, function(){ animate(box); });
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
    if (!box._k && window.KANJI_STROKES) buildBox(box);   // asset arrived after this box was laid out
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
    } else if (tries++ < 150) { setTimeout(fill, tries < 20 ? 50 : 200); }   // external asset may still be loading (waits up to ~27 s)
  }
  fill();
  // if the asset script is still in flight, fill as soon as it lands (covers WebViews that load it asynchronously)
  var ks = document.querySelectorAll('script[src*="_kanji_strokes"]');
  for (var si = 0; si < ks.length; si++) ks[si].addEventListener('load', fill, false);
})();
