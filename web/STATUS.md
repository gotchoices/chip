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

- [x] **Q5: Design Direction** — RESOLVED: Present alternate design previews during build.
      Fallback is to replicate current Startupzy style (dark hero, blue accents, mountain
      dividers) which is acceptable if no better alternative emerges.

---

## Pages to Port

Once questions are resolved, these are the content items to migrate:

- [ ] **Home / Landing Page** — Hero section ("How Valuable is a CHIP?"), current CHIP value
      callout, forum/publications preview cards, "What's a CHIP?" explainer section,
      "How to get involved" steps (1-2-3), FAQ accordion
- [ ] **What's a CHIP?** — Founder's message post (slug: /chip/) — lengthy explainer with
      definition, history, links to gotchoices.org
- [ ] **Publications** — Links to white papers and supporting documents.  Per plan: rewrite
      links to point into github.com/gotchoices/chip repo instead of hosting files locally
- [ ] **CHIP Value Today** — Explanatory text + embedded chart from mychips.org/value.html
- [ ] **White Paper post** — "CHIPs Valuation Theory White Paper" with inline PDF viewer
      and update notes (slug: /got-choices/)
- [ ] **ICT Capital post** — "A Look at ICT Capital" follow-up study (slug: /a-look-at-ict-capital/)
- [ ] **FAQ section** — Three Q&A items (submission process, payment eligibility, multiple entries)
- [ ] **Contact page** — Simple mailto: link, matching gotchoices.org pattern
- [ ] **Get Involved / Research** — Invitation to contact for research collaboration,
      mention of possible funding for bona fide participants (replaces bounties page)

## Pages to Drop

- [x] **Login page** — WordPress-specific, not needed
- [x] **Submit an Article page** — Blog submission form, not needed
- [x] **Forum / Posts listing** — Blog feature dropped per plan

## Infrastructure Tasks

- [ ] Design exploration: create 2-3 alternate design previews for review; fallback to
      replicating current Startupzy style if none preferred
- [ ] Set up site skeleton (index.html, shared header/footer, CSS, directory structure)
- [ ] Extract and organize media assets from WordPress uploads
      (images: ~10 unique files; theme stock images as needed)
- [ ] Remap publication/document downloads to GitHub repo links
      (github.com/gotchoices/chip — PDFs, ZIPs, R code, etc.)
- [ ] Navigation: Home, What's a CHIP?, Publications, CHIP Value, FAQ, Contact
- [ ] Social media sharing buttons (share on X, LinkedIn, Facebook, Reddit, Pinterest, Email)
      matching gotchoices.org pattern
- [ ] "Follow" social links (LinkedIn, YouTube, X, Rumble, GitHub) matching gotchoices.org
- [ ] Cross-links to sister sites: gotchoices.org, mychips.org, sereus.org
- [ ] Responsive design (desktop/tablet/mobile)
- [ ] Create `fetchValue` script — pulls chip-dollar.csv and chip.json from mychips.org,
      stores local copies for the D3 chart and headline value display
- [ ] Create `publish` script — scp-based deploy using CHIPCENTRAL_WEB_DEPLOY env var,
      modeled on mychips.org publish script
- [ ] Test and validate all pages
- [ ] Deploy to chosen hosting

## Source Material Reference

- WordPress SQL dump: `web/tmp/wordpress-quick-start/backup/db-feb-27-2025.sql`
- Uploaded media: `web/tmp/wordpress-quick-start/wordpress/wp-content/uploads/`
- Theme assets: `web/tmp/wordpress-quick-start/wordpress/wp-content/themes/startupzy/assets/`
- Extracted page content: `/tmp/wp_content/` (temporary, regenerable)
- Live site snapshot: https://chipcentral.net (still running as of Feb 2025)
- CHIP value chart source: https://mychips.org/value.html
