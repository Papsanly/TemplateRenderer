import unittest

from server import get_template_params, map_duration_to_seat_class
from renderer.template import render_template


class GiftCardClassTests(unittest.TestCase):
    def test_current_and_legacy_plans(self):
        for duration, expected in [(30, "Economy Class"), (50, "Business Class"),
                                   (60, "Business Class"), (110, "First Class"),
                                   (120, "First Class")]:
            with self.subTest(duration=duration):
                self.assertEqual(map_duration_to_seat_class(duration), expected)

    def test_current_classes_on_both_flight_certificate_sizes(self):
        for simulator in ("boeing737", "airbus320", "Boeing 737 MAX", "Airbus A320"):
            for duration, expected in [(50, "Business Class"), (110, "First Class")]:
                for template in ("wefly_certificate.html", "wefly_certificate_a4.html"):
                    with self.subTest(simulator=simulator, duration=duration, template=template):
                        params = get_template_params(simulator, str(duration), "TEST-CLASS", "2027-09-22", False)
                        html = render_template(template, params)
                        self.assertIn(expected, html)
                        self.assertNotIn("Economy Class", html)
                        self.assertEqual(params["duration"], str(duration))
                        self.assertEqual(params["code"], "TEST-CLASS")
                        self.assertEqual(params["expiration"], "09/22/2027")


if __name__ == "__main__":
    unittest.main()
