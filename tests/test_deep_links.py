import unittest

from deep_links import parse_competition_deep_link


class ParseCompetitionDeepLinkTest(unittest.TestCase):
    def test_start_without_payload(self):
        self.assertIsNone(parse_competition_deep_link("/start"))

    def test_start_with_competition_1(self):
        self.assertEqual(parse_competition_deep_link("/start competition_1"), 1)

    def test_start_with_competition_999(self):
        self.assertEqual(parse_competition_deep_link("/start competition_999"), 999)

    def test_competition_zero(self):
        self.assertIsNone(parse_competition_deep_link("competition_0"))

    def test_competition_negative(self):
        self.assertIsNone(parse_competition_deep_link("competition_-1"))

    def test_competition_text_id(self):
        self.assertIsNone(parse_competition_deep_link("competition_test"))

    def test_competition_extra_suffix(self):
        self.assertIsNone(parse_competition_deep_link("competition_2_extra"))

    def test_extra_argument_after_payload(self):
        self.assertIsNone(parse_competition_deep_link("/start competition_2 extra"))

    def test_empty_text(self):
        self.assertIsNone(parse_competition_deep_link(""))


if __name__ == "__main__":
    unittest.main()
