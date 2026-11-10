import unittest

from app import app


class TestFormPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_form_with_all_fields(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)

    def test_index_shows_title_and_units(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("BJT", body)
        self.assertIn("VCC", body)
        self.assertIn("µA", body)

    def test_stylesheet_is_served(self):
        self.assertEqual(self.client.get("/static/style.css").status_code, 200)


if __name__ == "__main__":
    unittest.main()
