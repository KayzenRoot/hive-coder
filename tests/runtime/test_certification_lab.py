from __future__ import annotations

import hashlib
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path

from hive_runtime.certification_contracts import EvaluationSuite, ExecutionStackDescriptor, SuiteLineageAuthority
from hive_runtime.certification_lab import (
    BenchmarkAttestationAuthority, CertificationReportAuthority, ContaminationRadar,
    DurableAttestationJournal, DurableChronoSealClock, GradeDecision, LabActor,
    LabActorRole, LabIdentityAuthority, ProviderCertificationLab, StackSealAuthority,
    TrialEvidenceAuthority, TrialForge, TrialReceipt, TrialResponse, TrialSpec,
)
from hive_runtime.evaluation_runtime import CertificationAuthority, ShadowBenchFactory
from hive_runtime.expert_agents import AgentProfile, AgentProfileAuthority, build_default_expertise_capsules
from hive_runtime.expert_common import BenchmarkDimension
from hive_runtime.orchestration import AgentRole
from hive_runtime.repository_intelligence import RepoDNAIndexer, TruthWeave
from hive_runtime.semantic_twin import SemanticTwinBuilder


def sha(text: str) -> str: return hashlib.sha256(text.encode()).hexdigest()


class MemoryAnchor:
    def __init__(self): self.value = 0
    def floor(self) -> int: return self.value
    def advance(self, sequence: int) -> None:
        if sequence < self.value: raise ValueError("anchor rollback")
        self.value = sequence


class PassingRunner:
    def __init__(self): self.saw_oracle_attribute = False
    def run(self, material, *, provider_id: str, model_id: str):
        self.saw_oracle_attribute = hasattr(material, "oracle_digest")
        return TrialResponse(f"analysis:{provider_id}:{model_id}:{material.prompt_digest}")


class PassingGrader:
    def grade(self, packet):
        self.last_oracle = packet.oracle_digest
        return GradeDecision(True, rationale_digest=sha("independent-pass"))


class EmptyProofGrader:
    def grade(self, packet): return GradeDecision(True)


class DualEndpoint:
    def run(self, material, *, provider_id: str, model_id: str): return TrialResponse("x")
    def grade(self, packet): return GradeDecision(True, rationale_digest=sha("dual"))


