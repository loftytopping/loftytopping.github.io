// Mobile menu, CV contents highlighting, and sizing the photo to match the name block.
(function () {
  function fitPortrait() {
    document.querySelectorAll('.name-row').forEach(function (row) {
      var img = row.querySelector('.portrait');
      var text = row.querySelector(':scope > div');
      if (!img || !text) return;
      if (window.innerWidth <= 600) { img.style.width = img.style.height = ''; return; }
      img.style.width = img.style.height = '110px';
      for (var i = 0; i < 3; i++) {  // the photo's width changes the text wrap, so settle in a few passes
        var h = Math.round(text.getBoundingClientRect().height);
        h = Math.max(110, Math.min(h, 200));
        img.style.width = img.style.height = h + 'px';
      }
    });
  }
  // Event status from the visitor's own date, so "happening now" is right between site rebuilds.
  var d = new Date();
  var today = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  document.querySelectorAll('[data-start][data-end]').forEach(function (el) {
    var now = el.dataset.start <= today && today <= el.dataset.end;
    if (el.classList.contains('now-at')) { el.hidden = !now; return; }
    el.classList.toggle('now', now);
    var badge = el.querySelector('.ev-now'); if (badge) badge.hidden = !now;
    if (el.dataset.end < today && !el.classList.contains('past')) el.hidden = true;  // ended since the last build
  });
  fitPortrait();
  window.addEventListener('resize', fitPortrait);
  window.addEventListener('load', fitPortrait);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitPortrait);

  var btn = document.querySelector('.menu-toggle');
  var nav = document.querySelector('.topbar nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  var toc = document.querySelectorAll('.toc a');
  if (toc.length && 'IntersectionObserver' in window) {
    var map = {};
    toc.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          toc.forEach(function (a) { a.classList.remove('on'); });
          var a = map[e.target.id]; if (a) a.classList.add('on');
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    document.querySelectorAll('.cv-sec[id]').forEach(function (s) { obs.observe(s); });
  }
})();
