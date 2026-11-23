"""KOVAN — Capacity valve.

The research's main finding: the bottleneck is not code production but
acceptance (review) capacity. This module answers the question "how many
tasks can we take" with measurement, not gut feeling.

Three calculations:
1. Review effort   : LOC / 500 + 0.25 hours of context per PR
2. Queue delay     : M/M/1  ->  (rho / (1-rho)) / mu
3. WIP limit       : Little's law  ->  target cycle time x daily arrivals

Calibration (research):
- 400 LOC ~ 0.8-1.0 review hours (Cisco/SmartBear)
- at mu = 10 PR/day: rho = 0.625 -> ~4 h (Google <4 h median)
- rho = 0.80 -> 9.6 h; rho = 0.89 -> ~19 h (Faros +441%)
- rho = 0.95 -> ~46 h: the system is saturated, the queue stretches to two days

Note: in M/M/1 the queue *length* (rho/(1-rho)) must not be confused with
the queue *time* (rho/(mu-lam)). This module reports time in hours.

Usage:
    python capacity.py --reviewers 2 --hours 3
    python capacity.py --lam 9 --mu 10
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field

LOC_PER_HOUR = 500.0
CONTEXT_HOURS_PER_PR = 0.25
DEFAULT_CONFLICT_RATE = 0.198  # same agent, concurrent PR pairs (arXiv 2607.04697)


@dataclass(frozen=True)
class WorkItem:
    id: str
    loc: int
    priority: int = 2  # 1 = highest
    dependencies: tuple[str, ...] = ()

    def sort_key(self) -> tuple[int, int, str]:
        return (self.priority, self.loc, self.id)


@dataclass
class CapacityDecision:
    accepted: list[WorkItem] = field(default_factory=list)
    deferred: list[WorkItem] = field(default_factory=list)
    used_hours: float = 0.0
    capacity_hours: float = 0.0

    @property
    def occupancy(self) -> float:
        return round(self.used_hours / self.capacity_hours, 4) if self.capacity_hours else 0.0

    def summary(self) -> dict:
        return {
            "kabul": [g.id for g in self.accepted],
            "ertelenen": [g.id for g in self.deferred],
            "kullanilan_saat": round(self.used_hours, 2),
            "kapasite_saat": round(self.capacity_hours, 2),
            "doluluk": self.occupancy,
        }


def review_hours(loc: int, context: float = CONTEXT_HOURS_PER_PR) -> float:
    """Hours needed to review one PR."""
    if loc < 0:
        raise ValueError("loc negatif olamaz")
    return loc / LOC_PER_HOUR + context


def review_capacity_hours(reviewers: int, focused_hours: float) -> float:
    """Daily/weekly focused review capacity."""
    if reviewers < 0 or focused_hours < 0:
        raise ValueError("negatif girdi")
    return reviewers * focused_hours


def mm1_delay(lam: float, mu: float) -> float:
    """M/M/1 average queue wait (hours). Infinite when rho >= 1."""
    if mu <= 0:
        raise ValueError("mu pozitif olmalı")
    rho = lam / mu
    if rho >= 1:
        return math.inf
    return (rho / (1 - rho)) * (1 / mu) * 24


def wip_limit(target_days: float, daily_arrivals: float) -> int:
    """Little's law: L = lambda * W."""
    if target_days < 0 or daily_arrivals < 0:
        raise ValueError("negatif girdi")
    return max(0, math.floor(target_days * daily_arrivals))


def conflicting_pairs(n: int, p: float = DEFAULT_CONFLICT_RATE) -> float:
    """Expected number of conflicting pairs for n concurrent PRs."""
    if n < 2:
        return 0.0
    return n * (n - 1) / 2 * p


def accept(
    work_items: list[WorkItem], capacity: float, wip: int | None = None
) -> CapacityDecision:
    """Accept work in priority order without exceeding capacity."""
    if capacity < 0:
        raise ValueError("kapasite negatif olamaz")

    remaining = capacity
    decision = CapacityDecision(capacity_hours=capacity)
    candidates = sorted(work_items, key=lambda g: g.sort_key())
    accepted_ids: set[str] = set()

    for item in candidates:
        if wip is not None and len(decision.accepted) >= wip:
            decision.deferred.append(item)
            continue
        if any(dep not in accepted_ids for dep in item.dependencies):
            decision.deferred.append(item)
            continue
        needed = review_hours(item.loc)
        if needed <= remaining + 1e-9:
            decision.accepted.append(item)
            accepted_ids.add(item.id)
            remaining -= needed
            decision.used_hours += needed
        else:
            decision.deferred.append(item)

    return decision


def capacity_report(
    *,
    reviewers: int,
    focused_hours: float,
    lam: float,
    mu: float,
    target_days: float = 1.0,
) -> dict:
    capacity = review_capacity_hours(reviewers, focused_hours)
    rho = lam / mu if mu else math.inf
    return {
        "kapasite_saat": capacity,
        "gunluk_kapasite_pr": round(capacity / (400 / LOC_PER_HOUR + CONTEXT_HOURS_PER_PR), 1),
        "rho": round(rho, 3) if math.isfinite(rho) else "sinirsiz",
        "kuyruk_gecikmesi_saat": (
            round(mm1_delay(lam, mu), 2) if math.isfinite(mm1_delay(lam, mu)) else "sinirsiz"
        ),
        "wip_limiti": wip_limit(target_days, lam),
        "tavsiye": _recommendation(rho),
    }


def _recommendation(rho: float) -> str:
    if rho >= 1:
        return "DUR: kapasite talebi karşılamıyor; yeni iş alma."
    if rho >= 0.85:
        return "KIS: kuyruk patlamak üzere; eşzamanlılığı düşür."
    if rho >= 0.6:
        return "DENGE: sağlıklı bant; WIP limitini koru."
    return "BOŞLUK: kapasite var; iş alımını artırabilirsin."


def _sample_backlog() -> list[WorkItem]:
    return [
        WorkItem("K-101", 40, 1),
        WorkItem("K-102", 320, 1),
        WorkItem("K-103", 120, 2),
        WorkItem("K-104", 600, 2),
        WorkItem("K-105", 200, 3),
        WorkItem("K-106", 90, 3),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN kapasite valfi")
    parser.add_argument("--reviewers", type=int, default=1)
    parser.add_argument("--hours", type=float, default=3.0)
    parser.add_argument("--lam", type=float, default=8.0, help="günlük PR gelişi")
    parser.add_argument("--mu", type=float, default=10.0, help="günlük inceleme kapasitesi (PR)")
    parser.add_argument("--target-days", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = capacity_report(
        reviewers=args.reviewers,
        focused_hours=args.hours,
        lam=args.lam,
        mu=args.mu,
        target_days=args.target_days,
    )
    decision = accept(_sample_backlog(), review_capacity_hours(args.reviewers, args.hours))
    report["ornek_kabul"] = decision.summary()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Kapasite        : {report['kapasite_saat']:.1f} saat/gün")
        print(f"Günlük PR tavanı: {report['gunluk_kapasite_pr']}")
        print(f"Doluluk (rho)   : {report['rho']}")
        print(f"Kuyruk bekleme  : {report['kuyruk_gecikmesi_saat']} saat")
        print(f"WIP limiti      : {report['wip_limiti']}")
        print(f"Tavsiye         : {report['tavsiye']}")
        print(f"Örnek kabul     : {report['ornek_kabul']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
