import tempfile
import unittest
from pathlib import Path
from data.database import initialize, save_run, list_runs


class TestDatabase(unittest.TestCase):
    def test_save_and_list_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            initialize(db)
            run = {"operator": "Test", "scenario": "A", "seed": 12, "length_m": 1000,
                   "speed_m_s": 1.0, "channels": 8, "reference_defects": 4,
                   "detected_indications": 3, "threshold": 0.3, "metadata": {"test": True}}
            run_id = save_run(run, db)
            rows = list_runs(db)
            self.assertEqual(run_id, 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["operator"], "Test")


if __name__ == "__main__":
    unittest.main()
