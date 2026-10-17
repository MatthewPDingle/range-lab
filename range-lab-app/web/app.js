// Range Lab app shell: the content area scrolls instead of the window, so reset it when switching tabs.
(function () {
  var main = document.querySelector('main');
  var tabs = document.getElementById('tabs');
  if (!main || !tabs) return;
  tabs.addEventListener('click', function () {
    main.scrollTop = 0;
    document.querySelectorAll('.stage, .rail, .ctl, .lens-head, .lens-blocks, .drill-home > .panel, .method > .panel').forEach(function (el) { el.scrollTop = 0; });
  });
})();

// Unfolded screen: keep the page tabs on the header row. If the labels would overflow (fonts differ by phone),
// tighten them a step at a time; only if even the tightest step overflows do they wrap below the title.
(function () {
  var top = document.querySelector('.top-in');
  var tabs = document.getElementById('tabs');
  if (!top || !tabs) return;
  var steps = ['fit1', 'fit2', 'fit3'];
  var over = function () { return tabs.scrollWidth > tabs.clientWidth + 1; };
  function fit() {
    top.classList.remove('fit1', 'fit2', 'fit3', 'fitwrap');
    if (!window.matchMedia('(min-width:600px)').matches) return;
    for (var i = 0; i < steps.length && over(); i++) top.classList.add(steps[i]);
    if (over()) { top.classList.remove('fit1', 'fit2', 'fit3'); top.classList.add('fitwrap'); }
  }
  fit();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  // refit whenever the header row changes width (fold, unfold, rotation, split screen)
  var w = 0;
  if (window.ResizeObserver) new ResizeObserver(function () { if (top.clientWidth !== w) { w = top.clientWidth; fit(); } }).observe(top);
  else window.addEventListener('resize', fit);
})();
