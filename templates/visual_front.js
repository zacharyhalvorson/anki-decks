(function () {
  // Anki's <body> also has class="card". Locate our explicit key, never
  // currentScript.closest('.card'), which can resolve to that outer body.
  var keys = document.querySelectorAll('.visual-key');
  var root = keys.length ? keys[keys.length - 1].closest('div.card') : null;
  if (!root) return;
  if (window.ankiVisualBridge) window.ankiVisualBridge();
  // Desktop Anki sets #qa opacity to zero while loading answer scripts.
  // Keep a static question outside that container until its answer is shown.
  var qa = root.closest('#qa');
  if (qa && window.MutationObserver) {
    var copy, timer;
    var observer = new MutationObserver(function () {
      if (!root.isConnected || qa.style.opacity === '0') showCopy();
    });
    function removeCopy() {
      observer.disconnect();
      clearTimeout(timer);
      if (copy) copy.remove();
      if (window.ankiVisualBridge === removeCopy) window.ankiVisualBridge = null;
    }
    function prepareCopy() {
      if (!root.isConnected || (copy && copy.style.visibility === 'visible')) return;
      if (copy) copy.remove();
      copy = root.cloneNode(true);
      copy.querySelectorAll('script, .visual-key, .dictionary-key').forEach(function (node) { node.remove(); });
      var bounds = root.getBoundingClientRect();
      copy.setAttribute('aria-hidden', 'true');
      Object.assign(copy.style, {position: 'fixed', left: bounds.left + 'px', top: bounds.top + 'px',
        width: bounds.width + 'px', height: bounds.height + 'px', boxSizing: 'border-box',
        maxWidth: 'none', maxHeight: 'none', margin: '0', pointerEvents: 'none', zIndex: '1000', visibility: 'hidden'});
      document.body.appendChild(copy);
    }
    function showCopy() {
      if (!copy) return;
      copy.style.visibility = 'visible';
      // A failed/foreign answer must never leave an overlay blocking the page.
      if (!timer) timer = setTimeout(removeCopy, 1500);
    }
    window.ankiVisualBridge = removeCopy;
    prepareCopy();
    requestAnimationFrame(prepareCopy);
    observer.observe(qa, {childList: true, attributes: true, attributeFilter: ['style']});
  }
  var capture = function () {
    if (!root.isConnected) return;
    var prompt = root.querySelector('.image-production-prompt img');
    if (prompt && prompt.tagName === 'IMG') {
      var bounds = prompt.getBoundingClientRect();
      window.ankiImageQuestion = {key: root.querySelector('.dictionary-key').textContent,
        top:bounds.top,left:bounds.left,width:bounds.width,height:bounds.height,time:Date.now()};
      window.ankiVisualQuestion = null;
      return;
    }
    window.ankiImageQuestion = null;
    var heading = root.querySelector('.front-english, .front-word');
    var hint = root.querySelector('.hint');
    var rect = hint.getBoundingClientRect();
    var style = getComputedStyle(hint);
    window.ankiVisualQuestion = {
      key: root.querySelector('.visual-key').textContent,
      production: !!root.querySelector('.front-english'),
      top: heading.getBoundingClientRect().top,
      center: heading.getBoundingClientRect().top + heading.getBoundingClientRect().height / 2,
      time: Date.now(),
      hint: {text: hint.textContent, left: rect.left, top: rect.top, width: rect.width,
        height: rect.height, font: style.font, color: style.color, textAlign: style.textAlign}
    };
  };
  capture();
  requestAnimationFrame(capture);
  root.addEventListener('pointerdown', capture, {capture: true});
})();
