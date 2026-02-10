# Web Port: chipcentral.net (WordPress -> Static HTML/JS)

## Open Questions

- [x] **Q1: Hosting & Deployment** — RESOLVED: Deploy to gotchoices.org droplet (same host
      as mychips.org) via scp-based publish script.  Uses env var CHIPCENTRAL_WEB_DEPLOY
      (e.g. user@host:/path/to/webroot).  Digital Ocean chipcentral.net droplet will be
      retired; DNS will point chipcentral.net to the gotchoices.org droplet.

- [x] **Q2: CHIP Value Display** — RESOLVED: Self-contained on chipcentral.net.
      A fetchValue script pulls chip-dollar.csv and chip.json from mychips.org (source of
      truth) and stores local copies.  The D3 chart is hosted locally, reads local CSV.
      Home page headline value derived from the latest CSV row.  Sites stay independent.

- [x] **Q3: Contact Form** — RESOLVED: Simple mailto: link on a contact page, matching the
      pattern used on gotchoices.org and mychips.org (e.g. mailto:info@chipcentral.net).

- [x] **Q4: Available Bounties** — RESOLVED: Drop bounty program and language entirely.
      Site is now purely informative.  Replace "Get Involved" / bounties content with an
      invitation to contact us for research collaboration, alluding to "possible funding"
      for bona fide research participants.

- [x] **Q5: Design Direction** — RESOLVED: Design B (clean modern) selected as primary.
      CSS is theme-swappable: change `theme-modern.css` to `theme-startup.css` in any
      HTML file's `<link>` tag to switch to Design A (dark hero / Startupzy style).

---

## Pages to Port

- [x] **Home / Landing Page** — `index.html`: Hero, dynamic CHIP value card,
      publications preview, What's a CHIP brief, research CTA, FAQ accordion
- [x] **What's a CHIP?** — `chip.html`: Founder's message, CHIP definition, MyCHIPs
      overview, links to gotchoices.org
- [x] **Publications** — `publications.html`: Links to GitHub repo (PDF, code, data)
      for white paper, ICT study, reproduction, and workbench
- [x] **CHIP Value Today** — `value.html`: Explanatory text + local D3 chart reading
      from local chip-dollar.csv (fetched from mychips.org)
- [x] **FAQ** — `faq.html`: Expanded from 3 to 8 Q&A items with accordion UI
- [x] **Contact** — `contact.html`: mailto link + related project cards
- [x] **Research Invitation** — CTA banner on index.html and language on chip.html
      and contact.html (replaces bounties/get-involved)
- [ ] **ICT Capital article** — The original WP site had a full article page with
      Abstract, Introduction, Results, and Conclusion sections.  Currently only
      referenced from publications.html.  Consider adding as standalone page.
- [ ] **White Paper update notes** — The got-choices post had Oct 2023 update notes
      about improved R code and API-based data fetching.  Currently summarized
      briefly in publications.html.

## Pages Dropped (intentional)

- [x] **Login page** — WordPress-specific, not needed
- [x] **Submit an Article page** — Blog submission form, not needed
- [x] **Forum / Posts listing** — Blog feature dropped per plan
- [x] **Available Bounties** — Bounty program dropped; replaced with research invitation

## Infrastructure Tasks

- [x] Design exploration: 3 previews created (A/B/C), Design B selected
- [x] Set up site skeleton: CSS theme system (base.css + swappable theme-*.css),
      shared header/footer via JS includes, mobile nav toggle
- [x] Extract and organize media assets (10 images in assets/img/)
- [x] Remap publication downloads to GitHub repo links
- [x] Navigation: Home, What's a CHIP?, Publications, CHIP Value, FAQ, Contact
- [x] Social media sharing buttons (X, LinkedIn, Facebook, Reddit, Email) in footer
- [x] "Follow" social links (LinkedIn, YouTube, X, GitHub) in footer
- [x] Cross-links to sister sites: gotchoices.org, mychips.org, sereus.org
- [x] Responsive CSS (mobile nav, stacked layouts, font scaling)
- [x] `fetchValue` script — pulls chip-dollar.csv and chip.json from mychips.org
- [x] `publish` script — scp deploy using CHIPCENTRAL_WEB_DEPLOY env var
- [x] `server` script — local dev server for preview (python3 http.server)
- [ ] Visual polish: review in browser, fix spacing/alignment issues
- [ ] Test all pages end-to-end
- [ ] Deploy to production

## Theme Switching

Single control point: edit `js/theme.js` and change the `CHIP_THEME` variable:
  `var CHIP_THEME = 'theme-modern';`   — Design B: clean modern (current)
  `var CHIP_THEME = 'theme-startup';`  — Design A: dark hero / Startupzy
All pages load this file in `<head>` so the switch is site-wide and flash-free.

## File Layout

```
web/site/
  index.html          Home / landing page
  chip.html           What's a CHIP?
  publications.html   Publications (links to GitHub)
  value.html          CHIP Value Today (D3 chart)
  faq.html            FAQ (8 items, accordion)
  contact.html        Contact (mailto + project cards)
  fetchValue          Script: fetch data from mychips.org
  publish             Script: scp deploy to server
  css/
    base.css          Theme-agnostic structural styles
    theme-modern.css  Design B: clean modern (active)
    theme-startup.css Design A: dark hero / Startupzy (alternate)
  js/
    common.js         Header/footer injection, CHIP value loading, nav
  includes/
    header.html       Shared site header + navigation
    footer.html       Shared footer with social links
  assets/
    img/              Images (hero, article thumbnails, icons)
    data/             chip-dollar.csv, chip.json
web/previews/         Design comparison files (A, B, C)
web/server            Local dev server script
web/STATUS.md         This file
```

## Source Material Reference

- WordPress SQL dump: `web/tmp/wordpress-quick-start/backup/db-feb-27-2025.sql`
- Uploaded media: `web/tmp/wordpress-quick-start/wordpress/wp-content/uploads/`
- Theme assets: `web/tmp/wordpress-quick-start/wordpress/wp-content/themes/startupzy/assets/`
- Extracted page content: `/tmp/wp_content/` (temporary, regenerable)
- Live site snapshot: https://chipcentral.net (still running as of Feb 2025)
- CHIP value chart source: https://mychips.org/value.html
