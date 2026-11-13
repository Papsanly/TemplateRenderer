import base64
import os
import re
import unittest

import qrcode

from renderer.config import TEMPLATE_PATH
from renderer.template import env, get_context_keys, render_template
from scripts.switch_theme import TEMPLATE_FILES, comment_christmas_block, uncomment_christmas_block
from server import (
    build_activation_url,
    generate_qr_code,
    get_template_name,
    get_template_params,
    map_duration_to_seat_class,
)

FRONT_TEMPLATES = ("aviasim_certificate.html", "aviasim_certificate_a4.html")
ALL_TEMPLATES = FRONT_TEMPLATES + ("aviasim_back.html", "aviasim_back_a4.html")

# What the site sends: the simulator's display name and one of its two plan lengths.
SITE_PLANS = [("Boeing 737", 60), ("Boeing 737", 120), ("F/A-18 Hornet", 50),
              ("F/A-18 Hornet", 100), ("Cessna", 30), ("Cessna", 50)]


def render_front(template, simulator="Boeing 737", duration="60", is_birthday=False,
                 code="7K2M9Q", expiration="2027-01-30"):
    params = get_template_params(simulator, duration, code, expiration, is_birthday)
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
        self.assertEqual(build_activation_url("7K2M9Q"), "https://aviasim.com.ua/activate/7K2M9Q")
        self.assertEqual(build_activation_url(" 7K2M9Q "), "https://aviasim.com.ua/activate/7K2M9Q")

    def test_link_escapes_characters_that_would_break_the_url(self):
        self.assertEqual(build_activation_url("A B/C?D#E"), "https://aviasim.com.ua/activate/A%20B%2FC%3FD%23E")

    def test_qr_image_encodes_that_link_with_a_quiet_zone(self):
        for code in ("7K2M9Q", "HORNET18", "BODO-ABCD-1234-XY"):
            with self.subTest(code=code):
                expected = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
                expected.add_data(f"https://aviasim.com.ua/activate/{code}")
                expected.make(fit=True)
                matrix = qr_modules_from_data_uri(generate_qr_code(code))
                self.assertEqual(matrix, expected.get_matrix())
                # Four light modules on every side, so the code scans on any background.
                self.assertFalse(any(any(row) for row in matrix[:4] + matrix[-4:]))
                self.assertFalse(any(any(row[:4]) or any(row[-4:]) for row in matrix))

    def test_each_code_gets_its_own_qr_in_the_rendered_card(self):
        for template in FRONT_TEMPLATES:
            with self.subTest(template=template):
                first = render_front(template, code="AAAAAA")
                second = render_front(template, code="BBBBBB")
                self.assertIn(generate_qr_code("AAAAAA"), first)
                self.assertIn(generate_qr_code("BBBBBB"), second)
                self.assertNotIn(generate_qr_code("AAAAAA"), second)


class SeatClassTests(unittest.TestCase):
    def test_every_plan_on_sale_gets_a_class(self):
        for duration, expected in [(30, "Економ-клас"), (50, "Бізнес-клас"), (60, "Бізнес-клас"),
                                   (100, "Перший клас"), (120, "Перший клас")]:
            with self.subTest(duration=duration):
                self.assertEqual(map_duration_to_seat_class(duration), expected)

    def test_a_plan_length_added_later_still_gets_one(self):
        self.assertEqual(map_duration_to_seat_class(20), "Економ-клас")
        self.assertEqual(map_duration_to_seat_class(45), "Бізнес-клас")
        self.assertEqual(map_duration_to_seat_class(90), "Перший клас")


