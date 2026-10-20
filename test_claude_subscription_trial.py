import copy
import unittest

from claude_subscription_trial import MODEL, parse_execution


class ClaudeTrialTests(unittest.TestCase):
    def setUp(self):
        self.messages = [
            {"type": "system", "subtype": "init", "model": MODEL},
            {"type": "result", "subtype": "success", "is_error": False,
             "num_turns": 1, "result": '{"approve":true,"reason":"근거 확인"}'},
        ]

    def test_accepts_complete_approval(self):
        self.assertIs(parse_execution(self.messages)["approve"], True)

    def test_rejection_is_a_valid_vote(self):
        self.messages[-1]["result"] = '{"approve":false,"reason":"수치 근거 부족"}'
        self.assertIs(parse_execution(self.messages)["approve"], False)

    def test_operational_failures_cannot_be_votes(self):
        for change in ({"is_error": True}, {"subtype": "error_max_turns"},
                       {"result": '{"approve":'}, {"num_turns": 3},
                       {"result": '{"approve":"true","reason":"x"}'}):
            with self.subTest(change=change):
                messages = copy.deepcopy(self.messages)
                messages[-1].update(change)
                with self.assertRaises(ValueError):
                    parse_execution(messages)

    def test_wrong_model_and_missing_result_rejected(self):
        for messages in (self.messages[:1], [self.messages[0], self.messages[-1], self.messages[-1]],
                         [{"type": "system", "subtype": "init", "model": "other"}, self.messages[-1]]):
            with self.assertRaises(ValueError):
                parse_execution(messages)

    def test_tool_calls_rejected(self):
        self.messages.insert(1, {"type": "assistant", "message": {
            "content": [{"type": "tool_use", "name": "Bash"}]}})
        with self.assertRaises(ValueError):
            parse_execution(self.messages)


if __name__ == "__main__":
    unittest.main()
