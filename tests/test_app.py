import re
import unittest

from app import app


class TestFormPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_prefills_the_example_circuit(self):
        body = self.client.get("/").get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)
        self.assertIn('value="12.0"', body)
        self.assertIn('value="100"', body)

    def test_index_has_unit_selectors(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('name="r1_unit"', body)
        self.assertIn('name="vcc_unit"', body)
        self.assertIn("kΩ", body)
        self.assertIn("mV", body)

    def test_index_shows_schematic_and_empty_results(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("Common-Emitter Amplifier", body)
        self.assertIn("Q1", body)
        self.assertIn("DC Bias Results", body)
        self.assertIn("Run the calculation", body)

    def test_stylesheet_is_served(self):
        response = self.client.get("/static/style.css")
        self.assertEqual(response.status_code, 200)
        response.close()


VALID_FORM = {
    "vcc": "12",
    "vcc_unit": "V",
    "r1": "100",
    "r1_unit": "kΩ",
    "r2": "22",
    "r2_unit": "kΩ",
    "rc": "2.2",
    "rc_unit": "kΩ",
    "re": "1.0",
    "re_unit": "kΩ",
    "beta": "100",
    "vbe": "0.7",
    "vbe_unit": "V",
}


class TestCalculateRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, **overrides):
        data = dict(VALID_FORM, **overrides)
        return self.client.post("/calculate", data=data)

    def test_valid_post_shows_operating_point(self):
        body = self.post().get_data(as_text=True)
        self.assertIn("Active region approximation OK", body)
        self.assertIn("1.94", body)  # VB
        self.assertIn("µA", body)
        self.assertIn("mA", body)

    def test_unit_selector_changes_the_calculation(self):
        body = self.post(r1="100000", r1_unit="Ω").get_data(as_text=True)
        self.assertIn("1.94", body)

    def test_cross_check_reports_agreement(self):
        body = self.post().get_data(as_text=True)
        self.assertIn("Thevenin", body)
        self.assertIn("agree", body)

    def test_delta_is_snapped_to_zero(self):
        body = self.post().get_data(as_text=True)
        self.assertNotIn("e-15", body)
        self.assertNotIn("e-16", body)

    def test_invalid_post_shows_error_and_keeps_values(self):
        body = self.post(r1="0").get_data(as_text=True)
        self.assertIn("Must be greater than 0.", body)
        self.assertIn('value="2.2"', body)

    def test_missing_field_shows_required_error(self):
        data = dict(VALID_FORM)
        del data["beta"]
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("This field is required.", body)

    def test_cutoff_shows_region_banner_and_values(self):
        body = self.post(vcc="5", r1="100", r2="10", rc="2.2").get_data(as_text=True)
        compact = re.sub(r"\s+", "", body)
        self.assertIn("Cutoff region", body)
        self.assertIn("<td>IB</td><td>0.0µA</td>", compact)
        self.assertIn("<td>VCE</td><td>5.00V</td>", compact)

    def test_saturation_shows_warning(self):
        body = self.post(rc="10").get_data(as_text=True)
        self.assertIn("Saturation region", body)
        self.assertIn("approximate", body)

    def test_non_stiff_divider_shows_warning(self):
        body = self.post(r1="10", r2="10", rc="0.1", re="0.047").get_data(as_text=True)
        self.assertIn("not stiff", body)


if __name__ == "__main__":
    unittest.main()
