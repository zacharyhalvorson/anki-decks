(function(){
  var rules = __DICTIONARY_LINKS__;
  var cs = document.currentScript;
  var root = cs && cs.closest ? cs.closest('.card') : null;
  if (!root) {
    var cards = document.querySelectorAll('.card');
    root = cards.length ? cards[cards.length - 1] : document;
  }
  var key = root.querySelector('.dictionary-key');
  var link = root.querySelector('.wordinfo-nih');
  if (!key || !link) return;
  var target = rules[(key.textContent || '').trim()];
  if (!target) return;
  var slash = target.indexOf('/');
  link.setAttribute('href', 'https://nihongo-app.com/dictionary/' +
    target.slice(0, slash + 1) + encodeURIComponent(target.slice(slash + 1)));
})();
