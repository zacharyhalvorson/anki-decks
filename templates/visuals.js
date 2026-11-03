(function () {
  var script = document.currentScript;
  var root = script && script.closest('.card');
  if (!root) return;
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
    document.body.classList.add('vocab-visual-page');
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
    root.classList.add('visual-ready');
  } else {
    document.body.classList.remove('vocab-visual-page');
  }
  var breakdown = root.querySelector('.kanji-breakdown');
  if (breakdown && !breakdown.querySelector('.k-brk') && !breakdown.textContent.trim()) breakdown.remove();
})();
