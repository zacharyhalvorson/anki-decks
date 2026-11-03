/* Tap guard for the ANSWER side: once the answer is showing, a tap on the card must never reach AnkiMobile's tap zones
   (which would answer the card and move to the next one). Only the buttons under the card move on.
   Inlined into both back templates. The fronts do NOT carry it: tapping the question still flips to the answer.
   AnkiMobile's tap detection is closed source, so three layers are used together:
   1. class "tappable" on everything inside the card, the full-screen .tap-shield and the card's ancestors up to <html>
      (AnkiMobile hands a tap on such an element to the page instead of acting on it);
   2. an onclick attribute on the card wrapper and the shield (the same rule, as documented for older builds);
   3. taps (click, and touchend of an unmoved single touch) are stopped at the wrapper, the shield and <html>,
      so they never bubble to a listener on body / document / window.
   Scrolls and swipes are left alone, and so are links, scripted clicks and the audio / stroke-order tap targets
   inside the card.
   The page-level listeners are added once and do nothing while the side on screen is not a guarded one
   (no .card[data-notap]), so the question side and other note types keep their normal tap behaviour. */
(function(){
  var SEL = '.card[data-notap]';
  function ours(){ return !!document.querySelector(SEL); }
  function tag(n){ if (n && n.classList && !n.classList.contains('tappable')) n.classList.add('tappable'); }
  // the card's ancestors (<html>, <body>, the app's container) outlive the card on some clients: mark the class as
  // ours there so it can be taken back when another note type is on screen
  function tagPage(){
    var w = document.querySelector(SEL), n = w && w.parentNode;
    for (; n && n.nodeType === 1; n = n.parentNode) if (!n.classList.contains('tappable')) { n.classList.add('tappable'); n.setAttribute('data-notap-page', ''); }
  }
  function untagPage(){
    var p = document.querySelectorAll('[data-notap-page]');
    for (var i = 0; i < p.length; i++) { p[i].classList.remove('tappable'); p[i].removeAttribute('data-notap-page'); }
  }
  var st = window.__tapGuard || (window.__tapGuard = {moved: true, sx: 0, sy: 0, page: false});
  function stopTap(e){
    if (!ours()) return;
    if (e.isTrusted === false) return;               // scripted clicks (the word block clicking the hidden audio button) pass as before
    if (e.type === 'touchend' && st.moved) return;   // a scroll or a swipe, not a tap
    e.stopPropagation();
  }
  function shieldNode(n){
    if (!n || n.__notap) return;
    n.__notap = 1;
    n.addEventListener('touchend', stopTap, false);
    n.addEventListener('click', stopTap, false);
  }

  // this render: tag what is on the card now and put the stoppers on the wrapper and the shield
  var all = document.querySelectorAll(SEL + ', ' + SEL + ' *, .tap-shield');
  for (var i = 0; i < all.length; i++) tag(all[i]);
  var tops = document.querySelectorAll(SEL + ', .tap-shield');
  for (i = 0; i < tops.length; i++) shieldNode(tops[i]);
  tagPage();

  if (st.page) return;
  st.page = true;
  // capture phase on window: runs before anything else sees the touch
  window.addEventListener('touchstart', function(e){
    if (!ours()) { untagPage(); st.moved = true; return; }
    // nodes built after the render (stroke-order SVGs, example rows) get the class the moment they are touched
    var n = e.target, w = n && n.closest ? n.closest(SEL) : null;
    for (; w && n && n !== w; n = n.parentNode) tag(n);
    tagPage();
    var t = e.touches && e.touches[0];
    if (!t || e.touches.length > 1) { st.moved = true; return; }
    st.sx = t.clientX; st.sy = t.clientY; st.moved = false;
  }, {capture: true, passive: true});
  window.addEventListener('touchmove', function(e){
    var t = e.touches && e.touches[0];
    if (!t || Math.abs(t.clientX - st.sx) > 12 || Math.abs(t.clientY - st.sy) > 12) st.moved = true;
  }, {capture: true, passive: true});
  window.addEventListener('touchcancel', function(){ st.moved = true; }, {capture: true, passive: true});
  shieldNode(document.documentElement);
  // keep the classes in step with the page: tag nodes as they are added to the card, and give <html>/<body> back
  // as soon as the card on screen is no longer one of these
  if (window.MutationObserver) {
    new MutationObserver(function(recs){
      if (!ours()) { untagPage(); return; }
      for (var r = 0; r < recs.length; r++) {
        var added = recs[r].addedNodes;
        for (var a = 0; a < added.length; a++) {
          var n = added[a];
          if (n.nodeType !== 1 || !n.closest || !n.closest(SEL)) continue;
          tag(n);
          var kids = n.querySelectorAll('*');
          for (var k = 0; k < kids.length; k++) tag(kids[k]);
        }
      }
      tagPage();
    }).observe(document.documentElement, {childList: true, subtree: true});
  }
})();
