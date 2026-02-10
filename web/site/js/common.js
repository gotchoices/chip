/* ═══════════════════════════════════════════════════════════════════════════
   common.js — Shared functionality for CHIP Central
   - Injects theme stylesheet from a single config point
   - Injects header/footer from includes/
   - Loads current CHIP value from local CSV data
   - Mobile nav toggle
   - Highlights active nav link
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Include header & footer ──
  function loadInclude(el) {
    var src = el.getAttribute('data-include');
    if (!src) return Promise.resolve();
    return fetch(src)
      .then(function (r) { return r.text(); })
      .then(function (html) { el.innerHTML = html; });
  }

  // Load all includes, then run post-load setup
  var includes = document.querySelectorAll('[data-include]');
  var promises = Array.prototype.map.call(includes, loadInclude);

  Promise.all(promises).then(function () {
    setupNav();
    highlightActiveNav();
  });

  // ── Mobile nav toggle ──
  function setupNav() {
    var toggle = document.querySelector('.nav-toggle');
    var nav = document.querySelector('.site-nav');
    if (toggle && nav) {
      toggle.addEventListener('click', function () {
        nav.classList.toggle('open');
      });
    }
  }

  // ── Highlight current page in nav ──
  function highlightActiveNav() {
    var page = window.location.pathname.split('/').pop() || 'index.html';
    var links = document.querySelectorAll('.site-nav a');
    links.forEach(function (a) {
      if (a.getAttribute('href') === page) {
        a.classList.add('active');
      }
    });
  }

  // ── Load CHIP value from local CSV ──
  // Reads assets/data/chip-dollar.csv and returns the latest valid value.
  // Calls window.onChipValueLoaded(value, date) if defined.
  window.loadChipValue = function () {
    return fetch('assets/data/chip-dollar.csv')
      .then(function (r) { return r.text(); })
      .then(function (text) {
        var lines = text.trim().split('\n');
        // Walk backwards to find last valid (non-NaN) value
        for (var i = lines.length - 1; i >= 1; i--) {
          var parts = lines[i].split(',');
          var date = parts[0];
          var value = parseFloat(parts[1]);
          if (!isNaN(value)) {
            // Update any elements with data-chip-value or data-chip-date
            document.querySelectorAll('[data-chip-value]').forEach(function (el) {
              el.textContent = value.toFixed(2);
            });
            document.querySelectorAll('[data-chip-date]').forEach(function (el) {
              el.textContent = date;
            });
            if (typeof window.onChipValueLoaded === 'function') {
              window.onChipValueLoaded(value, date);
            }
            return { value: value, date: date };
          }
        }
        return null;
      })
      .catch(function (err) {
        console.warn('Could not load CHIP value:', err);
        return null;
      });
  };

})();
