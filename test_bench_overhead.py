import runpy
import unittest
from pathlib import Path

mock = runpy.run_path(str(Path(__file__).with_name("stressmock.py")), run_name="stressmock")
pick_terminal = mock["pick_terminal"]

repro = runpy.run_path(str(Path(__file__).with_name("reproduce.py")), run_name="reproduce")
measurable = repro["measurable"]


class RunawayGuard(unittest.TestCase):
    def test_runs_past_the_scenario_are_not_used_for_per_turn_cpu(self):
        ok, looped = measurable([{"turns": 41}, {"turns": 16900}, {"turns": 40}])
        self.assertEqual([r["turns"] for r in ok], [41, 40])
        self.assertEqual([r["turns"] for r in looped], [16900])

    def test_a_few_extra_requests_are_still_a_valid_run(self):
        ok, looped = measurable([{"turns": 41}, {"turns": 50}])
        self.assertEqual(len(ok), 2)
        self.assertEqual(looped, [])


def terminal_body(*names):
    return {"tools": [{"type": "function", "function": {"name": n, "parameters": {"type": "object"}}}
                      for n in names]}


class CompletionTool(unittest.TestCase):
    def test_a_sub_agent_control_tool_is_not_a_completion_tool(self):
        # crush has `agent_stop`, whose `_stop` suffix used to make the mock
        # call it on every turn after the scenario ended: the run never finished.
        self.assertIsNone(pick_terminal(terminal_body("agent_stop")))
        self.assertIsNone(pick_terminal(terminal_body("job_kill", "agent_stop")))

    def test_a_real_completion_tool_is_still_used(self):
        tool = pick_terminal(terminal_body("agent_stop", "submit_and_exit"))
        self.assertEqual(tool[0], "submit_and_exit")


if __name__ == "__main__":
    unittest.main()
