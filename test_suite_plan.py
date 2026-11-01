import unittest

import run
import suite_plan


class Plan(unittest.TestCase):
    def test_a_sample_is_repeatable_and_covers_each_tier(self):
        tasks = run.select_tasks(run.CODING_TIERS, "")
        picked = suite_plan.sample(tasks, 40, 1)
        self.assertEqual(picked, suite_plan.sample(tasks, 40, 1))
        self.assertLessEqual(abs(len(picked) - 40), len(run.CODING_TIERS))
        self.assertEqual({run.tier_of(t) for t in picked}, set(run.CODING_TIERS))

    def test_every_task_lands_in_one_job_and_jobs_fit_the_limit(self):
        tasks = [f"t{i}" for i in range(289)]
        groups = suite_plan.split(tasks, 23, 1, 20)
        self.assertEqual(sum(groups, []), tasks)
        self.assertLessEqual(max(map(len, groups)) * 23 * suite_plan.MINUTES_PER_RUN, suite_plan.JOB_MINUTES)

    def test_a_small_run_spreads_over_the_jobs_it_asked_for(self):
        self.assertEqual(len(suite_plan.split([f"t{i}" for i in range(40)], 23, 1, 20)), 20)


if __name__ == "__main__":
    unittest.main()