class CertificationLabTests(unittest.TestCase):
    def setUp(self):
        self.profile_authority = AgentProfileAuthority(b"profile-authority-key-32-bytes-minimum!!")
        self.capsule = next(item for item in build_default_expertise_capsules(sha("doctrine")) if item.role is AgentRole.BACKEND)
        self.descriptor = ExecutionStackDescriptor(
            "opencode-go", "model-x", sha("model-revision"), sha("toolset-v1"),
            self.capsule.fingerprint(), sha("skillset-v1"), sha("runtime-v1"),
        )
        self.profile = self.profile_authority.seal(AgentProfile(
            "backend.lab", AgentRole.BACKEND, self.capsule.fingerprint(),
            frozenset({"tool_calling", "structured_output"}), 64000,
            "lineage.backend.lab", self.descriptor.fingerprint(),
        ))
        self.identity_authority = LabIdentityAuthority(b"lab-identity-authority-key-32-bytes!!")
        self.runner_actor = self.identity_authority.seal(LabActor(
            "runner.one", LabActorRole.RUNNER, "lineage.runner", sha("endpoint.runner"),
        ))
        self.grader_actor = self.identity_authority.seal(LabActor(
            "grader.one", LabActorRole.GRADER, "lineage.grader", sha("endpoint.grader"),
        ))
        self.suite_authority = SuiteLineageAuthority(b"suite-lineage-authority-key-32-bytes!")
        self.suite = self.suite_authority.seal(EvaluationSuite(
            "hive-shadow-repo", "1.0.0", "repo-reasoning", "independent.shadow.repo",
            "shadowbench", "1.0.0", sha("shadowbench-protocol-v1"),
        ))
        self.stack_authority = StackSealAuthority(
            b"stack-seal-authority-key-32-bytes!!!", self.profile_authority,
            self.identity_authority, self.suite_authority,
        )
        self.trial_authority = TrialEvidenceAuthority(b"trial-evidence-authority-key-32-bytes")
        self.benchmark_authority = BenchmarkAttestationAuthority(
            b"benchmark-authority-key-32-bytes!!!!", self.trial_authority, self.suite_authority,
        )
        self.report_authority = CertificationReportAuthority(b"report-authority-key-32-bytes!!!!!!!")

    def repository(self, root: Path):
        (root / "app.py").write_text('''\nfrom fastapi import FastAPI\napp = FastAPI()\n@app.get("/health")\ndef health():\n    return "ok"\n''', encoding="utf-8")
        indexed = RepoDNAIndexer().scan(root, repository_id="cert-lab")
        truth = TruthWeave(indexed).truth_map(); twin = SemanticTwinBuilder().build(indexed)
        return indexed, truth, twin

    def build_lab(self, root: Path, anchor: MemoryAnchor, truth, factory):
        journal = DurableAttestationJournal(root / "attestation.json", b"journal-key-32-bytes-minimum-secret!!", anchor)
        clock = DurableChronoSealClock(journal)
        certification_authority = CertificationAuthority(b"certification-authority-key-32-bytes!", clock, self.profile_authority)
        lab = ProviderCertificationLab(
            profile_authority=self.profile_authority, stack_authority=self.stack_authority,
            identity_authority=self.identity_authority, suite_authority=self.suite_authority,
            trial_authority=self.trial_authority, benchmark_authority=self.benchmark_authority,
            certification_authority=certification_authority, report_authority=self.report_authority,
            journal=journal, clock=clock, trial_forge=TrialForge(lambda case: factory.verify_case(case, truth)),
        )
        return lab, journal, clock

    def sealed_spec(self, case, twin, *, suite=None, runner=None, grader=None):
        suite = suite or self.suite; runner = runner or self.runner_actor; grader = grader or self.grader_actor
        spec = TrialSpec(
            "trial.one", self.profile.fingerprint(), self.descriptor.fingerprint(),
            self.descriptor.provider_id, self.descriptor.model_id, case.repository_snapshot_digest,
            twin.fingerprint(), case.dimension, suite.fingerprint(), case.semantic_fingerprint(),
            runner.fingerprint(), grader.fingerprint(),
        )
        return self.stack_authority.seal(spec, self.profile, self.descriptor, suite, runner, grader)

    def test_exact_stack_trial_hides_oracle_from_runner_and_rejects_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); indexed, truth, twin = self.repository(root)
            factory = ShadowBenchFactory(b"shadowbench-host-key-32-bytes-minimum!!")
            case = factory.generate(indexed.snapshot, truth, BenchmarkDimension.REPOSITORY_REASONING, epoch_label="epoch1")[0]
            lab, _, _ = self.build_lab(root, MemoryAnchor(), truth, factory)
            spec = self.sealed_spec(case, twin); runner = PassingRunner(); grader = PassingGrader()
            receipt = lab.run_trial(spec=spec, profile=self.profile, descriptor=self.descriptor, suite=self.suite,
                                    runner_actor=self.runner_actor, grader_actor=self.grader_actor,
                                    case=case, twin=twin, runner=runner, grader=grader)
            self.assertFalse(runner.saw_oracle_attribute); self.assertEqual(grader.last_oracle, case.oracle_digest)
            self.assertTrue(self.trial_authority.verify(receipt)); self.assertTrue(receipt.passed)
            with self.assertRaises(ValueError):
                lab.run_trial(spec=spec, profile=self.profile, descriptor=self.descriptor, suite=self.suite,
                              runner_actor=self.runner_actor, grader_actor=self.grader_actor,
                              case=case, twin=twin, runner=PassingRunner(), grader=PassingGrader())

    def test_one_shot_lineage_is_consumed_even_if_grader_proof_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); indexed, truth, twin = self.repository(root)
            factory = ShadowBenchFactory(b"shadowbench-host-key-32-bytes-minimum!!")
            case = factory.generate(indexed.snapshot, truth, BenchmarkDimension.DEBUGGING, epoch_label="epoch-proof")[0]
            lab, _, _ = self.build_lab(root, MemoryAnchor(), truth, factory); spec = self.sealed_spec(case, twin)
            with self.assertRaises(ValueError):
                lab.run_trial(spec=spec, profile=self.profile, descriptor=self.descriptor, suite=self.suite,
                              runner_actor=self.runner_actor, grader_actor=self.grader_actor,
                              case=case, twin=twin, runner=PassingRunner(), grader=EmptyProofGrader())
            with self.assertRaises(ValueError):
                lab.run_trial(spec=spec, profile=self.profile, descriptor=self.descriptor, suite=self.suite,
                              runner_actor=self.runner_actor, grader_actor=self.grader_actor,
                              case=case, twin=twin, runner=PassingRunner(), grader=PassingGrader())

    def test_same_runtime_object_cannot_be_runner_and_grader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); indexed, truth, twin = self.repository(root)
            factory = ShadowBenchFactory(b"shadowbench-host-key-32-bytes-minimum!!")
            case = factory.generate(indexed.snapshot, truth, BenchmarkDimension.REPOSITORY_REASONING, epoch_label="epoch2")[0]
            lab, _, _ = self.build_lab(root, MemoryAnchor(), truth, factory); endpoint = DualEndpoint()
            with self.assertRaises(ValueError):
                lab.run_trial(spec=self.sealed_spec(case, twin), profile=self.profile, descriptor=self.descriptor, suite=self.suite,
                              runner_actor=self.runner_actor, grader_actor=self.grader_actor,
                              case=case, twin=twin, runner=endpoint, grader=endpoint)

    def test_actor_endpoint_identity_cannot_collapse_with_different_lineage_labels(self):
        bad_grader = self.identity_authority.seal(LabActor(
            "grader.bad", LabActorRole.GRADER, "lineage.looks-different", self.runner_actor.endpoint_digest,
        ))
        spec = TrialSpec("trial.bad", self.profile.fingerprint(), self.descriptor.fingerprint(),
                         self.descriptor.provider_id, self.descriptor.model_id, "a"*64, "b"*64,
                         BenchmarkDimension.REPOSITORY_REASONING, self.suite.fingerprint(), "c"*64,
                         self.runner_actor.fingerprint(), bad_grader.fingerprint())
        with self.assertRaises(ValueError):
            self.stack_authority.seal(spec, self.profile, self.descriptor, self.suite, self.runner_actor, bad_grader)

    def test_stack_genome_prevents_provider_model_portability(self):
        altered = replace(self.descriptor, model_id="model-y")
        spec = TrialSpec("trial.drift", self.profile.fingerprint(), altered.fingerprint(), altered.provider_id, altered.model_id,
                         "a"*64, "b"*64, BenchmarkDimension.REPOSITORY_REASONING,
                         self.suite.fingerprint(), "c"*64, self.runner_actor.fingerprint(), self.grader_actor.fingerprint())
        with self.assertRaises(PermissionError):
            self.stack_authority.seal(spec, self.profile, altered, self.suite, self.runner_actor, self.grader_actor)

    def test_suite_family_cosmetic_names_cannot_fake_independence(self):
        other_name = self.suite_authority.seal(EvaluationSuite(
            "renamed-suite", "9.9.9", "totally-different-name", self.suite.independence_root,
            "other-generator-label", "9", sha("other-protocol"),
        ))
        self.assertEqual(self.suite.diversity_family(), other_name.diversity_family())
        self.assertNotEqual(self.suite.fingerprint(), other_name.fingerprint())

    def test_contamination_radar_can_only_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); indexed, truth, _ = self.repository(root)
            factory = ShadowBenchFactory(b"shadowbench-host-key-32-bytes-minimum!!")
            case = factory.generate(indexed.snapshot, truth, BenchmarkDimension.SECURITY, epoch_label="epoch1")[0]
            assessment = ContaminationRadar({case.semantic_fingerprint()}).assess(case)
            self.assertTrue(assessment.blocked); self.assertEqual(assessment.codes, ("known_exposure",))

    def test_atomic_reservation_allows_exactly_one_concurrent_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = DurableAttestationJournal(Path(tmp) / "journal.json", b"journal-key-32-bytes-minimum-secret!!", MemoryAnchor())
            subject = sha("same-lineage"); successes = []; failures = []
            def reserve():
                try: successes.append(journal.reserve_once(epoch=0, kind="trial-lineage", subject_digest=subject).sequence)
                except ValueError: failures.append(1)
            threads = [threading.Thread(target=reserve) for _ in range(8)]
            for thread in threads: thread.start()
            for thread in threads: thread.join()
            self.assertEqual(len(successes), 1); self.assertEqual(len(failures), 7); self.assertEqual(journal.sequence(), 1)

    def test_durable_journal_detects_signed_rollback_via_external_floor(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.json"; anchor = MemoryAnchor()
            journal = DurableAttestationJournal(path, b"journal-key-32-bytes-minimum-secret!!", anchor)
            journal.append(epoch=1, kind="trial", subject_digest=sha("one")); old_bytes = path.read_bytes()
            journal.append(epoch=2, kind="trial", subject_digest=sha("two")); self.assertEqual(anchor.floor(), 2)
            path.write_bytes(old_bytes)
            with self.assertRaises(PermissionError): DurableAttestationJournal(path, b"journal-key-32-bytes-minimum-secret!!", anchor)

    def test_durable_clock_survives_restart_and_cannot_move_backwards(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.json"; anchor = MemoryAnchor()
            clock = DurableChronoSealClock(DurableAttestationJournal(path, b"journal-key-32-bytes-minimum-secret!!", anchor)); clock.advance(9)
            restarted = DurableChronoSealClock(DurableAttestationJournal(path, b"journal-key-32-bytes-minimum-secret!!", anchor))
            self.assertEqual(restarted.now(), 9)
            with self.assertRaises(ValueError): restarted.advance(8)

    def test_benchmark_attestation_derives_suite_identity_and_rejects_tampering(self):
        receipt = self.trial_authority.seal(TrialReceipt(
            "receipt.synthetic", sha("trial"), self.profile.fingerprint(), self.suite.fingerprint(),
            BenchmarkDimension.DEBUGGING, sha("response"), True, False, False, False, 1, 1,
        ))
        result = self.benchmark_authority.issue("trusted.synthetic", self.profile.agent_id, self.profile.fingerprint(),
                                                BenchmarkDimension.DEBUGGING, self.suite, (receipt,))
        self.assertEqual(result.suite_family, self.suite.diversity_family()); self.assertEqual(result.suite, self.suite.suite_id)
        self.assertTrue(self.benchmark_authority.verify(result)); self.assertFalse(self.benchmark_authority.verify(replace(result, successes=0)))


if __name__ == "__main__": unittest.main()
