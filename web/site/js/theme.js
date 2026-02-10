/* ═══════════════════════════════════════════════════════════════════════════
   theme.js — CHIP Central theme selector
   Loaded in <head> BEFORE page renders to avoid flash of unstyled content.
   Change the THEME variable below to switch the entire site's visual style.
   ═══════════════════════════════════════════════════════════════════════════ */

// Options: 'theme-modern' (Design B, clean) or 'theme-startup' (Design A, dark hero)
var CHIP_THEME = 'theme-modern';

document.write('<link rel="stylesheet" href="css/' + CHIP_THEME + '.css">');
