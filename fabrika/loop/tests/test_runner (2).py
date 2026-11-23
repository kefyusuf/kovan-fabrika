"""KOVAN dongu kosucusu testleri.

Calistirmak icin:  python -m unittest discover -s tests -t .   (fabrika/loop icinde)
Bagimlilik: yalnizca standart kutuphane + PyYAML (spec yukleme testi icin).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Gomulu Python bazi ortamlarda cwd'yi sys.path'e eklemez (safepath/isolated).
# Test dosyasi kendi ust dizinini acikca ekler; `python tests/test_runner.py`
# ve `python -m unittest` ayni sekilde calisir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runner import (
    Candidate,
    ChangeClass,
    GateSpec,
    Ledger,
    Loop,
    ScriptedAdapter,
    Spec,
    SpecError,
    Task,
)


def cand(task_id: str, tokens: int = 1_000, diff: str = "src/app.py", **signals):
    base = {
        "lint": True,
        "types": True,
        "tests": True,
        "provenance": True,
        "review": True,
        "eval": 0.95,
        "cost_usd": 2.0,
    }
    base.update(signals)
    return Candidate(task_id=task_id, tokens=tokens, diff=diff, signals=base)


class LoopTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.spec = Spec.defaults()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_loop(self, tasks, script, spec=None, rounds=10, resume=False, workdir=None):
        loop = Loop(
            spec=spec or self.spec,
            adapter=ScriptedAdapter(script),
            workdir=workdir or self.dir,
            backlog=tasks,
        )
        return loop, loop.run(max_rounds=rounds, resume=resume)


class AcceptanceTests(LoopTestCase):
    def test_accept_when_all_gates_pass(self):
        tasks = [Task("T1", "kucuk duzeltme")]
        loop, report = self.run_loop(tasks, {"T1": [cand("T1")]})

        self.assertEqual(report.accepted, ["T1"])
        self.assertEqual(report.decisions[0].kind, "accepted")
        self.assertEqual(loop.spec.gates[0].name, "policy")

    def test_nonblocking_gate_warns_but_does_not_reject(self):
        tasks = [Task("T1", "pahali ama kabul")]
        _, report = self.run_loop(tasks, {"T1": [cand("T1", cost_usd=99.0)]})

        self.assertEqual(report.accepted, ["T1"])
        cost = [g for g in report.decisions[0].gates if g.gate == "cost"][0]
        self.assertFalse(cost.ok)
        self.assertFalse(cost.blocking)


class GateTests(LoopTestCase):
    def test_fail_fast_stops_at_first_blocking_gate(self):
        tasks = [Task("T1", "testi kirik")]
        _, report = self.run_loop(
            tasks, {"T1": [cand("T1", tests=False, eval=None)]}
        )

        last = report.decisions[-1]
        gates = [g.gate for g in last.gates]
        self.assertEqual(gates, ["policy", "lint", "types", "tests"])
        self.assertEqual(last.kind, "rejected")

    def test_missing_eval_signal_is_not_a_pass(self):
        tasks = [Task("T1", "olculmedi")]
        _, report = self.run_loop(tasks, {"T1": [cand("T1", eval=None)]})

        eval_gate = [g for g in report.decisions[-1].gates if g.gate == "eval"][0]
        self.assertFalse(eval_gate.ok)
        self.assertEqual(eval_gate.detail, "sinyal yok")

    def test_missing_boolean_signal_is_not_a_pass(self):
        broken = cand("T1")
        del broken.signals["lint"]
        tasks = [Task("T1", "lint sinyali yok")]

        _, report = self.run_loop(tasks, {"T1": [broken]})

        last = report.decisions[-1].gates[-1]
        self.assertEqual(last.gate, "lint")
        self.assertFalse(last.ok)
        self.assertEqual(last.detail, "sinyal yok")
        self.assertEqual(report.decisions[-1].kind, "rejected")

    def test_bool_signal_with_signal_field_is_boolean(self):
        """Canlı profil regresyonu: signal alanlı boolean False, sayısal
        0.0 sayılıp kapıyı GEÇİYORDU; artık boolean sayılır."""
        spec = Spec.defaults()
        spec.gates = [GateSpec("tests", True, signal="tests", order=10)]
        loop = Loop(spec=spec, adapter=ScriptedAdapter({}), workdir=self.dir)

        sonuc = loop.evaluate(Candidate("T", 0, diff="", signals={"tests": False}))
        self.assertFalse(sonuc[0].ok)
        self.assertEqual(sonuc[0].detail, "başarısız")

        sonuc2 = loop.evaluate(Candidate("T", 0, diff="", signals={"tests": True}))
        self.assertTrue(sonuc2[0].ok)

    def test_eval_threshold_enforced(self):
        tasks = [Task("T1", "eval dusuk")]
        _, report = self.run_loop(tasks, {"T1": [cand("T1", eval=0.72)]})

        self.assertEqual(report.decisions[-1].kind, "rejected")
        self.assertIn("eval=0.72", report.decisions[-1].reason)

    def test_revision_then_accept(self):
        tasks = [Task("T1", "iki deneme")]
        script = {"T1": [cand("T1", tests=False), cand("T1", tests=True)]}
        loop, report = self.run_loop(tasks, script)

        kinds = [d.kind for d in report.decisions]
        self.assertEqual(kinds, ["revise", "accepted"])
        self.assertEqual(report.revisions, 1)
        self.assertEqual(loop.adapter.calls, [("T1", 1), ("T1", 2)])


class HumanGateTests(LoopTestCase):
    def test_policy_violation_blocks_immediately(self):
        tasks = [Task("T1", "sirri oku", change_class=ChangeClass.C2)]
        _, report = self.run_loop(
            tasks, {"T1": [cand("T1", diff=".secrets/anahtar.pem")]}
        )

        self.assertEqual(report.decisions[0].kind, "blocked")
        self.assertEqual(report.blocked, ["T1"])
        self.assertEqual(report.revisions, 0)

    def test_constitution_file_is_protected(self):
        # Gercek sozlesme dosyasi kullanilir: koruma, varsayilan Spec'te degil
        # goal.yaml'in forbidden_paths listesinde tanimli.
        real = Spec.load(Path(__file__).resolve().parent.parent)
        tasks = [Task("T1", "anayasayı düzenle", change_class=ChangeClass.C2)]
        _, report = self.run_loop(
            tasks, {"T1": [cand("T1", diff="loop/constitution.md")]}, spec=real
        )

        self.assertEqual(report.decisions[0].kind, "blocked")
        self.assertIn("politika ihlali", report.decisions[0].reason)

    def test_c3_change_requires_human(self):
        tasks = [Task("T1", "anayasayi degistir", change_class=ChangeClass.C3)]
        loop, report = self.run_loop(tasks, {"T1": [cand("T1")]})

        self.assertEqual(report.decisions[0].kind, "blocked")
        self.assertIn("insan onayı", report.decisions[0].reason)
        # tek denemede durur, israr etmez
        self.assertEqual(len(loop.adapter.calls), 1)


class StopRuleTests(LoopTestCase):
    def test_budget_exhaustion_stops(self):
        spec = Spec.defaults()
        spec.budget_tokens = 2_500
        tasks = [
            Task("T1", "a", estimate_tokens=1_000),
            Task("T2", "b", estimate_tokens=1_000),
            Task("T3", "c", estimate_tokens=1_000),
        ]
        script = {t: [cand(t, tokens=1_000)] for t in ("T1", "T2", "T3")}

        _, report = self.run_loop(tasks, script, spec=spec)

        self.assertEqual(report.accepted, ["T1", "T2"])
        self.assertEqual(report.stopped, "butce_bitti")

    def test_budget_overflow_blocks_before_verification(self):
        spec = Spec.defaults()
        spec.budget_tokens = 2_500
        tasks = [Task("T1", "tahmini aşan", estimate_tokens=1_000)]

        _, report = self.run_loop(
            tasks, {"T1": [cand("T1", tokens=5_000)]}, spec=spec
        )

        self.assertEqual(report.accepted, [])
        self.assertEqual(report.decisions[0].kind, "blocked")
        self.assertIn("bütçe aşıldı", report.decisions[0].reason)
        self.assertEqual(report.stopped, "butce_bitti")

    def test_circuit_breaker_after_three_failures(self):
        tasks = [Task(f"T{i}", "bozuk") for i in range(1, 6)]
        script = {t.id: [cand(t.id, tests=False)] for t in tasks}

        _, report = self.run_loop(tasks, script)

        self.assertEqual(report.stopped, "devre_kesici")
        rejected = [d for d in report.decisions if d.kind == "rejected"]
        self.assertEqual(len(rejected), 3)
        self.assertEqual(report.accepted, [])

    def test_plateau_detection(self):
        spec = Spec.defaults()
        spec.consecutive_failures = 99
        spec.plateau_rounds = 2
        tasks = [Task(f"T{i}", "bos is") for i in range(1, 5)]
        script = {t.id: [cand(t.id, review=False)] for t in tasks}

        _, report = self.run_loop(tasks, script, spec=spec)

        self.assertEqual(report.stopped, "plato")
        rejected = [d for d in report.decisions if d.kind == "rejected"]
        self.assertEqual(len(rejected), 2)

    def test_human_stop_file(self):
        (self.dir / "STOP").write_text("dur", encoding="utf-8")
        tasks = [Task("T1", "hic baslamamali")]
        _, report = self.run_loop(tasks, {"T1": [cand("T1")]})

        self.assertEqual(report.stopped, "insan_durdurdu")
        self.assertEqual(report.accepted, [])


class LearningTests(LoopTestCase):
    def test_rejection_writes_lesson(self):
        tasks = [Task("T1", "kotu")]
        _, _report = self.run_loop(tasks, {"T1": [cand("T1", types=False)]})

        lines = (self.dir / "lessons.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["gate"], "types")

    def test_repeated_failure_emits_skill_candidate(self):
        tasks = [Task("T1", "a"), Task("T2", "b")]
        script = {
            "T1": [cand("T1", review=False)],
            "T2": [cand("T2", review=False)],
        }

        _, _report = self.run_loop(tasks, script)

        skills = (self.dir / "skills.proposed.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(len(skills), 1)
        record = json.loads(skills[0])
        self.assertEqual(record["kind"], "skill_candidate")
        self.assertEqual(record["gate"], "review")
        self.assertEqual(record["status"], "proposed")


class LedgerTests(LoopTestCase):
    def test_ledger_chain_verifies(self):
        tasks = [Task("T1", "a"), Task("T2", "b")]
        script = {"T1": [cand("T1")], "T2": [cand("T2", tests=False)]}
        self.run_loop(tasks, script)

        ledger = Ledger(self.dir / "ledger.jsonl")
        ok, count, reason = ledger.verify()
        self.assertTrue(ok, reason)
        self.assertEqual(count, 3)  # 2 karar + 1 revizyon
        self.assertEqual(ledger.records()[0]["prev"], Ledger.GENESIS)

    def test_tampering_is_detected(self):
        self.run_loop([Task("T1", "a")], {"T1": [cand("T1")]})
        path = self.dir / "ledger.jsonl"
        records = [json.loads(line) for line in path.read_text("utf-8").splitlines()]
        records[0]["payload"]["kind"] = "rejected"
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records)
            + "\n",
            encoding="utf-8",
        )

        ok, _count, reason = Ledger(path).verify()
        self.assertFalse(ok)
        self.assertIn("tahrif", reason)


class ResumeTests(LoopTestCase):
    def test_resume_skips_completed_tasks(self):
        tasks = [Task("T1", "a"), Task("T2", "b")]
        self.run_loop(tasks, {"T1": [cand("T1")], "T2": [cand("T2")]}, rounds=1)

        loop, report = self.run_loop(
            tasks,
            {"T2": [cand("T2")]},
            workdir=self.dir,
            resume=True,
        )

        self.assertEqual(report.accepted, ["T1", "T2"])
        self.assertEqual(loop.adapter.calls, [("T2", 1)])


class SpecTests(unittest.TestCase):
    def test_spec_without_goal_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SpecError):
                Spec.load(tmp)

    def test_repository_specs_load(self):
        spec_dir = Path(__file__).resolve().parent.parent
        spec = Spec.load(spec_dir)

        self.assertEqual(spec.goal_id, "kovan-gece-vardiyasi-v1")
        names = [g.name for g in spec.gates]
        self.assertEqual(names[0], "policy")
        self.assertIn("eval", names)
        self.assertGreater(spec.budget_tokens, 0)
        self.assertIn("anayasa/", spec.forbidden_paths)


if __name__ == "__main__":
    unittest.main(verbosity=2)
