import unittest

from bias import BiasInputError, parse_inputs

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


if __name__ == "__main__":
    unittest.main()
