(function () {
  // Anki's <body> also has class="card". Locate our explicit key, never
  // currentScript.closest('.card'), which can resolve to that outer body.
  var keys = document.querySelectorAll('.visual-key');
  var root = keys.length ? keys[keys.length - 1].closest('div.card') : null;
  if (!root) return;
  if (root.classList.contains('image-production-answer')) return;
  var question = window.ankiVisualQuestion;
  window.ankiVisualQuestion = null;
  var key = root.querySelector('.visual-key');
  if (!question || !key || question.key !== key.textContent || Date.now() - question.time > 3600000 || question.production !== root.classList.contains('prod')) question = null;
  var visual = root.querySelector('.vocab-visual');
  if (visual) {
    root.insertBefore(visual, root.firstChild);
    root.classList.add('has-vocab-visual');
    // Keep late network/decode completion from appearing in a single frame.
    var image = visual.querySelector('img');
    if (image) {
      var requestedAt = performance.now();
      image.loading = 'eager';
      image.style.visibility = 'hidden';
      var revealImage = function () {
        if (!image.isConnected || !image.naturalWidth) return;
        var late = performance.now() - requestedAt > 80;
        if (late && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
          image.animate([{opacity: 0}, {opacity: 1}], {duration: 280, easing: 'ease-out', fill: 'both'});
        }
        image.style.visibility = '';
      };
      if (image.decode) image.decode().then(revealImage).catch(function () {});
      else if (image.complete) revealImage();
      else image.addEventListener('load', revealImage, {once: true});
    }
    var content = document.createElement('div');
    content.className = 'visual-content';
    Array.from(root.children).forEach(function (child) {
      if (child !== visual && child.tagName !== 'SCRIPT') content.appendChild(child);
    });
    root.insertBefore(content, visual.nextSibling);
    // Match the question heading's center before moving the entire answer block.
    var heading = content.querySelector(root.classList.contains('prod') ? '.front-english' : '.front-word-ruby');
    var frontSize = root.classList.contains('prod') ? 34 : 46;
    var targetCenter = root.getBoundingClientRect().top + parseFloat(getComputedStyle(root).paddingTop) + 24 + frontSize * 1.6 / 2 + 8;
    var headingRect = heading.getBoundingClientRect();
    // Production starts with the question's actual font metrics. Align its top,
    // not the center of the smaller final line box (which caused a visible jump).
    var start = root.classList.contains('prod')
      ? targetCenter - frontSize * 1.6 / 2 - headingRect.top
      : targetCenter - headingRect.top - headingRect.height / 2;
    if (question) start = root.classList.contains('prod')
      ? question.top - headingRect.top
      : question.center - headingRect.top - headingRect.height / 2;
    root.style.setProperty('--visual-content-start', start + 'px');
    var animateHint = function () {
    if (question && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      var hint = document.createElement('div');
      hint.textContent = question.hint.text;
      hint.setAttribute('aria-hidden', 'true');
      Object.assign(hint.style, {position: 'fixed', left: question.hint.left + 'px',
        top: question.hint.top + 'px', width: question.hint.width + 'px',
        height: question.hint.height + 'px', font: question.hint.font,
        color: question.hint.color, textAlign: question.hint.textAlign,
        pointerEvents: 'none', zIndex: '5'});
      document.body.appendChild(hint);
      hint.animate([{transform: 'translateY(0)'},
        {transform: 'translateY(' + (-start) + 'px)'}],
        {duration: 560, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards'});
      hint.animate([{opacity: 1}, {opacity: 0}],
        {duration: 180, easing: 'ease-out', fill: 'forwards'}).onfinish = function () { hint.remove(); };
    }
    };
    var startReveal = function () {
      if (!root.isConnected) return;
      root.classList.add('visual-ready');
      animateHint();
      if (window.ankiVisualBridge) window.ankiVisualBridge();
    };
    // Start on Anki's visible frame, not while #qa is transparent.
    var reviewer = null;
    try { if (window.require) reviewer = window.require('anki/reviewer'); } catch (_) {}
    if (reviewer && reviewer.onShownHook) reviewer.onShownHook.push(startReveal);
    else startReveal();
  }
  if (!visual && window.ankiVisualBridge) window.ankiVisualBridge();
  var breakdown = root.querySelector('.kanji-breakdown');
  if (breakdown && !breakdown.querySelector('.k-brk') && !breakdown.textContent.trim()) breakdown.remove();
})();
