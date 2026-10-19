import unittest
import pandas as pd
from core.engine import generate_defects, simulate_mfl, detect_indications


class TestEngine(unittest.TestCase):
    def test_defects_are_reproducible(self):
        a = [d.as_dict() for d in generate_defects(1000, seed=7, count=5)]
        b = [d.as_dict() for d in generate_defects(1000, seed=7, count=5)]
        self.assertEqual(a, b)
        self.assertEqual(len(a), 5)

    def test_simulation_shape_and_columns(self):
        frame, defects, meta = simulate_mfl(length_m=500, sample_count=100, channels=4, seed=3, defect_count=2)
        self.assertEqual(len(frame), 100)
        self.assertIn("magnitude", frame.columns)
        self.assertEqual(len(meta["channel_columns"]), 4)
        self.assertEqual(len(defects), 2)
        self.assertTrue(frame["distance_m"].is_monotonic_increasing)

    def test_failed_channel_is_zero(self):
        frame, _, _ = simulate_mfl(length_m=300, sample_count=100, channels=4, failed_channel=2)
        self.assertTrue((frame["ch_03"] == 0).all())

    def test_detector_empty_and_hits(self):
        empty = pd.DataFrame({"distance_m": [0, 1, 2], "magnitude": [0.0, 0.1, 0.2]})
        self.assertTrue(detect_indications(empty, threshold=0.5).empty)
        hits = pd.DataFrame({"distance_m": [0, 1, 2, 10], "magnitude": [0.1, 0.8, 0.7, 0.9]})
        result = detect_indications(hits, threshold=0.5, min_separation_m=3)
        self.assertEqual(len(result), 2)

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            simulate_mfl(length_m=0)
        with self.assertRaises(ValueError):
            simulate_mfl(sample_count=10)


if __name__ == "__main__":
    unittest.main()