class GiftCertificateTemplateTests(unittest.TestCase):
    def test_one_template_per_format(self):
        self.assertEqual(get_template_name(a4=True), "aviasim_certificate_a4.html")
        self.assertEqual(get_template_name(a4=False), "aviasim_certificate.html")

    def test_pass_shows_what_was_bought(self):
        for simulator, duration in SITE_PLANS:
            for template in FRONT_TEMPLATES:
                with self.subTest(simulator=simulator, duration=duration, template=template):
                    html = body_of(render_front(template, simulator, str(duration)))
                    self.assertIn("ПОСАДКОВИЙ ТАЛОН", html)
                    self.assertIn(f'<span class="pass__value">{simulator}</span>', html)
                    self.assertIn(f'<span class="pass__value">{duration} хв</span>', html)
                    self.assertIn(f'<span class="pass__value">{map_duration_to_seat_class(duration)}</span>', html)
                    self.assertIn(">7K2M9Q</span>", html)

    def test_simulator_keys_are_accepted_as_well_as_names(self):
        for key, gate in [("boeing737", "Boeing 737"), ("f18", "F/A-18 Hornet"), ("cessna", "Cessna"),
                          ("CESSNA", "Cessna")]:
            with self.subTest(key=key):
                self.assertIn(f'<span class="pass__value">{gate}</span>',
                              body_of(render_front("aviasim_certificate_a4.html", key)))

    def test_expiry_date_is_printed_the_ukrainian_way(self):
        for sent, printed in [("2027-01-30", "30.01.2027"), ("2027-11-14T00:00:00.000Z", "14.11.2027")]:
            for template in FRONT_TEMPLATES:
                with self.subTest(sent=sent, template=template):
                    html = body_of(render_front(template, expiration=sent))
                    self.assertIn("ДІЙСНИЙ ДО", html)
                    self.assertIn(f'<span class="pass__value">{printed}</span>', html)
                    self.assertNotIn("ТЕРМІН ДІЇ", html)

    def test_without_a_date_the_pass_states_the_term_instead_of_inventing_one(self):
        for template in FRONT_TEMPLATES:
            for expiration in (None, ""):
                with self.subTest(template=template, expiration=expiration):
                    html = body_of(render_front(template, expiration=expiration))
                    self.assertIn("ТЕРМІН ДІЇ", html)
                    self.assertIn('<span class="pass__value">1 рік</span>', html)
                    self.assertNotIn("ДІЙСНИЙ ДО", html)
                    self.assertIsNone(re.search(r"\d{2}[./]\d{2}[./]\d{4}", html))

    def test_birthday_greeting_only_when_asked(self):
        for template in FRONT_TEMPLATES:
            with self.subTest(template=template):
                self.assertIn("З днем народження!", body_of(render_front(template, is_birthday=True)))
                self.assertNotIn("pass__greeting", body_of(render_front(template)))

    def test_long_codes_step_down_in_size(self):
        for code, css_class in [("7K2M9Q", 'class="pass__code"'), ("HORNET18", 'class="pass__code"'),
                                ("ELEVENCHARS", "pass__code--long"), ("BODO-ABCD-1234-XY", "pass__code--xlong"),
                                ("A-VERY-LONG-PARTNER-VOUCHER-CODE", "pass__code--xxlong")]:
            with self.subTest(code=code):
                self.assertIn(f"{css_class}", render_front("aviasim_certificate_a4.html", code=code))

    def test_cli_and_bot_still_see_the_card_fields(self):
        """These are the keys main.py and the bot ask for, and the ones a render refuses to go without."""
        for template in FRONT_TEMPLATES:
            with self.subTest(template=template):
                keys = {key.name for key in get_context_keys(template)}
                self.assertEqual(keys, {"code", "qr_code", "gate", "duration", "seat_class"})

    def test_expiration_is_optional_for_a_render(self):
        params = get_template_params("Boeing 737", "60", "7K2M9Q", None, False)
        del params["expiration"]
        for template in FRONT_TEMPLATES:
            with self.subTest(template=template):
                self.assertIn("ТЕРМІН ДІЇ", render_template(template, params))

    def test_rules_page_covers_all_three_simulators_and_needs_no_context(self):
        rules = render_template("aviasim_back_a4.html", {})
        for expected in ("Обмеження", "Boeing 737", "F/A-18", "Cessna", "110 кг", "ВІК ДИТИНИ", "VR-ШОЛОМ",
                         "Сертифікат дійсний 1 рік з дати покупки"):
            with self.subTest(expected=expected):
                self.assertIn(expected, rules)

    def test_nothing_from_the_wefly_card_leaks_in(self):
        for template in ALL_TEMPLATES:
            with self.subTest(template=template):
                html = body_of(render_front(template, is_birthday=True)).lower()
                for foreign in ("wefly", "pasadena", "formula", "(844)", "gift card"):
                    self.assertNotIn(foreign, html)

    def test_every_file_a_template_points_at_exists(self):
        """A missing photo, icon or font would only show up as a hole in the printed certificate."""
        for template in ALL_TEMPLATES:
            params = get_template_params("Boeing 737", "60", "7K2M9Q", "2027-01-30", True)
            html = uncomment_christmas_block(read_template(template))
            html = env.from_string(html).render(params)
            refs = set(re.findall(r'src="((?:images|fonts)/[^"]+)"', html))
            refs |= set(re.findall(r"url\('((?:images|fonts)/[^']+)'\)", html))
            self.assertTrue(refs, template)
            for ref in refs:
                with self.subTest(template=template, ref=ref):
                    self.assertTrue(os.path.isfile(os.path.join(TEMPLATE_PATH, ref)), ref)

    def test_the_bundled_font_covers_ukrainian(self):
        """The Latin subset alone would print Cyrillic in whatever font the server has."""
        css = read_template("partials/aviasim_gift.css")
        self.assertIn("fonts/Manrope-cyrillic.woff2", css)
        cyrillic = css.split("fonts/Manrope-cyrillic.woff2")[1].split("}")[0]
        for needed in ("U+0400-045F", "U+0490-0491"):  # А-я with і, ї, є; and ґ
            self.assertIn(needed, cyrillic)


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

                params = get_template_params("Boeing 737", "60", "7K2M9Q", "2027-01-30", False)
                self.assertIn("З Новим роком і Різдвом!", env.from_string(festive).render(params))
                self.assertNotIn("З Новим роком", env.from_string(source).render(params))
                birthday = dict(params, is_birthday=True)
                self.assertIn("З днем народження!", env.from_string(festive).render(birthday))
                self.assertNotIn("З Новим роком", env.from_string(festive).render(birthday))


if __name__ == "__main__":
    unittest.main()
