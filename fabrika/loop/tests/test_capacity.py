"""Capacity valve tests."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from capacity import (  # noqa: E402
    WorkItem,
    conflicting_pairs,
    review_hours,
    accept,
    review_capacity_hours,
    mm1_delay,
    wip_limit,
)


class ReviewHoursTest(unittest.TestCase):
    def test_400_loc_is_one_hour(self):
        # 400/500 = 0.8 + 0.25 context = 1.05
        self.assertAlmostEqual(review_hours(400), 1.05, places=3)

    def test_zero_loc_context_only(self):
        self.assertAlmostEqual(review_hours(0), 0.25, places=3)

    def test_negative_loc_rejected(self):
        with self.assertRaises(ValueError):
            review_hours(-1)


class ReviewCapacityTest(unittest.TestCase):
    def test_two_reviewers_three_hours(self):
        self.assertEqual(review_capacity_hours(2, 3), 6)

    def test_negative_input(self):
        with self.assertRaises(ValueError):
            review_capacity_hours(-1, 3)


class QueueDelayTest(unittest.TestCase):
    def test_lambda_8_mu_10(self):
        # Wq = rho / (mu - lam) days = 0.8/2 = 0.4 days = 9.6 hours
        self.assertAlmostEqual(mm1_delay(8, 10), 9.6, places=2)

    def test_four_hour_threshold_rho_0625(self):
        self.assertAlmostEqual(mm1_delay(6.25, 10), 4.0, places=2)

    def test_19_hours_rho_0888(self):
        self.assertAlmostEqual(mm1_delay(8.878, 10), 19.0, places=1)

    def test_saturated_system_infinite(self):
        self.assertTrue(math.isinf(mm1_delay(10, 10)))
        self.assertTrue(math.isinf(mm1_delay(12, 10)))

    def test_zero_mu_raises(self):
        with self.assertRaises(ValueError):
            mm1_delay(1, 0)


class WipLimitTest(unittest.TestCase):
    def test_littles_law(self):
        self.assertEqual(wip_limit(1.0, 8), 8)
        self.assertEqual(wip_limit(0.5, 8), 4)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            wip_limit(-1, 8)


class ConflictTest(unittest.TestCase):
    def test_eight_prs(self):
        self.assertAlmostEqual(conflicting_pairs(8), 28 * 0.198, places=3)

    def test_single_pr(self):
        self.assertEqual(conflicting_pairs(1), 0.0)


class AcceptTest(unittest.TestCase):
    def test_priority_and_capacity(self):
        work_items = [
            WorkItem("K-101", 40, 1),
            WorkItem("K-102", 320, 1),
            WorkItem("K-103", 120, 2),
            WorkItem("K-104", 600, 2),
            WorkItem("K-105", 200, 3),
            WorkItem("K-106", 90, 3),
        ]
        decision = accept(work_items, capacity=3.0)

        self.assertEqual([g.id for g in decision.accepted], ["K-101", "K-102", "K-103", "K-106", "K-105"])
        self.assertEqual([g.id for g in decision.deferred], ["K-104"])
        self.assertLessEqual(decision.used_hours, 3.0)

    def test_deferred_when_dependency_unmet(self):
        work_items = [
            WorkItem("A", 900, 1),  # 2.05 hours, does not fit
            WorkItem("B", 40, 2, dependencies=("A",)),
        ]
        decision = accept(work_items, capacity=1.0)

        self.assertEqual(decision.accepted, [])
        self.assertEqual([g.id for g in decision.deferred], ["A", "B"])

    def test_wip_limit_enforced(self):
        work_items = [WorkItem(f"T{i}", 10, 1) for i in range(5)]
        decision = accept(work_items, capacity=10.0, wip=2)

        self.assertEqual(len(decision.accepted), 2)
        self.assertEqual(len(decision.deferred), 3)

    def test_zero_capacity(self):
        decision = accept([WorkItem("T1", 10, 1)], capacity=0.0)

        self.assertEqual(decision.accepted, [])
        self.assertEqual(decision.occupancy, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
