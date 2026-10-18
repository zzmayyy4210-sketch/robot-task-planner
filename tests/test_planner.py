import unittest
from pydantic import ValidationError
from planner import plan, validate_candidate


class PlannerTests(unittest.TestCase):
    def test_complete(self):
        result = plan("�������ϵĺ�ɫ����Ž���ߵĺ��ӡ�")
        self.assertEqual(result["object"], "red_block")
        self.assertEqual(result["target"], "left_box")
        self.assertEqual(len(result["steps"]), 5)

    def test_missing_fields_never_produces_steps(self):
        result = plan("�ѷ���Ž�����")
        self.assertEqual(len(result["questions"]), 2)
        self.assertEqual(result["steps"], [])

    def test_unsupported_and_compound(self):
        for text in ["��ˮ", "�ѻ�ɫ����Ž���ߵĺ���", "��Ҫ�Ѻ�ɫ����Ž���ߵĺ���",
                     "�Ѻ�ɫ����Ž���ߵĺ����ٻ�ԭ��", "���Թ�������ɹ�"]:
            with self.subTest(text=text):
                self.assertEqual(plan(text)["status"], "rejected")

    def test_invalid_input(self):
        for value in ["", "  ", None, 123, "x" * 501]:
            self.assertEqual(plan(value)["error"], "invalid_input")

    def test_model_output_boundary(self):
        for raw in ['not json', '{"action":"delete"}', '{"target":"unknown"}',
                    '{"object":"red_block","extra":"ignored?"}']:
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                validate_candidate(raw)


if __name__ == "__main__":
    unittest.main()
