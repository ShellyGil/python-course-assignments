import unittest

from day03 import pcr_logic


class TestPcrLogic(unittest.TestCase):
    def test_per_sample_volumes_for_supported_mixes(self):
        per_two_x = pcr_logic.per_sample_volumes(2)
        per_five_x = pcr_logic.per_sample_volumes(5)

        self.assertAlmostEqual(per_two_x["DDW (µL)"], 4.0)
        self.assertAlmostEqual(per_two_x["Mix 2X (µL)"], 6.0)
        self.assertAlmostEqual(per_two_x["Primer F (µL)"], 0.5)
        self.assertAlmostEqual(per_two_x["Primer R (µL)"], 0.5)

        self.assertAlmostEqual(per_five_x["Mix 5X (µL)"], 2.4)
        self.assertAlmostEqual(per_five_x["DDW (µL)"], 7.6)

    def test_compute_totals_respects_rounding(self):
        per, totals, total_mix = pcr_logic.compute_totals(n_samples=8, excess_percent=12.5, mix_x=2)
        self.assertEqual(totals["DDW (µL)"], 36.0)
        self.assertAlmostEqual(total_mix, sum(totals.values()))
        self.assertEqual(per["Primer F (µL)"], 0.5)

    def test_compute_totals_invalid_inputs_raise(self):
        with self.assertRaisesRegex(ValueError, "n_samples must be >= 1"):
            pcr_logic.compute_totals(n_samples=0, excess_percent=0, mix_x=2)
        with self.assertRaisesRegex(ValueError, "excess_percent must be >= 0"):
            pcr_logic.compute_totals(n_samples=1, excess_percent=-1, mix_x=2)

    def test_format_report_contains_key_details(self):
        per, totals, total_mix = pcr_logic.compute_totals(4, 5, 5)
        report = pcr_logic.format_report(4, 5, 5, per, totals, total_mix)

        self.assertIn("Samples: 4 | Excess: 5.0% | Mix: 5X", report)
        self.assertIn("TOTAL master mix", report)
        self.assertIn("Mix 5X (µL)", report)


if __name__ == "__main__":
    unittest.main()
