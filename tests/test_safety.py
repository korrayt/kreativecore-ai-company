from pathlib import Path
import pytest
from engine.safety import SafetyError, apply_actions, safe_relative_path

def test_escape():
    with pytest.raises(SafetyError):
        safe_relative_path('../secret')

def test_protected(tmp_path: Path):
    with pytest.raises(SafetyError):
        apply_actions(tmp_path, [{"op": "write", "path": "engine/x.py", "content": "x"}], protected_prefixes=["engine/"], max_files=2, max_bytes=10)

def test_write(tmp_path: Path):
    result = apply_actions(tmp_path, [{"op": "write", "path": "src/a.py", "content": "x"}], protected_prefixes=["engine/"], max_files=2, max_bytes=10)
    assert result == ["src/a.py"]
