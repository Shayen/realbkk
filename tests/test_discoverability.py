import html
import json
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGE_TYPES = ("index.html", "photos.html", "led-wall.html", "vp-sim.html")
LOCALES = ("en", "th", "ja")
SITE_URL = "https://www.realbkk.com"
LOGO_URL = f"{SITE_URL}/logo/REAL-bangkok3.jpg"
YOUTUBE_URL = "https://www.youtube.com/@realbangkok7314/videos"


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.document_language = None
        self.language_buttons = []
        self.references = []
        self.page_links = []
        self.title = []
        self.meta = []
        self.links = []
        self.jsonld_blocks = []
        self.headings = []
        self.summaries = []
        self.adjacent_summaries = 0
        self.faq_sections = 0
        self.faq_details = []
        self.faqs = []
        self.images = []
        self._in_title = False
        self._jsonld_data = None
        self._in_heading = False
        self._heading_text = []
        self._after_heading = False
        self._summary = None
        self._faq_active = False
        self._faq_capture = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if self._after_heading:
            if tag == "p" and "page-summary" in attributes.get("class", "").split():
                self.adjacent_summaries += 1
            self._after_heading = False
        if tag == "html":
            self.document_language = attributes.get("lang")
        if tag == "title":
            self._in_title = True
        if tag == "h1":
            self._in_heading = True
            self._heading_text = []
        if tag == "img":
            self.images.append(attributes)
        if tag == "p" and "page-summary" in attributes.get("class", "").split():
            self._summary = {"attributes": attributes, "text": []}
        if tag == "section" and "faq" in attributes.get("class", "").split():
            self.faq_sections += 1
            self._faq_active = True
        if self._faq_active and tag == "details":
            self.faq_details.append(attributes)
        if self._faq_active and tag in ("summary", "p"):
            self._faq_capture = {"tag": tag, "text": []}
        if tag == "meta":
            self.meta.append(attributes)
        if tag == "link":
            self.links.append(attributes)
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self._jsonld_data = []
        if tag == "button" and attributes.get("data-v") in LOCALES:
            self.language_buttons.append(attributes)
        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value:
                self.references.append((tag, attribute, value))
                if tag == "a" and attribute == "href":
                    self.page_links.append(value)

    def handle_data(self, data):
        if self._in_title:
            self.title.append(data)
        if self._in_heading:
            self._heading_text.append(data)
        if self._summary is not None:
            self._summary["text"].append(data)
        if self._faq_capture is not None:
            self._faq_capture["text"].append(data)
        if self._jsonld_data is not None:
            self._jsonld_data.append(data)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._jsonld_data is not None:
            self.jsonld_blocks.append("".join(self._jsonld_data))
            self._jsonld_data = None
        if tag == "h1":
            self.headings.append("".join(self._heading_text).strip())
            self._in_heading = False
            self._after_heading = True
        if tag == "p" and self._summary is not None:
            self._summary["text"] = "".join(self._summary["text"]).strip()
            self.summaries.append(self._summary)
            self._summary = None
        if tag in ("summary", "p") and self._faq_capture is not None:
            if self._faq_capture["tag"] == tag:
                self.faq_capture_text = "".join(self._faq_capture["text"]).strip()
                if tag == "summary":
                    self._current_question = self.faq_capture_text
                else:
                    self.faqs.append((getattr(self, "_current_question", ""), self.faq_capture_text))
                self._faq_capture = None
        if tag == "section" and self._faq_active:
            self._faq_active = False


def route_path(locale, page_type):
    if locale == "en":
        return f"/{page_type}"
    return f"/{locale}/{page_type}"


def canonical_path(locale, page_type):
    if page_type == "index.html":
        return "/" if locale == "en" else f"/{locale}/"
    return route_path(locale, page_type)


def canonical_url(locale, page_type):
    return f"{SITE_URL}{canonical_path(locale, page_type)}"


