# SEO, AEO, and AI Discoverability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make REAL Bangkok's four static pages independently discoverable in English, Thai, and Japanese, with English primary and accurate answer-ready content.

**Architecture:** Keep English at the existing root URLs and add static `/th/` and `/ja/` counterparts. Make each document's language explicit in HTML, route language selection through same-page locale links, and add static per-locale metadata, structured data, crawl files, summaries, and tool FAQs.

**Tech Stack:** Static HTML, CSS, and JavaScript; Python standard-library `unittest` for static-site checks. No production dependency or build system.

**Spec:** [`docs/superpowers/specs/2026-10-23-seo-aeo-aio-design.md`](../specs/2026-10-23-seo-aeo-aio-design.md)

## Global Constraints

- Do not add a framework, package, build dependency, or backend.
- Preserve the current root page paths and the existing tools' behavior, including LED-wall state sharing and simulator functionality.
- Keep the existing three-language selector, but make it navigate between the locale-specific URLs.
- Do not introduce new business facts or broaden the site's service claims.
- Update the run README if the new locale paths or local validation workflow require clarification.

## Review Focus

- A stale local-storage language preference must not make the English root or a locale URL render the wrong language; test each locale route's `html lang` and language selector state.
- `/index.html` must not compete with `/` as a second English homepage; test that its canonical points to `/`.
- Locale-prefixed pages must not break shared scripts, styles, images, or navigation; test that every local asset URL resolves from the site root and smoke-test page navigation.
- Hreflang and sitemap URLs must agree with the canonical URL for each page; test all 12 route mappings and the three reciprocal language alternates.
- Invalid JSON-LD or FAQ markup that differs from visible answers must not ship; parse every JSON-LD block and compare FAQ question/answer text with visible content.

---

### Task 1: Create crawlable locale pages and route-aware language selection

**Files:**
- Modify: `index.html`, `photos.html`, `led-wall.html`, `vp-sim.html`
- Create: `th/index.html`, `th/photos.html`, `th/led-wall.html`, `th/vp-sim.html`
- Create: `ja/index.html`, `ja/photos.html`, `ja/led-wall.html`, `ja/vp-sim.html`
- Modify: `js/home.js`, `js/app.js`, `js/vp-sim.js`
- Create: `tests/test_discoverability.py`

**Interfaces:**
- Each document sets `html[lang]` to exactly `en`, `th`, or `ja`.
- Each `#langSeg` button has a `data-href` pointing to the same page in its selected locale.
- The language control matching `html[lang]` has `aria-pressed="true"`; the others have `aria-pressed="false"`.
- The existing page scripts initialize their language from `document.documentElement.lang`; the selected route is authoritative, not `localStorage` or a query parameter.
- Keep LED-wall and simulator persistence keys unchanged.

- [ ] **Step 1: Write failing locale and asset tests**

  In `tests/test_discoverability.py`, use Python's `unittest`, `html.parser`, and `pathlib` to add:
  - `test_all_locale_routes_exist_with_correct_document_language`: assert the root English files and all eight `/th/` and `/ja/` files exist and have the expected `html lang`.
  - `test_language_switch_targets_same_page_in_each_locale`: assert every page has EN/TH/JP controls whose `data-href` points to the corresponding page route and only the current locale is pressed.
  - `test_local_asset_references_resolve_from_site_root`: assert local `src`/`href` references use root-relative paths and resolve to existing files.
  - `test_internal_page_links_resolve_in_same_locale`: assert navigation links point to the matching route in the current locale and resolve to a page.

- [ ] **Step 2: Run the locale tests and verify they fail for missing locale routes**

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: FAIL because the Thai/Japanese route files and `data-href` links do not yet exist.

- [ ] **Step 3: Add localized static pages and make language selection route-driven**

  Use the four current HTML pages as the English root versions and create the Thai/Japanese equivalents. Localize the initial HTML copy and set the matching `html lang`; reference shared assets with root-relative paths. Add equivalent `data-href` targets to language controls and internal navigation.

  In `js/home.js`, `js/app.js`, and `js/vp-sim.js`, initialize the selected language from `document.documentElement.lang`. Replace in-place language mutation/local-storage preference changes in the selector handlers with navigation to the clicked control's `data-href`. Preserve configurator/simulator state storage.

- [ ] **Step 4: Run locale tests and verify they pass**

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: PASS for all route, language, and local asset assertions.

- [ ] **Step 5: Smoke-test all locale pages and existing tools**

  Serve the site with `python3 -m http.server 8000`. Visit all 12 URLs; change languages from each page and confirm the matching page opens in the selected language. Check the configurator still copies/shares its state and the simulator still loads its modules and saved wall settings.

  Expected: no broken assets, wrong-language page, console error, or lost tool behavior.

