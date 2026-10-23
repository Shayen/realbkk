import html
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGE_TYPES = ("index.html", "photos.html", "led-wall.html", "vp-sim.html")
LOCALES = ("en", "th", "ja")


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.document_language = None
        self.language_buttons = []
        self.references = []
        self.page_links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "html":
            self.document_language = attributes.get("lang")
        if tag == "button" and attributes.get("data-v") in LOCALES:
            self.language_buttons.append(attributes)
        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value:
                self.references.append((tag, attribute, value))
                if tag == "a" and attribute == "href":
                    self.page_links.append(value)


def route_path(locale, page_type):
    if locale == "en":
        return f"/{page_type}"
    return f"/{locale}/{page_type}"


def parse_page(path):
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class DiscoverabilityTests(unittest.TestCase):
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
