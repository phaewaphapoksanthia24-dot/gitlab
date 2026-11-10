import unittest

from bias import BiasInput, BiasInputError, OperatingPoint, analyze_bias, parse_inputs, points_agree

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}


def errors_for(**overrides):
    raw = dict(VALID, **overrides)
    with unittest.TestCase().assertRaises(BiasInputError) as ctx:
        parse_inputs(raw)
    return ctx.exception.errors


class TestParseInputs(unittest.TestCase):
    def test_valid_inputs_become_floats(self):
        data = parse_inputs(VALID)
        self.assertEqual(data.vcc, 12.0)
        self.assertEqual(data.r1, 47000.0)
        self.assertEqual(data.beta, 100.0)

    def test_missing_field_is_reported(self):
        raw = dict(VALID)
        del raw["rc"]
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs(raw)
        self.assertEqual(ctx.exception.errors["rc"], "กรุณากรอกค่านี้")

    def test_empty_field_is_reported(self):
        self.assertEqual(errors_for(r1="   ")["r1"], "กรุณากรอกค่านี้")

    def test_non_numeric_field_is_reported(self):
        self.assertEqual(errors_for(vcc="สิบสอง")["vcc"], "ต้องเป็นตัวเลข")

    def test_comma_separated_number_is_rejected(self):
        self.assertEqual(errors_for(r1="47,000")["r1"], "ต้องเป็นตัวเลข")

    def test_non_finite_values_are_rejected(self):
        for value in ("nan", "inf", "1e309"):
            with self.subTest(value=value):
                self.assertEqual(errors_for(re=value)["re"], "ต้องเป็นตัวเลขจำกัด")

    def test_zero_and_negative_resistances_are_rejected(self):
        for field in ("r1", "r2", "rc", "re"):
            for value in ("0", "-1"):
                with self.subTest(field=field, value=value):
                    self.assertEqual(errors_for(**{field: value})[field], "ต้องมากกว่า 0")

    def test_non_positive_vcc_is_rejected(self):
        self.assertEqual(errors_for(vcc="0")["vcc"], "ต้องมากกว่า 0")

    def test_non_positive_beta_is_rejected(self):
        for value in ("0", "-5"):
            with self.subTest(value=value):
                self.assertEqual(errors_for(beta=value)["beta"], "beta ต้องมากกว่า 0")

    def test_negative_vbe_is_rejected(self):
        self.assertEqual(errors_for(vbe="-0.1")["vbe"], "VBE ต้องไม่ติดลบ")

    def test_vbe_must_be_below_vcc(self):
        self.assertEqual(errors_for(vbe="12")["vbe"], "VBE ต้องน้อยกว่า VCC")

    def test_all_errors_are_collected(self):
        errors = errors_for(vcc="0", beta="-1", vbe="abc")
        self.assertEqual(set(errors), {"vcc", "beta", "vbe"})

    def test_fractional_beta_is_accepted(self):
        self.assertEqual(parse_inputs(dict(VALID, beta="100.5")).beta, 100.5)


def make_input(**overrides):
    base = dict(vcc=12.0, r1=47000.0, r2=10000.0, rc=4700.0, re=1000.0, beta=100.0, vbe=0.7)
    base.update(overrides)
    return BiasInput(**base)


class TestPrimaryCalculation(unittest.TestCase):
    def test_active_region_values(self):
        result = analyze_bias(make_input())
        self.assertEqual(result.region, "active")
        self.assertAlmostEqual(result.primary.vb, 1.9991970451, delta=1e-9)
        self.assertAlmostEqual(result.primary.ve, 1.2991970451, delta=1e-9)
        self.assertAlmostEqual(result.primary.vc, 5.9542315722, delta=1e-9)
        self.assertAlmostEqual(result.primary.vce, 4.6550345271, delta=1e-9)
        self.assertAlmostEqual(result.primary.ib, 1.2863337080e-5, delta=1e-11)
        self.assertAlmostEqual(result.primary.ic, 1.2863337080e-3, delta=1e-9)
        self.assertAlmostEqual(result.primary.ie, 1.299197e-3, delta=1e-9)

    def test_active_region_has_no_warnings(self):
        self.assertEqual(analyze_bias(make_input()).warnings, ())

    def test_cutoff_clamps_currents_and_reports_zero(self):
        result = analyze_bias(make_input(vcc=5.0, r1=100000.0, r2=10000.0, rc=2200.0))
        self.assertEqual(result.region, "cutoff")
        self.assertAlmostEqual(result.primary.vb, 0.4545454545, delta=1e-9)
        self.assertEqual(result.primary.ve, 0.0)
        self.assertEqual(result.primary.vc, 5.0)
        self.assertEqual(result.primary.vce, 5.0)
        self.assertEqual(result.primary.ib, 0.0)
        self.assertEqual(result.primary.ic, 0.0)
        self.assertEqual(result.primary.ie, 0.0)
        self.assertIsNone(result.independent)
        self.assertIsNone(result.agreement_ok)
        self.assertIn("cutoff", result.warnings[0])

    def test_saturation_is_detected_and_values_stay_unclamped(self):
        result = analyze_bias(make_input(rc=10000.0))
        self.assertEqual(result.region, "saturation")
        self.assertAlmostEqual(result.primary.vce, -2.1625341256, delta=1e-9)
        self.assertAlmostEqual(result.primary.vc, -0.8633370805, delta=1e-9)
        self.assertTrue(any("saturation" in w for w in result.warnings))

    def test_non_stiff_divider_gets_a_warning(self):
        result = analyze_bias(make_input(r1=10000.0, r2=10000.0, rc=100.0, re=47.0))
        self.assertEqual(result.region, "active")
        self.assertTrue(any("10 เท่า" in w for w in result.warnings))

    def test_stiff_divider_gets_no_warning(self):
        self.assertFalse(any("10 เท่า" in w for w in analyze_bias(make_input()).warnings))


class TestIndependentCalculation(unittest.TestCase):
    def test_independent_method_matches_known_values(self):
        result = analyze_bias(make_input())
        self.assertIsNotNone(result.independent)
        self.assertAlmostEqual(result.independent.ve, 1.2991970451, delta=1e-9)
        self.assertAlmostEqual(result.independent.vb, 1.9991970451, delta=1e-9)
        self.assertAlmostEqual(result.independent.vc, 5.9542315722, delta=1e-9)
        self.assertAlmostEqual(result.independent.ic, 1.2863337080e-3, delta=1e-9)

    def test_methods_agree_across_parameter_sweep(self):
        cases = [
            dict(),
            dict(beta=50.0),
            dict(beta=200.0),
            dict(vcc=22.0, r1=22000.0, r2=4700.0, rc=2200.0, re=470.0, beta=200.0, vbe=0.65),
            dict(rc=10000.0),
        ]
        for overrides in cases:
            with self.subTest(**overrides):
                result = analyze_bias(make_input(**overrides))
                self.assertIsNotNone(result.independent)
                self.assertTrue(result.agreement_ok)
                self.assertFalse(any("ไม่ตรงกัน" in w for w in result.warnings))

    def test_points_agree_rejects_mismatch(self):
        a = OperatingPoint(vb=1.0, ve=1.0, vc=1.0, vce=1.0, ib=1.0, ic=1.0, ie=1.0)
        b = OperatingPoint(vb=1.0, ve=1.0, vc=1.0, vce=1.0, ib=1.0, ic=1.0, ie=1.01)
        self.assertTrue(points_agree(a, a))
        self.assertFalse(points_agree(a, b))


if __name__ == "__main__":
    unittest.main()
