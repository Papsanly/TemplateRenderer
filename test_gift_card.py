import base64
import os
import re
import unittest

import qrcode

from renderer.config import TEMPLATE_PATH
from renderer.template import env, get_context_keys, render_template
from scripts.switch_theme import TEMPLATE_FILES, comment_christmas_block, uncomment_christmas_block
from server import (
    back_cover_a4_path,
    build_activation_url,
    generate_qr_code,
    get_template_name,
    get_template_params,
)

FRONT_TEMPLATES = ("wefly_certificate.html", "wefly_certificate_a4.html")
ALL_TEMPLATES = FRONT_TEMPLATES + ("wefly_back.html", "wefly_back_a4.html")


def render_front(template, simulator, is_birthday=False, code="PDLEDC"):
    params = get_template_params(simulator, "50", code, "2027-09-22", is_birthday)
    return render_template(template, params)


def read_template(template):
    with open(os.path.join(TEMPLATE_PATH, template), encoding="utf-8") as f:
        return f.read()


def body_of(html):
    """The markup after the stylesheet, minus the QR data URI (random-looking base64)."""
    return re.sub(r'src="data:[^"]+"', 'src=""', html.split("</style>")[1])


def qr_modules_from_data_uri(data_uri):
    """Rebuild the module matrix from the SVG the server puts in the template."""
    prefix = "data:image/svg+xml;base64,"
    assert data_uri.startswith(prefix)
    svg = base64.b64decode(data_uri[len(prefix):]).decode()
    size = int(re.search(r'viewBox="0 0 (\d+) \1"', svg).group(1))
    matrix = [[False] * size for _ in range(size)]
    for x, y, width in re.findall(r"M(\d+) (\d+)h(\d+)v1h-\d+z", svg):
        for column in range(int(x), int(x) + int(width)):
            matrix[int(y)][column] = True
    return matrix


class ActivationQrTests(unittest.TestCase):
    def test_link_opens_the_activation_page_for_this_code(self):
        self.assertEqual(build_activation_url("PDLEDC"), "https://wefly.aero/activate/PDLEDC")
        self.assertEqual(build_activation_url(" WF-7K2M-9Q "), "https://wefly.aero/activate/WF-7K2M-9Q")

    def test_link_escapes_characters_that_would_break_the_url(self):
        self.assertEqual(build_activation_url("A B/C?D#E"), "https://wefly.aero/activate/A%20B%2FC%3FD%23E")

    def test_qr_image_encodes_that_link_with_a_quiet_zone(self):
        for code in ("PDLEDC", "WF-7K2M-9Q", "GROUPON-ABCD-1234-XY"):
            with self.subTest(code=code):
                expected = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
                expected.add_data(f"https://wefly.aero/activate/{code}")
                expected.make(fit=True)
                matrix = qr_modules_from_data_uri(generate_qr_code(code))
                self.assertEqual(matrix, expected.get_matrix())
                # Four light modules on every side, so the code scans on any background.
                self.assertFalse(any(any(row) for row in matrix[:4] + matrix[-4:]))
                self.assertFalse(any(any(row[:4]) or any(row[-4:]) for row in matrix))

    def test_each_code_gets_its_own_qr_in_the_rendered_card(self):
        for template in FRONT_TEMPLATES:
            with self.subTest(template=template):
                first = render_front(template, "boeing737", code="AAAAAA")
                second = render_front(template, "boeing737", code="BBBBBB")
                self.assertIn(generate_qr_code("AAAAAA"), first)
                self.assertIn(generate_qr_code("BBBBBB"), second)
                self.assertNotIn(generate_qr_code("AAAAAA"), second)


