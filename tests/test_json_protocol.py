import unittest
from engine.json_protocol import (
    ProtocolError,
    extract_json,
    render_department_markdown,
    validate_code_actions,
    validate_department_document,
    validate_department_json,
)


class TestJsonProtocol(unittest.TestCase):
    def test_json_repair(self):
        self.assertEqual(extract_json('```json\n{"status":"ok",}\n```'), {"status": "ok"})

    def test_actions(self):
        self.assertEqual(
            len(validate_code_actions({"actions": [{"op": "write", "path": "src/a.py", "content": "x"}]})),
            1,
        )

    def test_bad_action(self):
        with self.assertRaises(ProtocolError):
            validate_code_actions({"actions": [{"op": "shell", "path": "x"}]})

    def test_validate_department_json_valid(self):
        valid_payload = {
            "objective": "Belirlenen urun hedeflerini analiz etmek ve yol haritasini cikarmak.",
            "required_inputs": ["Proje BRIEF dokumani", "Mevcut mimari analizi"],
            "dependencies": ["Yonetim onayi", "Teknik mimari tasarim"],
            "acceptance_criteria": ["MVP kapsaminin netlestirilmesi", "Kabul kriterlerinin belirlenmesi"],
            "risks": ["Model baglam limitinin asilmasi risk"],
            "next_task": {
                "title": "Ürün Önceliklendirme Matrisi Hazırlığı",
                "description": "MVP içindeki özelliklerin önceliklendirilmesi ve iş paketlerine bölünmesi.",
                "deliverable": "tasks/projects/ilk-projem/.company/departments/dept-02-product-planning.md",
                "done_when": ["Tüm MVP maddeleri önceliklendirildi", "Kabul kriterleri dokümante edildi"],
            },
        }
        validated = validate_department_json(valid_payload)
        self.assertEqual(validated["objective"], valid_payload["objective"])
        self.assertEqual(len(validated["required_inputs"]), 2)

    def test_validate_department_json_missing_field(self):
        invalid_payload = {
            "objective": "Short",
            "required_inputs": ["Input 1"],
            "dependencies": ["Dep 1"],
            "acceptance_criteria": ["Criteria 1"],
            "risks": [],
            "next_task": {
                "title": "Task Title",
                "description": "Task Description",
                "deliverable": "Deliverable",
                "done_when": ["Done 1"],
            },
        }
        with self.assertRaises(ProtocolError):
            validate_department_json(invalid_payload)

    def test_validate_department_json_context_dump(self):
        dump_payload = {
            "objective": "===== FILE: tasks/projects/ilk-projem/PROJECT.toml context dump test",
            "required_inputs": ["Input 1"],
            "dependencies": ["Dep 1"],
            "acceptance_criteria": ["Criteria 1"],
            "risks": ["Risk 1"],
            "next_task": {
                "title": "Task Title",
                "description": "Task Description long enough here",
                "deliverable": "Deliverable",
                "done_when": ["Done 1"],
            },
        }
        with self.assertRaises(ProtocolError):
            validate_department_json(dump_payload)

    def test_render_department_markdown_and_document_validation(self):
        payload = {
            "objective": "Belirlenen urun hedeflerini analiz etmek ve detayli yol haritasini cikarmak.",
            "required_inputs": ["Proje BRIEF dokumani", "Mevcut mimari analizi ve isterler"],
            "dependencies": ["Yonetim onayi ve stratejik hedefler", "Teknik mimari tasarim ve altyapi"],
            "acceptance_criteria": ["MVP kapsaminin netlestirilmesi ve onaylanmasi", "Kabul kriterlerinin eksiksiz dokumante edilmesi"],
            "risks": ["Model baglam limitinin asilmasi ve performans riski", "Zaman planlamasinda aksamalar"],
            "next_task": {
                "title": "Ürün Önceliklendirme Matrisi Hazırlığı",
                "description": "MVP içindeki özelliklerin önceliklendirilmesi ve detayli iş paketlerine bölünmesi.",
                "deliverable": "tasks/projects/ilk-projem/.company/departments/dept-02-product-planning.md",
                "done_when": ["Tüm MVP maddeleri önceliklendirildi", "Kabul kriterleri dokümante edildi"],
            },
        }
        markdown = render_department_markdown(payload, "Ürün ve Planlama")
        self.assertIn("# Ürün ve Planlama Raporu", markdown)
        self.assertIn("## Amaç", markdown)
        self.assertIn("## Kabul Kriterleri", markdown)

        path = "tasks/projects/ilk-projem/.company/departments/dept-02-product-planning.md"
        validate_department_document(path, markdown)


if __name__ == "__main__":
    unittest.main()
