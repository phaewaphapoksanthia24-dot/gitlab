import unittest
from electrical import analyze_dc, analyze_network, parse_branches


class TestDCAnalyzer(unittest.TestCase):
    def test_known_values(self):
        result = analyze_dc(12, 6)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)

    def test_zero_voltage(self):
        result = analyze_dc(0, 10)
        self.assertAlmostEqual(result["current_a"], 0.0)
        self.assertAlmostEqual(result["power_w"], 0.0)

    def test_rejects_nonpositive_resistance(self):
        for resistance in (0, -1):
            with self.subTest(resistance=resistance):
                with self.assertRaises(ValueError):
                    analyze_dc(12, resistance)

    def test_rejects_nonfinite_inputs(self):
        for voltage, resistance in ((float("nan"), 10), (12, float("inf"))):
            with self.subTest(voltage=voltage, resistance=resistance):
                with self.assertRaises(ValueError):
                    analyze_dc(voltage, resistance)


class TestDCNetwork(unittest.TestCase):
    def test_series_and_parallel_network(self):
        result = analyze_network(12, [[10, 20], [30]])
        self.assertAlmostEqual(result["equivalent_resistance_ohm"], 15.0)
        self.assertAlmostEqual(result["total_current_a"], 0.8)
        self.assertAlmostEqual(result["total_power_w"], 9.6)
        self.assertAlmostEqual(result["branches"][0]["current_a"], 0.4)
        self.assertAlmostEqual(result["branches"][0]["resistors"][0]["voltage_v"], 4.0)

    def test_parse_branches(self):
        self.assertEqual(parse_branches("10, 20; 30"), [[10.0, 20.0], [30.0]])

    def test_rejects_invalid_network_values(self):
        for branches in ([], [[]], [[0]], [[-1]], [[float("nan")]]):
            with self.subTest(branches=branches):
                with self.assertRaises(ValueError):
                    analyze_network(12, branches)

    def test_rejects_nonfinite_voltage(self):
        with self.assertRaises(ValueError):
            analyze_network(float("inf"), [[10]])


if __name__ == "__main__":
    unittest.main()