class GiftCardTemplateTests(unittest.TestCase):
    def test_one_template_per_format(self):
        self.assertEqual(get_template_name(a4=True), "wefly_certificate_a4.html")
        self.assertEqual(get_template_name(a4=False), "wefly_certificate.html")

    def test_flight_simulators_get_the_boarding_pass(self):
        for simulator, gate in [("boeing737", "Boeing 737 MAX"), ("Boeing 737 MAX", "Boeing 737 MAX"),
                                ("airbus320", "Airbus A320"), ("Airbus A320", "Airbus A320")]:
            for template in FRONT_TEMPLATES:
                with self.subTest(simulator=simulator, template=template):
                    html = body_of(render_front(template, simulator))
                    self.assertIn("BOARDING PASS", html)
                    self.assertIn("FLIGHT DURATION", html)
                    self.assertIn(f'<span class="pass__value">{gate}</span>', html)
                    self.assertNotIn("RACE", html)
                    self.assertNotIn("f1", html)

    def test_a4_hero_names_the_simulator_that_was_bought(self):
        self.assertIn("only motion-powered Boeing 737 MAX simulator", render_front("wefly_certificate_a4.html", "boeing737"))
        html = render_front("wefly_certificate_a4.html", "Airbus A320")
        self.assertIn("only motion-powered Airbus A320 simulator", html)
        self.assertNotIn("Boeing", html)

    def test_formula_1_gets_the_race_pass_however_the_simulator_is_named(self):
        for simulator in ("formula1", "Formula 1", "FORMULA1"):
            for template in FRONT_TEMPLATES:
                with self.subTest(simulator=simulator, template=template):
                    html = body_of(render_front(template, simulator))
                    self.assertIn("RACE PASS", html)
                    self.assertIn("RACE DURATION", html)
                    self.assertIn("images/f1-outline-white.svg", html)
                    self.assertNotIn("BOARDING PASS", html)
                    self.assertNotIn("plane-outline", html)
        html = body_of(render_front("wefly_certificate_a4.html", "formula1"))
        self.assertIn("images/gift/hero-f1.jpg", html)
        self.assertIn("Who can race", html)
        self.assertNotIn("cockpit", html)

    def test_birthday_greeting_only_when_asked(self):
        for template in FRONT_TEMPLATES:
            with self.subTest(template=template):
                self.assertIn("Happy Birthday!", body_of(render_front(template, "boeing737", is_birthday=True)))
                self.assertNotIn("pass__greeting", body_of(render_front(template, "boeing737")))

    def test_long_codes_step_down_in_size(self):
        for code, css_class in [("PDLEDC", 'class="pass__code"'), ("WF-7K2M-9Q", 'class="pass__code"'),
                                ("ELEVENCHARS", "pass__code--long"), ("GROUPON-ABCD-1234-XY", "pass__code--xlong"),
                                ("A-VERY-LONG-PARTNER-VOUCHER-CODE", "pass__code--xxlong")]:
            with self.subTest(code=code):
                self.assertIn(f"{css_class}", render_front("wefly_certificate_a4.html", "boeing737", code=code))

    def test_cli_and_bot_still_see_the_card_fields(self):
        for template in FRONT_TEMPLATES:
            with self.subTest(template=template):
                keys = {key.name for key in get_context_keys(template)}
                self.assertEqual(keys, {"code", "qr_code", "gate", "duration", "seat_class", "expiration"})

    def test_back_page_rules_match_the_simulator(self):
        flight = render_template("wefly_back_a4.html", {})
        self.assertIn("FLIGHT SIMULATORS", flight)
        self.assertIn("Shared cockpit", flight)
        self.assertEqual(flight, render_template("wefly_back_a4.html", {"gate": "Boeing 737 MAX"}))
        racing = render_template("wefly_back_a4.html", {"gate": "Formula 1"})
        self.assertIn("FORMULA 1 SIMULATOR", racing)
        self.assertIn("Minimum height: 4 ft 0 in", racing)
        self.assertNotIn("flight", body_of(racing).lower())
        self.assertNotEqual(back_cover_a4_path("formula1"), back_cover_a4_path("boeing737"))
        self.assertEqual(back_cover_a4_path(None), back_cover_a4_path("Airbus A320"))

    def test_every_file_a_template_points_at_exists(self):
        """A missing photo, icon or font would only show up as a hole in the printed card."""
        for template in ALL_TEMPLATES:
            for simulator in ("boeing737", "formula1"):
                params = get_template_params(simulator, "50", "PDLEDC", "2027-09-22", True)
                html = uncomment_christmas_block(read_template(template))
                html = env.from_string(html).render(params)
                refs = set(re.findall(r'src="((?:images|fonts)/[^"]+)"', html))
                refs |= set(re.findall(r"url\('((?:images|fonts)/[^']+)'\)", html))
                self.assertTrue(refs, template)
                for ref in refs:
                    with self.subTest(template=template, simulator=simulator, ref=ref):
                        self.assertTrue(os.path.isfile(os.path.join(TEMPLATE_PATH, ref)), ref)


class ChristmasThemeTests(unittest.TestCase):
    def test_switch_script_covers_the_templates_in_use(self):
        self.assertEqual(sorted(TEMPLATE_FILES), sorted(FRONT_TEMPLATES))

    def test_greeting_turns_on_and_back_off(self):
        for template in TEMPLATE_FILES:
            with self.subTest(template=template):
                source = read_template(template)
                self.assertEqual(comment_christmas_block(source), source, "theme should ship switched off")
                festive = uncomment_christmas_block(source)
                self.assertNotEqual(festive, source)
                self.assertEqual(comment_christmas_block(festive), source)

                params = get_template_params("boeing737", "50", "PDLEDC", "2027-09-22", False)
                self.assertIn("Merry Christmas", env.from_string(festive).render(params))
                self.assertNotIn("Merry Christmas", env.from_string(source).render(params))
                birthday = dict(params, is_birthday=True)
                self.assertIn("Happy Birthday!", env.from_string(festive).render(birthday))
                self.assertNotIn("Merry Christmas", env.from_string(festive).render(birthday))


if __name__ == "__main__":
    unittest.main()