### Task 2: Add localized metadata, structured data, and crawl files

**Files:**
- Modify: all 12 HTML pages
- Create: `robots.txt`, `sitemap.xml`
- Modify: `tests/test_discoverability.py`

**Interfaces:**
- English homepage canonical: `https://www.realbkk.com/`; if `/index.html` remains reachable, its canonical is also `/`.
- The canonical URL for each other route is its own `https://www.realbkk.com` URL.
- Each page's hreflang set contains `en`, `th`, `ja`, and `x-default`; `x-default` points to the corresponding English page.
- Every page includes JSON-LD `Organization`, `WebSite`, and page-level `WebPage` entities. Reuse the same organization identifier and only verified identity details.

- [ ] **Step 1: Add failing metadata and crawl-file tests**

  Extend `tests/test_discoverability.py` with:
  - `test_each_page_has_one_localized_title_description_and_canonical`: assert one non-empty title, one description, and the expected canonical on each route.
  - `test_social_metadata_matches_localized_page`: assert Open Graph title/description/URL/image and a Twitter card are present and use that page's locale and URL.
  - `test_hreflang_alternates_are_reciprocal`: assert each localized page links to the three equivalent routes and the English `x-default`.
  - `test_sitemap_contains_each_canonical_once_and_robots_references_it`: parse XML with `xml.etree.ElementTree`, assert all 12 canonical URLs appear once, and assert `robots.txt` permits crawling and references the sitemap.
  - `test_jsonld_parses_and_uses_verified_schema_types`: parse every `application/ld+json` block with `json.loads`; assert organization, website, and page entities are present and no unsupported local-business contact claims are added.

- [ ] **Step 2: Run metadata tests and verify they fail**

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: FAIL because the pages do not yet contain canonical, social, hreflang, or JSON-LD metadata and crawl files are absent.

- [ ] **Step 3: Add metadata and crawl files**

  Add unique localized `<title>` and description values, canonical and social tags, reciprocal hreflang alternates, and JSON-LD to all 12 pages. Use the verified `www.realbkk.com` domain, public organization name, existing logo, and existing YouTube channel only. Add `robots.txt` with an allow-all default and the sitemap URL; add `sitemap.xml` with exactly the 12 canonical URLs.

- [ ] **Step 4: Run metadata tests and verify they pass**

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: PASS, including successful parsing of all XML and JSON-LD.

### Task 3: Add answer-ready copy, visible tool FAQs, and operating notes

**Files:**
- Modify: all 12 HTML pages
- Modify: `js/home.js` only if required to give meaningful gallery images localized alt text
- Modify: `README.md`
- Modify: `tests/test_discoverability.py`

**Interfaces:**
- Every page has one concise, visible, localized summary adjacent to its main heading.
- Only the LED Wall Configurator and Virtual Production Simulator get FAQs; answers describe existing inputs, outputs, and workflows.
- If FAQ structured data is used, it is generated from or kept text-identical to the visible FAQ content.
- Decorative images retain empty alt text; informative images receive localized descriptions.

- [ ] **Step 1: Add failing answer-content tests**

  Extend `tests/test_discoverability.py` with:
  - `test_each_page_has_a_visible_localized_summary`: assert each page has a main heading and a non-empty adjacent summary in its document language.
  - `test_tool_faq_markup_matches_visible_questions_and_answers`: assert FAQs appear only on the two tool pages and any FAQ JSON-LD exactly matches the visible question/answer text.
  - `test_informative_images_have_alt_text`: assert gallery/content images have localized non-empty alt text and decorative images remain explicitly empty-alt.

- [ ] **Step 2: Run answer-content tests and verify they fail**

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: FAIL for missing localized summaries and FAQs, or any informative images without localized alt text.

- [ ] **Step 3: Add factual summaries and tool FAQs**

  Add concise localized page summaries and a small visible FAQ to each tool page. Base answers only on the current configurator and simulator UI; do not claim studio specifications, pricing, availability, or other unverified business details. Add FAQ JSON-LD only if it matches the visible FAQ exactly. Correct alt text for informative images while preserving empty decorative alt text.

- [ ] **Step 4: Update the README for locale paths and checks**

  Update `README.md` to describe the English root pages, Thai/Japanese route prefixes, and the Python standard-library test command.

- [ ] **Step 5: Run all static checks and browser smoke tests**

  Run: `python3 -m unittest discover -s tests -v`

  Expected: PASS for all locale, metadata, sitemap, robots, structured-data, summary, FAQ, and alt-text checks.

  Then serve locally with `python3 -m http.server 8000`, open the homepage in each locale, test selector navigation and internal links, and confirm the configurator/simulator still work.

## Execution note

The current workspace is not a Git checkout. Do not attempt commits here; apply this plan in a clone or other Git worktree before implementation if commits or a PR are required.
