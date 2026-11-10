import re
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
        response = self.client.get("/static/style.css")
        self.assertEqual(response.status_code, 200)
        response.close()


VALID_FORM = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}


class TestCalculateRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, **overrides):
        data = dict(VALID_FORM, **overrides)
        return self.client.post("/calculate", data=data)

    def test_valid_post_shows_operating_point_and_comparison(self):
        body = self.post().get_data(as_text=True)
        self.assertIn("Active", body)
        self.assertIn("1.999", body)  # VB
        self.assertIn("12.86", body)  # IB เป็น µA
        self.assertIn("Thevenin", body)
        self.assertIn("Nodal", body)
        self.assertNotIn('class="error"', body)

    def test_invalid_post_shows_error_and_keeps_valid_values(self):
        body = self.post(r1="0").get_data(as_text=True)
        self.assertIn("ต้องมากกว่า 0", body)
        self.assertIn('value="4700"', body)  # RC ที่กรอกถูกต้องยังอยู่
        self.assertNotIn("Thevenin", body)

    def test_missing_field_shows_required_error(self):
        data = dict(VALID_FORM)
        del data["beta"]
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("กรุณากรอกค่านี้", body)

    def test_cutoff_shows_note_instead_of_comparison(self):
        body = self.post(vcc="5", r1="100000", r2="10000", rc="2200").get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("ไม่เทียบผล", body)
        self.assertNotIn("Thevenin", body)

    def test_cutoff_still_shows_the_operating_point_values(self):
        body = self.post(vcc="5", r1="100000", r2="10000", rc="2200").get_data(as_text=True)
        compact = re.sub(r"\s+", "", body)
        self.assertIn("<td>IB</td><td>µA</td><td>0</td>", compact)
        self.assertIn("<td>IC</td><td>mA</td><td>0</td>", compact)
        self.assertIn("<td>VCE</td><td>V</td><td>5</td>", compact)

    def test_saturation_shows_warning(self):
        body = self.post(rc="10000").get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("active region", body)

    def test_non_stiff_divider_shows_warning(self):
        body = self.post(r1="10000", r2="10000", rc="100", re="47").get_data(as_text=True)
        self.assertIn("10 เท่า", body)


if __name__ == "__main__":
    unittest.main()
