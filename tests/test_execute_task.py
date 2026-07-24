import unittest
from engine.execute_task import document_target, validate_agent_scope
from engine.json_protocol import ProtocolError


class TestExecuteTask(unittest.TestCase):
    def test_document_target_department(self):
        target = document_target("dept-02-product-planning", "tasks/projects/ilk-projem")
        self.assertEqual(
            target,
            "tasks/projects/ilk-projem/.company/departments/dept-02-product-planning.md",
        )

    def test_validate_agent_scope_allowed(self):
        request_text = "Analysis request for `tasks/projects/ilk-projem`"
        actions = [
            {
                "op": "write",
                "path": "tasks/projects/ilk-projem/.company/departments/dept-02-product-planning.md",
                "content": "sample content",
            }
        ]
        validate_agent_scope("dept-02-product-planning", request_text, actions)

    def test_validate_agent_scope_forbidden_path(self):
        request_text = "Analysis request for `tasks/projects/ilk-projem`"
        forbidden_actions = [
            {
                "op": "write",
                "path": "tasks/projects/ilk-projem/.company/PROJECT_STATE.json",
                "content": "corrupted content",
            }
        ]
        with self.assertRaises(ProtocolError):
            validate_agent_scope("dept-02-product-planning", request_text, forbidden_actions)

    def test_validate_agent_scope_multiple_actions(self):
        request_text = "Analysis request for `tasks/projects/ilk-projem`"
        multiple_actions = [
            {
                "op": "write",
                "path": "tasks/projects/ilk-projem/.company/departments/dept-02-product-planning.md",
                "content": "valid content",
            },
            {
                "op": "write",
                "path": "tasks/projects/ilk-projem/.company/AI_ANALYSIS.json",
                "content": "extra write",
            },
        ]
        with self.assertRaises(ProtocolError):
            validate_agent_scope("dept-02-product-planning", request_text, multiple_actions)


if __name__ == "__main__":
    unittest.main()
