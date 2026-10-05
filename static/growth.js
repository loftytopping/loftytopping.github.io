// Hygroscopic growth of three aerosol types as relative humidity cycles.
// Growth factor from kappa-Kohler theory, ignoring the Kelvin term: GF = (1 + kappa * aw / (1 - aw))^(1/3), aw ~ RH.
(function () {
  var cv = document.getElementById('growth');
  if (!cv) return;
  var ctx = cv.getContext('2d');
  var out = document.getElementById('rh-readout');
  var W = 480, H = 420, PLOT_TOP = 292;
  var TYPES = [
    { name: 'ammonium sulfate', kappa: 0.61, token: '--p1' },
    { name: 'sea salt', kappa: 1.28, token: '--p2' },
    { name: 'organic', kappa: 0.1, token: '--p3' }
  ];
  var RH_MIN = 0.3, RH_MAX = 0.95, PERIOD = 14000;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function gf(kappa, rh) { return Math.cbrt(1 + kappa * rh / (1 - rh)); }

  // seeded particles so the picture is the same on every load
  var seed = 7;
  function rnd() { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }
  var parts = [];
  for (var i = 0; i < 34; i++) {
    parts.push({ x: rnd() * W, y: 14 + rnd() * (PLOT_TOP - 40), r0: 3 + rnd() * 7,
      t: TYPES[i % 3], vx: (rnd() - 0.5) * 0.12, vy: (rnd() - 0.5) * 0.08, ph: rnd() * 6.28 });
  }

  function setup() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function tok(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  // plot geometry: RH 30..95 % on x, GF 1..3 on y
  var PX0 = 44, PX1 = W - 12, PY0 = H - 26, PY1 = PLOT_TOP + 14;
  function sx(rh) { return PX0 + (rh - RH_MIN) / (RH_MAX - RH_MIN) * (PX1 - PX0); }
  function sy(g) { return PY0 - (g - 1) / 2 * (PY0 - PY1); }

  function draw(rh, dt) {
    var muted = tok('--muted'), line = tok('--line'), fg = tok('--fg');
    ctx.clearRect(0, 0, W, H);

    // particles
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      if (dt) {
        p.ph += 0.0006 * dt;
        p.x += p.vx * dt * 0.06 + Math.sin(p.ph) * 0.05;
        p.y += p.vy * dt * 0.06 + Math.cos(p.ph * 1.3) * 0.04;
        if (p.x < -40) p.x = W + 40; if (p.x > W + 40) p.x = -40;
        if (p.y < 10) p.vy = Math.abs(p.vy); if (p.y > PLOT_TOP - 30) p.vy = -Math.abs(p.vy);
      }
      var col = tok(p.t.token);
      var r = p.r0 * gf(p.t.kappa, rh);
      ctx.globalAlpha = 0.22; ctx.fillStyle = col;
      ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, 6.2832); ctx.fill();
      ctx.globalAlpha = 0.9; ctx.lineWidth = 1; ctx.strokeStyle = col; ctx.stroke();
      ctx.globalAlpha = 1; ctx.beginPath(); ctx.arc(p.x, p.y, p.r0 * 0.55, 0, 6.2832); ctx.fill();
    }

    // plot frame and grid
    ctx.strokeStyle = line; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, PLOT_TOP); ctx.lineTo(W, PLOT_TOP); ctx.stroke();
    ctx.font = '10px "JetBrains Mono", monospace'; ctx.fillStyle = muted;
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    [1, 2, 3].forEach(function (g) {
      ctx.beginPath(); ctx.moveTo(PX0, sy(g)); ctx.lineTo(PX1, sy(g)); ctx.stroke();
      ctx.fillText(g.toFixed(1), PX0 - 6, sy(g));
    });
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    [0.3, 0.5, 0.7, 0.9].forEach(function (x) { ctx.fillText(Math.round(x * 100) + '%', sx(x), PY0 + 6); });
    ctx.save(); ctx.translate(12, (PY0 + PY1) / 2); ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = 'middle'; ctx.fillText('GF', 0, 0); ctx.restore();

    // curves
    TYPES.forEach(function (t) {
      ctx.strokeStyle = tok(t.token); ctx.lineWidth = 1.6; ctx.beginPath();
      for (var x = RH_MIN; x <= RH_MAX + 1e-9; x += 0.005) {
        var y = sy(gf(t.kappa, x)); if (x === RH_MIN) ctx.moveTo(sx(x), y); else ctx.lineTo(sx(x), y);
      }
      ctx.stroke();
      ctx.fillStyle = tok(t.token);
      ctx.beginPath(); ctx.arc(sx(rh), sy(gf(t.kappa, rh)), 3.2, 0, 6.2832); ctx.fill();
    });
    ctx.strokeStyle = fg; ctx.globalAlpha = 0.35; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(sx(rh), PY1 - 4); ctx.lineTo(sx(rh), PY0); ctx.stroke();
    ctx.setLineDash([]); ctx.globalAlpha = 1;

    if (out) out.textContent = 'RH ' + Math.round(rh * 100) + '%  GF(sulfate) ' + gf(0.61, rh).toFixed(2);
  }

  setup();
  window.addEventListener('resize', setup);
  if (reduce) { draw(0.85, 0); return; }
  var last = null;
  function frame(ts) {
    var dt = last === null ? 0 : Math.min(ts - last, 50); last = ts;
    var u = 0.5 - 0.5 * Math.cos(2 * Math.PI * ((ts + 0.372 * PERIOD) % PERIOD) / PERIOD);
    draw(RH_MIN + u * (RH_MAX - RH_MIN), dt);
    requestAnimationFrame(frame);
  }
  draw(0.85, 0);
  requestAnimationFrame(frame);
})();
