(function () {
  var root = document.currentScript.closest('.card');
  if (!root) return;
  document.body.classList.remove('vocab-visual-page');
  var capture = function () {
    if (!root.isConnected) return;
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
