"""KOVAN loop runner — reference implementation.

Design principle: a "self-improving system" is not magic; it is a state
machine. Each turn proceeds in this order:

    OBSERVE -> SELECT -> PROPOSE -> VERIFY (gates) -> DECIDE -> RECORD -> LEARN

This file makes the factory's claimed behaviors *measurable*:
- gate order and fail-fast
- budget accounting (tokens)
- circuit breaker (consecutive failures)
- plateau detection (no progress)
- change classes (C0-C3) and human approval
- hash-chained ledger (tamper detection)
- recurring failure -> skill candidate extraction

The runner never touches the network and never calls an LLM. The model call
lives behind the `Adapter` interface; tests run deterministically with
`ScriptedAdapter`. This is the code counterpart of the "verify the skeleton
first, connect the model later" decision (ADR-F02).
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence


# --------------------------------------------------------------------------
# Change classes (ADR-F08)
# --------------------------------------------------------------------------


class ChangeClass(str, Enum):
    """How much "structure" a change carries.

    C0: spelling/comments/configuration - gates suffice.
    C1: skills, prompts, docs - eval + review.
    C2: product code - all gates.
    C3: constitution, policy, model, roster - impossible without human approval.
    """

    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


HUMAN_REQUIRED = {ChangeClass.C3}


# --------------------------------------------------------------------------
# Data models
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    change_class: ChangeClass = ChangeClass.C2
    priority: int = 2  # 1 = highest
    estimate_tokens: int = 10_000
    touches: tuple[str, ...] = ()

    def sort_key(self) -> tuple[int, int, str]:
        return (self.priority, self.estimate_tokens, self.id)


@dataclass
class Candidate:
    """The candidate change produced by the Adapter."""

    task_id: str
    tokens: int
    diff: str = ""
    signals: dict[str, Any] = field(default_factory=dict)
    attempt: int = 1


@dataclass(frozen=True)
class GateResult:
    gate: str
    ok: bool
    blocking: bool
    detail: str = ""


@dataclass
class Decision:
    kind: str  # accepted | revise | rejected | blocked
    task_id: str
    reason: str
    gates: list[GateResult] = field(default_factory=list)


@dataclass
class RunReport:
    decisions: list[Decision] = field(default_factory=list)
    stopped: str = ""
    tokens_spent: int = 0
    accepted: list[str] = field(default_factory=list)
    revisions: int = 0
    blocked: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "accepted": len(self.accepted),
            "rejected": sum(1 for d in self.decisions if d.kind == "rejected"),
            "blocked": len(self.blocked),
            "revised": self.revisions,
            "tokens_spent": self.tokens_spent,
            "stopped": self.stopped,
            "accept_rate": (
                round(len(self.accepted) / len(self.decisions), 3)
                if self.decisions
                else 0.0
            ),
        }


# --------------------------------------------------------------------------
# Contract (spec) loading
# --------------------------------------------------------------------------


@dataclass
class GateSpec:
    name: str
    blocking: bool = True
    threshold: float | None = None
    signal: str | None = None
    order: int = 100


class SpecError(RuntimeError):
    """The contract could not be loaded: the loop must not start."""


@dataclass
class Spec:
    goal_id: str = "kovan-v1"
    forbidden_paths: tuple[str, ...] = ("anayasa/", ".secrets/", "politika/")
    human_keywords: tuple[str, ...] = ()
    max_attempts: int = 2
    budget_tokens: int = 2_000_000
    consecutive_failures: int = 3
    plateau_rounds: int = 5
    max_usd_per_pr: float = 6.0
    gates: list[GateSpec] = field(default_factory=list)

    @classmethod
    def defaults(cls) -> "Spec":
        return cls(
            gates=[
                GateSpec("policy", True, order=10),
                GateSpec("lint", True, order=20),
                GateSpec("types", True, order=30),
                GateSpec("tests", True, order=40),
                GateSpec("provenance", True, order=45),
                GateSpec("review", True, order=50),
                GateSpec("eval", True, threshold=0.90, signal="eval", order=60),
                GateSpec("cost", False, threshold=6.0, signal="cost_usd", order=70),
            ]
        )

    @classmethod
    def load(cls, directory: str | Path, require_goal: bool = True) -> "Spec":
        """Loads from the goal.yaml + gates.yaml files.

        With `require_goal=True`, a missing goal contract makes loading fail:
        a loop without a goal performs work it cannot measure (PRD FR-01).
        """
        directory = Path(directory)
        spec = cls.defaults()

        goal_file = directory / "goal.yaml"
        if not goal_file.exists():
            if require_goal:
                raise SpecError(
                    f"{goal_file} yok: hedef sozlesmesi olmadan dongu baslatilamaz"
                )
        else:
            data = _read_yaml(goal_file)
            constraints = data.get("constraints", {}) or {}
            budget = data.get("budget", {}) or {}
            stop = data.get("stop_rules", {}) or {}
            spec.goal_id = (data.get("goal", {}) or {}).get("id", spec.goal_id)
            spec.forbidden_paths = tuple(
                constraints.get("forbidden_paths", spec.forbidden_paths)
            )
            spec.human_keywords = tuple(constraints.get("require_human_for", ()))
            spec.max_attempts = int(constraints.get("max_attempts", spec.max_attempts))
            spec.budget_tokens = int(budget.get("tokens_per_shift", spec.budget_tokens))
            spec.consecutive_failures = int(
                stop.get("consecutive_failures", spec.consecutive_failures)
            )
            spec.plateau_rounds = int(stop.get("plateau_rounds", spec.plateau_rounds))
            spec.max_usd_per_pr = float(
                budget.get("max_usd_per_merged_pr", spec.max_usd_per_pr)
            )

        gates_file = directory / "gates.yaml"
        if gates_file.exists():
            data = _read_yaml(gates_file)
            loaded: list[GateSpec] = []
            for i, row in enumerate(data.get("gates", []), start=1):
                loaded.append(
                    GateSpec(
                        name=str(row["name"]),
                        blocking=bool(row.get("blocking", True)),
                        threshold=(
                            float(row["threshold"]) if "threshold" in row else None
                        ),
                        signal=row.get("signal"),
                        order=int(row.get("order", i * 10)),
                    )
                )
            if loaded:
                spec.gates = sorted(loaded, key=lambda g: g.order)
        if not spec.goal_id.strip():
            raise SpecError("goal.id bos: hedef tanimsiz")
        return spec


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - not an environment guarantee
        raise RuntimeError(
            f"{path.name} okumak icin PyYAML gerekli: python -m pip install pyyaml"
        )
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# --------------------------------------------------------------------------
# Ledger: hash chain
# --------------------------------------------------------------------------


class Ledger:
    """Links every decision to the previous record's hash.

    Airlock uses the same pattern for tool calls; here it is used for the
    loop's own decisions. The goal is the same: nobody can later claim "it
    actually did not happen that way".
    """

    GENESIS = "0" * 64

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._tip = self._last_hash()

    # -- public ---------------------------------------------------------
    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        seq = self._next_seq()
        record = {
            "seq": seq,
            "ts": round(time.time(), 3),
            "prev": self._tip,
            "payload": payload,
        }
        record["hash"] = _hash_record(record)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        self._tip = record["hash"]
        return record

    def records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def verify(self) -> tuple[bool, int, str]:
        """(passed, record_count, first_break_reason)"""
        prev = self.GENESIS
        records = self.records()
        for record in records:
            body = {k: v for k, v in record.items() if k != "hash"}
            if body["prev"] != prev:
                return False, len(records), f"seq {record['seq']}: prev baglantisi kopuk"
            if _hash_record(body) != record["hash"]:
                return False, len(records), f"seq {record['seq']}: kayit tahrif edilmis"
            prev = record["hash"]
        return True, len(records), ""

    # -- private --------------------------------------------------------
    def _next_seq(self) -> int:
        return len(self.records()) + 1

    def _last_hash(self) -> str:
        records = self.records()
        return records[-1]["hash"] if records else self.GENESIS


def _hash_record(record: dict[str, Any]) -> str:
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# --------------------------------------------------------------------------
# Adapter: where the model plugs in
# --------------------------------------------------------------------------


class Adapter(Protocol):
    def propose(self, task: Task, attempt: int) -> Candidate: ...


class ScriptedAdapter:
    """For tests and dry runs: answers each task in scripted order."""

    def __init__(self, script: dict[str, Sequence[Candidate]]):
        self._script = {k: list(v) for k, v in script.items()}
        self.calls: list[tuple[str, int]] = []

    def propose(self, task: Task, attempt: int) -> Candidate:
        self.calls.append((task.id, attempt))
        queue = self._script.get(task.id, [])
        if not queue:
            return Candidate(task_id=task.id, tokens=task.estimate_tokens)
        candidate = queue[min(attempt - 1, len(queue) - 1)]
        return candidate


# --------------------------------------------------------------------------
# Loop
# --------------------------------------------------------------------------


class Loop:
    def __init__(
        self,
        spec: Spec,
        adapter: Adapter,
        workdir: str | Path,
        backlog: Iterable[Task] = (),
    ):
        self.spec = spec
        self.adapter = adapter
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)

        self.ledger = Ledger(self.workdir / "ledger.jsonl")
        self.lessons_path = self.workdir / "lessons.jsonl"
        self.skills_path = self.workdir / "skills.proposed.jsonl"

        self.backlog: list[Task] = sorted(backlog, key=lambda t: t.sort_key())
        self.pending: list[Task] = list(self.backlog)

        self.budget_left = spec.budget_tokens
        self.consecutive_failures = 0
        self.rounds_since_progress = 0
        self.report = RunReport()
        self._lesson_counts: dict[str, int] = self._load_lesson_counts()

    # -- public ---------------------------------------------------------
    def run(self, max_rounds: int = 50, resume: bool = False) -> RunReport:
        if resume:
            self._restore()

        for _ in range(max_rounds):
            stop = self._check_stop()
            if stop:
                self.report.stopped = stop
                break
            task = self._select()
            if task is None:
                self.report.stopped = "is_kalmadi"
                break
            # Starting a task requires budget at least equal to its estimate.
            # Starting over budget makes the ceiling "approximate"; a ceiling
            # cannot be approximate.
            if self.budget_left < task.estimate_tokens:
                self.report.stopped = "butce_bitti"
                break
            self._run_task(task)
        else:
            self.report.stopped = "tur_siniri"

        self._persist()
        return self.report

    # -- steps ----------------------------------------------------------
    def _check_stop(self) -> str:
        if (self.workdir / "STOP").exists():
            return "insan_durdurdu"
        if self.budget_left <= 0:
            return "butce_bitti"
        if self.consecutive_failures >= self.spec.consecutive_failures:
            return "devre_kesici"
        if self.rounds_since_progress >= self.spec.plateau_rounds:
            return "plato"
        return ""

    def _select(self) -> Task | None:
        return self.pending[0] if self.pending else None

    def _run_task(self, task: Task) -> None:
        attempt = 1
        while attempt <= self.spec.max_attempts:
            candidate = self.adapter.propose(task, attempt)
            self._spend(candidate.tokens)

            if self.budget_left < 0:
                # The spending already happened; no budget is left for
                # verification. Accepting the task would make the ceiling
                # "approximate"; a ceiling cannot be approximate.
                self._decide(
                    Decision("blocked", task.id, "bütçe aşıldı: doğrulama yapılamaz", [])
                )
                self.report.blocked.append(task.id)
                self.pending.pop(0)
                self._note_outcome(progress=False, failure=True)
                return

            gates = self.evaluate(candidate)
            blocking_failures = [g for g in gates if not g.ok and g.blocking]

            # C3 and policy violations: a human gate; retrying is pointless.
            human_gate = self._human_gate(task, gates)
            if human_gate is not None:
                self._decide(Decision("blocked", task.id, human_gate, gates))
                self.report.blocked.append(task.id)
                self.pending.pop(0)
                self._note_outcome(progress=False, failure=True)
                return

            if not blocking_failures:
                self._decide(Decision("accepted", task.id, "tüm kapılar geçti", gates))
                self.report.accepted.append(task.id)
                self.pending.pop(0)
                self._note_outcome(progress=True, failure=False)
                return

            first = blocking_failures[0]
            reason = f"{first.gate}: {first.detail or 'başarısız'}"
            if attempt < self.spec.max_attempts:
                self._decide(Decision("revise", task.id, reason, gates))
                self.report.revisions += 1
                attempt += 1
                continue

            self._decide(Decision("rejected", task.id, reason, gates))
            self._learn(task, first)
            self.pending.pop(0)
            self._note_outcome(progress=False, failure=True)
            return

    # -- gates ----------------------------------------------------------
    def evaluate(self, candidate: Candidate) -> list[GateResult]:
        results: list[GateResult] = []
        for gate in self.spec.gates:
            result = self._run_gate(gate, candidate)
            results.append(result)
            if not result.ok and result.blocking:
                break  # fail-fast: stop at the first blocking gate
        return results

    def _run_gate(self, gate: GateSpec, candidate: Candidate) -> GateResult:
        if gate.name == "policy":
            hit = [
                path
                for path in self.spec.forbidden_paths
                if path and path in candidate.diff
            ]
            if hit:
                return GateResult("policy", False, True, f"yasak yol: {hit[0]}")
            return GateResult("policy", True, True, "temiz")

        if gate.signal is None:
            value = candidate.signals.get(gate.name)
            if value is None:
                # No signal, no pass: something unmeasured cannot count as "passed".
                return GateResult(gate.name, False, gate.blocking, "sinyal yok")
            ok = bool(value)
            return GateResult(
                gate.name, ok, gate.blocking, "geçti" if ok else "başarısız"
            )

        value = candidate.signals.get(gate.signal)
        if value is None:
            # No signal, no pass: "unmeasured" != "passed".
            return GateResult(gate.name, False, gate.blocking, "sinyal yok")
        if isinstance(value, bool):
            # A boolean signal is never coerced to a number: the False = 0.0 trap.
            ok = value
            return GateResult(
                gate.name, ok, gate.blocking, "geçti" if ok else "başarısız"
            )
        try:
            sayi = float(value)
        except (TypeError, ValueError):
            return GateResult(gate.name, False, gate.blocking, "sinyal sayı değil")
        if gate.name == "cost":
            esik = gate.threshold if gate.threshold is not None else math.inf
            ok = sayi <= esik
        else:
            esik = gate.threshold if gate.threshold is not None else 0.0
            ok = sayi >= esik
        return GateResult(gate.name, ok, gate.blocking, f"{gate.signal}={value}")

    def _human_gate(self, task: Task, gates: list[GateResult]) -> str | None:
        if task.change_class in HUMAN_REQUIRED:
            return f"{task.change_class.value} değişiklik: insan onayı gerekli"
        touched = " ".join(task.touches)
        for keyword in self.spec.human_keywords:
            if keyword and keyword in touched:
                return f"insan onayı gerekli: {keyword}"
        policy = next((g for g in gates if g.gate == "policy" and not g.ok), None)
        if policy is not None:
            return f"politika ihlali: {policy.detail}"
        return None

    # -- record ---------------------------------------------------------
    def _decide(self, decision: Decision) -> None:
        self.report.decisions.append(decision)
        self.ledger.append(
            {
                "type": "decision",
                "task": decision.task_id,
                "kind": decision.kind,
                "reason": decision.reason,
                "gates": [
                    {"gate": g.gate, "ok": g.ok, "blocking": g.blocking, "detail": g.detail}
                    for g in decision.gates
                ],
            }
        )

    def _learn(self, task: Task, failure: GateResult) -> None:
        """Recurring failure -> skill candidate.

        Rule: the same gate + same reason seen twice is no longer a task
        problem but a *system* problem; it is recorded as a skill candidate
        (ADR-F04). It is recorded, never applied automatically.
        """
        fingerprint = hashlib.sha1(
            f"{failure.gate}|{failure.detail}".encode("utf-8")
        ).hexdigest()[:12]
        count = self._lesson_counts.get(fingerprint, 0) + 1
        self._lesson_counts[fingerprint] = count
        lesson = {
            "task": task.id,
            "gate": failure.gate,
            "detail": failure.detail,
            "fingerprint": fingerprint,
            "seen": count,
        }
        _append_jsonl(self.lessons_path, lesson)
        if count >= 2:
            _append_jsonl(
                self.skills_path,
                {
                    "kind": "skill_candidate",
                    "fingerprint": fingerprint,
                    "gate": failure.gate,
                    "symptom": failure.detail,
                    "status": "proposed",
                    "needs": "gece_vardiyasi_damitma",
                },
            )

    def _note_outcome(self, progress: bool, failure: bool) -> None:
        self.consecutive_failures = self.consecutive_failures + 1 if failure else 0
        self.rounds_since_progress = 0 if progress else self.rounds_since_progress + 1

    def _spend(self, tokens: int) -> None:
        self.budget_left -= max(0, int(tokens))
        self.report.tokens_spent += max(0, int(tokens))

    # -- state ----------------------------------------------------------
    def _persist(self) -> None:
        state = {
            "goal": self.spec.goal_id,
            "budget_left": self.budget_left,
            "tokens_spent": self.report.tokens_spent,
            "consecutive_failures": self.consecutive_failures,
            "rounds_since_progress": self.rounds_since_progress,
            "accepted": self.report.accepted,
            "blocked": self.report.blocked,
            "pending": [t.id for t in self.pending],
            "stopped": self.report.stopped,
        }
        (self.workdir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _restore(self) -> None:
        path = self.workdir / "state.json"
        if not path.exists():
            return
        state = json.loads(path.read_text(encoding="utf-8"))
        self.budget_left = int(state.get("budget_left", self.budget_left))
        self.report.tokens_spent = int(state.get("tokens_spent", 0))
        self.consecutive_failures = int(state.get("consecutive_failures", 0))
        self.rounds_since_progress = int(state.get("rounds_since_progress", 0))
        self.report.accepted = list(state.get("accepted", []))
        self.report.blocked = list(state.get("blocked", []))
        done = set(state.get("accepted", [])) | set(state.get("blocked", []))
        self.pending = [t for t in self.pending if t.id not in done]

    def _load_lesson_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        if not self.lessons_path.exists():
            return counts
        with self.lessons_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                fp = json.loads(line).get("fingerprint")
                if fp:
                    counts[fp] = counts.get(fp, 0) + 1
        return counts


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


__all__ = [
    "Adapter",
    "Candidate",
    "ChangeClass",
    "Decision",
    "GateResult",
    "GateSpec",
    "Ledger",
    "Loop",
    "RunReport",
    "ScriptedAdapter",
    "Spec",
    "Task",
]
