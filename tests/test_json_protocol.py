import pytest
from engine.json_protocol import ProtocolError, extract_json, validate_code_actions

def test_json_repair():
    assert extract_json('```json\n{"status":"ok",}\n```') == {"status": "ok"}

def test_actions():
    assert len(validate_code_actions({"actions": [{"op": "write", "path": "src/a.py", "content": "x"}]})) == 1

def test_bad_action():
    with pytest.raises(ProtocolError):
        validate_code_actions({"actions": [{"op": "shell", "path": "x"}]})
