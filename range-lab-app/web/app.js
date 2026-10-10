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
