(function () {
  // The handoff overlay is a cloned question outside #qa. Its dictionary key
  // must never win over the live answer when Anki replaces the card DOM.
  var keys = document.querySelectorAll('.visual-key');
  var root = keys.length ? keys[keys.length - 1].closest('div.card') : null;
  var key = root && root.querySelector('.dictionary-key');
  if (!root || !key) return;
  var rules = __IMAGE_PRODUCTION_RULES__;
  var filename = rules[key.textContent.trim()];
  if (!filename) return;
  var back = root.classList.contains('prod');
  if (!back) {
    var figure = document.createElement('figure');
    figure.className = 'image-production-prompt';
    var image = document.createElement('img');
    image.src = filename;
    image.alt = 'Name the pictured object in Japanese';
    image.loading = 'eager';
    figure.appendChild(image);
    root.insertBefore(figure, root.firstChild);
    root.classList.add('image-production-question');
    // Keep a usable English question if the client's image media is missing.
    image.onerror = function () { figure.remove(); root.classList.remove('image-production-question'); };
    return;
  }
  var visual = root.querySelector('.vocab-visual');
  if (!visual) return;
  var english = root.querySelector('.front-english');
  english.className = 'meaning';
  root.querySelector('.word-block').appendChild(english);
  root.classList.remove('prod');
  root.classList.add('image-production-answer', 'has-vocab-visual');
  root.insertBefore(visual, root.firstChild);
  // Kana-only notes store their illustration in KanjiBreakdown too. Once it
  // moves to the banner, remove the empty section just as normal cards do.
  var breakdown = root.querySelector('.kanji-breakdown');
  if (breakdown && !breakdown.querySelector('.k-brk') && !breakdown.textContent.trim()) breakdown.remove();
  var content = document.createElement('div');
  content.className = 'image-production-content';
  Array.from(root.children).forEach(function (node) {
    if (node !== visual && node.tagName !== 'SCRIPT') content.appendChild(node);
  });
  root.insertBefore(content, visual.nextSibling);
  var question = window.ankiImageQuestion;
  window.ankiImageQuestion = null;
  if (!question || question.key !== key.textContent || Date.now() - question.time > 3600000) question = null;
  function reveal() {
    if (!root.isConnected) return;
    root.classList.add('visual-ready');
    var image = visual.querySelector('img');
    function releaseQuestion() { if (window.ankiVisualBridge) window.ankiVisualBridge(); }
    if (!image || !image.animate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      releaseQuestion();
      return;
    }
    var bounds = image.getBoundingClientRect(), style = getComputedStyle(image);
    // Reserve the final compact banner while the original question image shrinks.
    visual.style.height = bounds.height + 'px';
    var narrow = window.matchMedia('(max-width: 480px)').matches;
    var start = question || {top: bounds.top + (narrow ? 24 : 40), left: bounds.left,
      width: bounds.width, height: narrow ? 280 : 320};
    // Every answer section follows the image's bottom edge, preserving the final
    // image-to-word gap throughout the shrink. Use one easing and timeline for
    // both motions, not a delayed 16px fade-in at the final answer position.
    var contentOffset = (start.top + start.height) - (bounds.top + bounds.height);
    var motion = {duration:440,easing:'cubic-bezier(.22,1,.36,1)'};
    image.animate([
      {transform: 'translate(' + (start.left-bounds.left) + 'px,' + (start.top-bounds.top) + 'px)', width:start.width+'px',height:start.height+'px',padding:'0px'},
      {transform:'translate(0,0)',width:bounds.width+'px',height:bounds.height+'px',padding:style.padding}
    ], motion);
    content.animate([{transform:'translateY(' + contentOffset + 'px)'},{transform:'translateY(0)'}], motion);
    content.animate([{opacity:0},{opacity:1}], {duration:160,easing:'ease-out'});
    // Both first animation frames are installed before the retained question is removed.
    releaseQuestion();
  }
  // Native Anki plays the WordAudio field when showing the answer. Do not also click
  // its replay link here: doing so would play the same recording twice.
  var reviewer;
  try { if (window.require) reviewer=window.require('anki/reviewer'); } catch(e) {}
  if (reviewer && reviewer.onShownHook) reviewer.onShownHook.push(reveal);
  else requestAnimationFrame(reveal);
})();
