import unittest

import run
import suite_plan


class Plan(unittest.TestCase):
    def test_a_sample_is_repeatable_exact_and_covers_each_tier(self):
        tasks = run.select_tasks(run.CODING_TIERS, "")
        picked = suite_plan.sample(tasks, 40, 1)
        self.assertEqual(picked, suite_plan.sample(tasks, 40, 1))
        self.assertEqual(len(picked), 40)
        self.assertEqual({run.tier_of(t) for t in picked}, set(run.CODING_TIERS))

    def test_a_sample_spreads_hard_tasks_over_projects(self):
        tasks = run.select_tasks(["hard"], "")
        picked = suite_plan.sample(tasks, 7, 1)
        families = [suite_plan.family(t) for t in picked]
        self.assertGreater(len(set(families)), 2)

    def test_every_task_lands_in_one_job_and_jobs_fit_the_limit(self):
        tasks = run.select_tasks(run.CODING_TIERS, "")
        groups = suite_plan.split(tasks, 23, 1, 20)
        self.assertEqual(sorted(sum(groups, [])), tasks)
        for g in groups:
            minutes = sum(suite_plan.MINUTES[run.tier_of(t)] for t in g) * 23
            self.assertTrue(minutes <= suite_plan.JOB_MINUTES or len(g) == 1)

    def test_a_small_run_uses_the_jobs_it_asked_for(self):
        tasks = run.select_tasks(["core"], "")[:40]
        self.assertEqual(len(suite_plan.split(tasks, 23, 1, 20)), 20)


if __name__ == "__main__":
    unittest.main()