def parse_page(path):
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class DiscoverabilityTests(unittest.TestCase):
    def test_each_page_has_a_visible_localized_summary(self):
        summaries_by_page = {page_type: [] for page_type in PAGE_TYPES}
        simulator_script = (ROOT / "js/vp-sim.js").read_text(encoding="utf-8")
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    parser = parse_page(route)
                    self.assertEqual(len(parser.headings), 1, "Each page must have one main heading")
                    self.assertEqual(len(parser.summaries), 1, "Each page must have one adjacent summary")
                    self.assertEqual(parser.adjacent_summaries, 1)
                    summary = parser.summaries[0]
                    self.assertTrue(summary["text"], "Summary must not be empty")
                    self.assertEqual(summary["attributes"].get("lang"), locale)
                    self.assertNotIn("hidden", summary["attributes"])
                    self.assertNotIn("sr-only", summary["attributes"].get("class", "").split())
                    if page_type == "vp-sim.html":
                        locale_block = re.search(
                            rf"(?ms)^\s{{2}}{locale}: \{{(.*?)(?=^\s{{2}}(?:th|en|ja): \{{|^\s*\}};)",
                            simulator_script,
                        )
                        self.assertIsNotNone(locale_block, f"Missing {locale} simulator translations")
                        self.assertRegex(
                            locale_block.group(1),
                            r"'page\.simSummary':\s*'[^']+'",
                            f"Missing {locale} simulator summary translation",
                        )
                    summaries_by_page[page_type].append(summary["text"])
        for page_type, summaries in summaries_by_page.items():
            self.assertEqual(len(summaries), len(set(summaries)), f"{page_type} summaries must be localized")

    def test_tool_faq_markup_matches_visible_questions_and_answers(self):
        tool_pages = {"led-wall.html", "vp-sim.html"}
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    parser = parse_page(route)
                    expected_sections = int(page_type in tool_pages)
                    self.assertEqual(parser.faq_sections, expected_sections)
                    if not expected_sections:
                        self.assertEqual(parser.faqs, [])
                        self.assertEqual(parser.faq_details, [])
                        continue
                    self.assertGreaterEqual(len(parser.faqs), 2)
                    self.assertTrue(all("open" in details for details in parser.faq_details))
                    self.assertTrue(all(question and answer for question, answer in parser.faqs))
                    for block in parser.jsonld_blocks:
                        parsed = json.loads(block)
                        entities = parsed.get("@graph", [parsed])
                        for entity in entities:
                            if entity.get("@type") != "FAQPage":
                                continue
                            structured_faqs = [
                                (
                                    item.get("name", "").strip(),
                                    item.get("acceptedAnswer", {}).get("text", "").strip(),
                                )
                                for item in entity.get("mainEntity", [])
                            ]
                            self.assertEqual(structured_faqs, parser.faqs)

    def test_informative_images_have_alt_text(self):
        home_script = (ROOT / "js/home.js").read_text(encoding="utf-8")
        self.assertIn("img.alt = t('alt.' + img.dataset.cat)", home_script)
        self.assertIn("img.alt = t('alt.' + p.cat)", home_script)
        self.assertIsNotNone(
            re.search(
                r"img\.dataset\.cat = p\.cat;\s*img\.alt = t\('alt\.' \+ p\.cat\);",
                home_script,
            ),
            "Gallery thumbnails must receive localized alt text when created",
        )
        for locale in LOCALES:
            with self.subTest(locale=locale):
                locale_block = re.search(
                    rf"(?ms)^\s*{locale}: \{{(.*?)(?=^\s*(?:th|en|ja): \{{|^\s*\}};)",
                    home_script,
                )
                self.assertIsNotNone(locale_block, f"Missing {locale} gallery translations")
                for category in ("stage", "crew", "control"):
                    self.assertRegex(
                        locale_block.group(1),
                        rf"'alt\.{category}':\s*'[^']+'",
                        f"Missing localized {category} image description",
                    )

        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    for image in parse_page(route).images:
                        self.assertIn("alt", image, f"Every image needs explicit alt text: {route}")
                        if image.get("alt") == "":
                            if page_type == "index.html":
                                self.assertEqual(image.get("class"), "on", "Only the decorative hero image is empty-alt")
                            elif page_type == "photos.html":
                                self.assertNotIn("src", image, "The empty-alt photo image is a dynamic reveal placeholder")
                            else:
                                self.fail(f"Informative image must have a description: {route}")

    def test_each_page_has_one_localized_title_description_and_canonical(self):
        titles = []
        descriptions = []
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    parser = parse_page(route)
                    title = "".join(parser.title).strip()
                    descriptions_for_page = [
                        meta.get("content", "").strip()
                        for meta in parser.meta
                        if meta.get("name", "").lower() == "description"
                    ]
                    canonicals = [
                        link.get("href")
                        for link in parser.links
                        if "canonical" in link.get("rel", "").split()
                    ]
                    self.assertTrue(title, "Page title must not be empty")
                    self.assertEqual(len(descriptions_for_page), 1)
                    self.assertTrue(descriptions_for_page[0], "Page description must not be empty")
                    self.assertEqual(canonicals, [canonical_url(locale, page_type)])
                    titles.append(title)
                    descriptions.append(descriptions_for_page[0])
        self.assertEqual(len(titles), len(set(titles)), "Titles must be unique across all locale routes")
        self.assertEqual(
            len(descriptions),
            len(set(descriptions)),
            "Descriptions must be unique across all locale routes",
        )

    def test_social_metadata_matches_localized_page(self):
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    parser = parse_page(route)
                    values = {
                        (meta.get("property") or meta.get("name")): meta.get("content", "").strip()
                        for meta in parser.meta
                    }
                    title = "".join(parser.title).strip()
                    description = values.get("description")
                    self.assertTrue(title)
                    self.assertTrue(description)
                    self.assertEqual(values.get("og:title"), title)
                    self.assertEqual(values.get("og:description"), description)
                    self.assertEqual(values.get("og:url"), canonical_url(locale, page_type))
                    self.assertEqual(values.get("og:image"), LOGO_URL)
                    self.assertEqual(values.get("og:locale"), {"en": "en_US", "th": "th_TH", "ja": "ja_JP"}[locale])
                    self.assertTrue(values.get("twitter:card"))
                    self.assertEqual(values.get("twitter:card"), "summary_large_image")

    def test_hreflang_alternates_are_reciprocal(self):
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    parser = parse_page(route)
                    alternates = {
                        link.get("hreflang"): link.get("href")
                        for link in parser.links
                        if link.get("rel") == "alternate" and link.get("hreflang")
                    }
                    english_url = canonical_url("en", page_type)
                    self.assertEqual(
                        alternates,
                        {
                            "en": english_url,
                            "th": canonical_url("th", page_type),
                            "ja": canonical_url("ja", page_type),
                            "x-default": english_url,
                        },
                    )

    def test_sitemap_contains_each_canonical_once_and_robots_references_it(self):
        sitemap = ET.parse(ROOT / "sitemap.xml")
        urls = [element.text for element in sitemap.findall(".//{*}loc")]
        expected = [
            canonical_url(locale, page_type)
            for locale in LOCALES
            for page_type in PAGE_TYPES
        ]
        self.assertEqual(len(urls), 12)
        self.assertCountEqual(urls, expected)
        self.assertEqual(len(urls), len(set(urls)))

        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        directives = [line.strip() for line in robots.splitlines() if line.strip()]
        self.assertIn("User-agent: *", directives)
        self.assertIn("Allow: /", directives)
        self.assertIn(f"Sitemap: {SITE_URL}/sitemap.xml", directives)

    def test_jsonld_parses_and_uses_verified_schema_types(self):
        organization_ids = set()
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    parser = parse_page(route)
                    self.assertTrue(parser.jsonld_blocks)
                    entities = []
                    for block in parser.jsonld_blocks:
                        parsed = json.loads(block)
                        entities.extend(parsed.get("@graph", [parsed]))
                    by_type = {
                        entity_type: entity
                        for entity in entities
                        for entity_type in (
                            [entity["@type"]]
                            if isinstance(entity.get("@type"), str)
                            else entity.get("@type", [])
                        )
                    }
                    self.assertTrue({"Organization", "WebSite", "WebPage"} <= set(by_type))
                    organization = by_type["Organization"]
                    organization_ids.add(organization.get("@id"))
                    self.assertEqual(organization.get("name"), "REAL Bangkok")
                    self.assertEqual(organization.get("url"), f"{SITE_URL}/")
                    self.assertEqual(organization.get("logo"), LOGO_URL)
                    self.assertEqual(organization.get("sameAs"), [YOUTUBE_URL])
                    self.assertEqual(by_type["WebSite"].get("url"), f"{SITE_URL}/")
                    self.assertEqual(by_type["WebPage"].get("url"), canonical_url(locale, page_type))
                    self.assertEqual(by_type["WebPage"].get("inLanguage"), locale)
                    serialized = json.dumps(entities).lower()
                    self.assertNotIn("localbusiness", serialized)
                    for unsupported_claim in ("address", "telephone", "openinghours", "contactpoint"):
                        self.assertNotIn(f'"{unsupported_claim}"', serialized)
        self.assertEqual(len(organization_ids), 1)
        self.assertNotIn(None, organization_ids)

    def test_all_locale_routes_exist_with_correct_document_language(self):
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                with self.subTest(locale=locale, page=page_type):
                    route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                    self.assertTrue(route.is_file(), f"Missing route: {route.relative_to(ROOT)}")
                    self.assertEqual(parse_page(route).document_language, locale)

    def test_language_switch_targets_same_page_in_each_locale(self):
        for current_locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if current_locale == "en" else f"{current_locale}/{page_type}")
                with self.subTest(locale=current_locale, page=page_type):
                    parser = parse_page(route)
                    controls = {button.get("data-v"): button for button in parser.language_buttons}
                    self.assertEqual(set(controls), set(LOCALES))
                    for locale in LOCALES:
                        button = controls[locale]
                        self.assertEqual(button.get("data-href"), route_path(locale, page_type))
                        self.assertEqual(button.get("aria-pressed"), str(locale == current_locale).lower())

    def test_local_asset_references_resolve_from_site_root(self):
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    for tag, attribute, reference in parse_page(route).references:
                        parsed = urlsplit(html.unescape(reference))
                        if parsed.scheme or parsed.netloc or parsed.path.endswith(".html"):
                            continue
                        if not parsed.path:
                            continue
                        self.assertTrue(
                            parsed.path.startswith("/"),
                            f"{route.relative_to(ROOT)} {tag}[{attribute}] is not root-relative: {reference}",
                        )
                        asset = ROOT / unquote(parsed.path.lstrip("/"))
                        self.assertTrue(
                            asset.is_file(),
                            f"{route.relative_to(ROOT)} references missing asset: {reference}",
                        )

    def test_internal_page_links_resolve_in_same_locale(self):
        known_pages = set(PAGE_TYPES)
        for locale in LOCALES:
            for page_type in PAGE_TYPES:
                route = ROOT / (page_type if locale == "en" else f"{locale}/{page_type}")
                with self.subTest(locale=locale, page=page_type):
                    for reference in parse_page(route).page_links:
                        parsed = urlsplit(html.unescape(reference))
                        if parsed.scheme or parsed.netloc or not parsed.path.endswith(".html"):
                            continue
                        target_name = Path(unquote(parsed.path)).name
                        if target_name not in known_pages:
                            continue
                        expected = route_path(locale, target_name)
                        self.assertEqual(parsed.path, expected, f"Wrong-locale link in {route}: {reference}")
                        target = ROOT / parsed.path.lstrip("/")
                        self.assertTrue(target.is_file(), f"Missing linked page: {reference}")


if __name__ == "__main__":
    unittest.main()
