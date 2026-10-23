# SEO, AEO, and AI discoverability design

## Goal

Improve organic search visibility and make the site's verified information easier for answer engines and AI search systems to find and quote. English is the primary language; Thai and Japanese remain supported as independently crawlable secondary locales.

The work must preserve the existing static-site approach and interactive tools. It must not invent business facts or promise rankings, rich results, or AI citations.

## Current state

- The site is a static website with four pages: the home/showcase, photos, LED Wall Configurator, and Virtual Production Simulator.
- Thai, English, and Japanese are available through client-side language switching. The same URL currently serves each language, and language preference is stored in local storage.
- Page titles and descriptions exist, but the photos page reuses the home description.
- The pages do not currently define canonical URLs, Open Graph/Twitter metadata, hreflang links, or structured data. There is no sitemap or robots.txt.
- The site domain used for canonicals is `https://www.realbkk.com`.

## Locale URL design

Keep the current root URLs as English:

| Page | English | Thai | Japanese |
|---|---|---|---|
| Home | `/` (`/index.html` may remain an alias) | `/th/` | `/ja/` |
| Photos | `/photos.html` | `/th/photos.html` | `/ja/photos.html` |
| LED Wall Configurator | `/led-wall.html` | `/th/led-wall.html` | `/ja/led-wall.html` |
| Virtual Production Simulator | `/vp-sim.html` | `/th/vp-sim.html` | `/ja/vp-sim.html` |

The locale route, not local storage, determines the initial document language and selected language control. The language selector navigates to the equivalent page in the selected locale. It must not redirect search crawlers or visitors based on cookies or browser language.

The root `/` is the canonical English homepage. If `/index.html` remains directly accessible, it must identify `/` as canonical.

Each route must provide localized initial HTML for its document language, including the title, description, main heading, concise explanatory copy, and other meaningful page text. Existing JavaScript interactions and tools remain functional. Shared CSS, JavaScript, images, and navigation links must resolve correctly from both root and locale-prefixed paths.

## Search metadata and structured data

- Give each page in each locale a distinct, accurate title and meta description.
- Add one canonical URL per document, pointing to its own locale URL.
- Add reciprocal `hreflang` links for English (`en`), Thai (`th`), Japanese (`ja`), and English as `x-default`.
- Add localized Open Graph title/description/URL/image metadata and appropriate Twitter card metadata.
- Add JSON-LD for the REAL Bangkok organization and website, plus appropriate page-level `WebPage` metadata. Use only details verifiable from the site, such as the public name, domain, logo, and YouTube channel. Do not add an address, phone number, opening hours, or service claims that are not present and verified.
- Add a sitemap containing all 12 canonical URLs and a `robots.txt` that permits crawling and references that sitemap.

## Answer and AI search content

- Add a concise, visible, localized summary near each page's main heading so the page purpose and supported facts are clear in the initial HTML.
- Add a small localized FAQ to the two interactive tool pages. Questions and answers must describe only existing, verifiable tool behavior, such as calculator inputs/outputs and the simulator workflow.
- Add FAQ structured data only when it exactly matches visible FAQ content.
- Ensure images that communicate content have descriptive localized alternative text; retain empty alt text for decorative images.
- Use semantic heading structure and descriptive link text where necessary to make the content easier to parse.

These changes improve clarity and crawlability but do not guarantee search rankings, FAQ rich results, or AI citations. No `llms.txt` or proprietary crawler-specific behavior is required.

## Compatibility and scope

- Do not add a framework, package, build dependency, or backend.
- Preserve the current root page paths and the existing tools' behavior, including LED-wall state sharing and simulator functionality.
- Keep the existing three-language selector, but make it navigate between the locale-specific URLs.
- Do not introduce new business facts or broaden the site's service claims.
- Update the run README if the new locale paths or local validation workflow require clarification.

## Acceptance criteria

1. All 12 locale/page URLs return the intended page in its intended language without requiring a language preference in local storage.
2. Each page has one correct localized title, description, canonical URL, Open Graph/Twitter metadata, and a complete reciprocal hreflang set.
3. The language selector navigates to the matching page in each supported language; navigation and shared assets work from root and locale paths.
4. The sitemap lists each canonical URL exactly once, and robots.txt points to the sitemap without blocking the site.
5. JSON-LD parses as valid JSON and contains no unverified business facts. Any FAQ markup matches visible answers.
6. Existing configurator and simulator functionality remains available.
7. Local verification covers metadata consistency, links/assets, and behavior across locales. Deployment verification in Search Console or AI search products is an operational follow-up, not a claim of guaranteed ranking.
