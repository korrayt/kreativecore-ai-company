import tempfile
import unittest
from pathlib import Path
from engine.safety import SafetyError, apply_actions, safe_relative_path


class TestSafety(unittest.TestCase):
    def test_escape(self):
        with self.assertRaises(SafetyError):
            safe_relative_path("../secret")

    def test_protected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with self.assertRaises(SafetyError):
                apply_actions(
                    tmp_path,
                    [{"op": "write", "path": "engine/x.py", "content": "x"}],
                    protected_prefixes=["engine/"],
                    max_files=2,
                    max_bytes=10,
                )

    def test_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            result = apply_actions(
                tmp_path,
                [{"op": "write", "path": "src/a.py", "content": "x"}],
                protected_prefixes=["engine/"],
                max_files=2,
                max_bytes=10,
            )
            self.assertEqual(result, ["src/a.py"])


if __name__ == "__main__":
    unittest.main()
