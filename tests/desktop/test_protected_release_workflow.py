from __future__ import annotations

"""Static audit of the protected-release workflow (HCODER-WO-0026, Context Lock Delta 002).

A workflow file cannot demonstrate its own safety by being reviewed: a job that
quietly drops an ``environment:``, widens ``permissions:`` or interpolates a secret
into a command line leaves the repository green and the release claim false. This
audit reads the YAML as text — the governed dependency lock admits no YAML parser,
and a parser would hide exactly the structural facts being checked here — and every
guard is paired with a synthetic mutation of the same text, so a guard that could
never fire is caught in this file rather than in production.

Self-reference law: where a guard is about *this* file it reads the syntax tree, not
a substring list. A tuple of forbidden call names written as source text contains
those very names, so a textual scan of this file fails for naming what it forbids.

Scope law: this audits the workflow that exists. It is not evidence that a signing
stage was ever executed, that a credential exists, or that an environment is
protected; the last is the objective work of the probe job itself, and this file
only proves that the probe is reachable and that nothing treats YAML intent as a
verdict.
"""

import ast
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "protected-release.yml"
PACKAGE_MATRIX = REPO_ROOT / ".github" / "workflows" / "native-package-matrix.yml"
VALIDATOR = REPO_ROOT / "tools" / "desktop" / "release_provenance.py"

PROBE_JOB = "probe-release-protection"
CREDENTIAL_JOBS = ("sign-windows", "sign-and-notarize-macos")
BUILD_JOBS = ("build-attest-windows", "build-attest-linux", "build-attest-macos")
JOB_ORDER = ("preflight", PROBE_JOB, *BUILD_JOBS, *CREDENTIAL_JOBS, "publish")
OIDC_PERMISSIONS = ("id-token", "attestations", "artifact-metadata")
SIGNING_ENVIRONMENT = "hive-release-signing"
PUBLISH_ENVIRONMENT = "hive-release-publish"
SIX_TARGETS = {
    "windows": {"msi", "nsis"},
    "linux": {"deb", "appimage"},
    "macos": {"app", "dmg"},
}
#: The order a build lane must exercise the contract in: mint the baseline, prove it
#: validates, advance the attestation once and re-prove, advance again and re-prove,
#: then ask the gate. A shorter or reordered sequence either skips a proof or lets a
#: stale document stand in for a fresh one.
BUILD_MODE_SEQUENCE = (
    "--build", "--verify", "--transition", "--verify", "--transition", "--verify", "--gate",
)
#: A handed-over document is judged again before any credential slot is named, so a
#: signing stage runs exactly these two modes and mints nothing of its own.
SIGNING_MODE_SEQUENCE = ("--verify", "--transition")
#: The label each lane must print to show that a verified attestation did not buy it
#: the requirement it still lacks. Windows lacks publisher signing only; macOS lacks
#: publisher signing and platform trust; Linux is allowed, so it demands neither.
SEPARATION_PROOFS = {
    "build-attest-windows": "SEPARATION_PROOF=VERIFIED_ATTESTATION_DOES_NOT_SATISFY_PUBLISHER_SIGNING",
    "build-attest-macos": "SEPARATION_PROOF=PLATFORM_TRUST_AND_PUBLISHER_SIGNING_ARE_SEPARATE_REQUIREMENTS",
}

#: Command forms that would install, launch or register a produced package, or hand
#: the product an updater. Build-prerequisite package management is deliberately not
#: in this list: installing ``libwebkit2gtk`` to compile is not the governed act, and
#: a guard that conflated them would forbid the canonical build law it preserves.
#: ``WindowsInstaller.Installer`` is absent for the same reason — the preserved
#: CP-0025 structural check opens an MSI *read-only* to query ``ProductVersion``, so
#: banning the noun would reject that evidence instead of the act of installing.
INSTALL_OR_EXECUTE_FORMS = (
    "msiexec",
    "Start-Process",
    "Invoke-Item",
    "dpkg -i",
    "rpm -i",
    "snap install",
    "install hive",
    "hdiutil attach",
    "open -a ",
    "systemctl",
    "plugins.updater",
    "updater",
)


def read(path: Path) -> str:
    # Text mode on purpose: a CRLF worktree checkout must audit the same as an LF one.
    return path.read_text(encoding="utf-8")


def job_blocks(text: str) -> dict[str, str]:
    """Split the ``jobs:`` mapping into per-job blocks by its two-space indentation."""
    lines = text.split("\n")
    try:
        start = next(index for index, line in enumerate(lines) if line == "jobs:")
    except StopIteration:
        raise AssertionError("workflow has no jobs: mapping") from None
    blocks: dict[str, str] = {}
    name: str | None = None
    buffer: list[str] = []
    for line in lines[start + 1 :]:
        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if match:
            if name is not None:
                blocks[name] = "\n".join(buffer)
            name, buffer = match.group(1), []
            continue
        if not line.startswith((" ", "#")) and line.strip():
            break
        if name is not None:
            buffer.append(line)
    if name is not None:
        blocks[name] = "\n".join(buffer)
    return blocks


def job_condition(job_text: str) -> str:
    """One job's ``if:`` expression, with a folded block scalar joined into one line.

    Reading only ``if: <rest of line>`` would return ``>-`` for a multi-line condition
    and then assert nothing at all, which is how a dropped opt-in would survive review.
    """
    lines = job_text.split("\n")
    for index, line in enumerate(lines):
        match = re.match(r"^    if:\s*(.*)$", line)
        if match is None:
            continue
        value = match.group(1).strip()
        if not value.startswith((">-", ">+", "|", ">")):
            return value
        collected: list[str] = []
        for follow in lines[index + 1 :]:
            if re.match(r"^    \S", follow) or (not follow.strip() and collected):
                break
            collected.append(follow.strip())
        return " ".join(part for part in collected if part)
    raise AssertionError("job has no if: condition")


def trigger_names(text: str) -> list[str]:
    """Names directly under the trigger mapping, so prose cannot satisfy the check."""
    lines = text.split("\n")
    try:
        start = next(index for index, line in enumerate(lines) if re.match(r"^on:\s*$", line))
    except StopIteration:
        start = next(
            index for index, line in enumerate(lines) if re.match(r"^True:\s*$", line)
        )
    names: list[str] = []
    for line in lines[start + 1 :]:
        if not line.startswith(" ") and line.strip():
            break
        match = re.match(r"^  ([A-Za-z0-9_]+):", line)
        if match:
            names.append(match.group(1))
    return names


def run_bodies(text: str) -> list[str]:
    """Command text of every ``run:`` block, with each block's own indent removed."""
    lines = text.split("\n")
    bodies: list[str] = []
    index = 0
    while index < len(lines):
        header = re.match(r"^(\s*)run:\s*\|?\s*$", lines[index])
        if not header:
            index += 1
            continue
        index += 1
        collected: list[str] = []
        base_indent: int | None = None
        while index < len(lines):
            line = lines[index]
            if not line.strip():
                collected.append("")
                index += 1
                continue
            indent = len(line) - len(line.lstrip())
            if base_indent is None:
                if indent <= len(header.group(1)):
                    break
                base_indent = indent
            if indent < base_indent:
                break
            collected.append(line[base_indent:])
            index += 1
        bodies.append("\n".join(collected))
    return bodies


def permission_keys(job_text: str) -> list[str]:
    """The ``permissions:`` keys a job grants itself, without their values."""
    match = re.search(r"^    permissions:\n((?:^      \S.*\n)+)", job_text, re.MULTILINE)
    return [line.split(":")[0].strip() for line in match.group(1).splitlines()] if match else []


#: The validator's modes, longest name first so ``--verify-tag`` cannot read as
#: ``--verify``.
VALIDATOR_MODES = ("environment-protection", "channel-gate", "build", "verify", "gate", "transition")


def validator_invocations(job_text: str) -> list[str]:
    """Each ``-m tools.desktop.release_provenance`` call, continuations joined.

    The heredoc bodies of the packaging steps import the same module without invoking
    its CLI, and a comment naming a mode is not a mode being executed.
    """
    statements: list[str] = []
    for body in run_bodies(job_text):
        pending = ""
        for raw in body.split("\n"):
            line = raw.strip()
            if pending:
                line, pending = (pending + " " + line), ""
            if not line or line.startswith("#"):
                continue
            if line.endswith("\\"):
                pending = line[:-1].strip()
                continue
            if "-m tools.desktop.release_provenance" in line:
                statements.append(line)
    return statements


def validator_modes(job_text: str) -> list[str]:
    """The modes a job executes, in document order, counted per real invocation."""
    found: list[str] = []
    for line in validator_invocations(job_text):
        match = re.search(r"--(%s)(?![\w-])" % "|".join(VALIDATOR_MODES), line)
        if match:
            found.append("--" + match.group(1))
    return found


def step_texts(job_text: str) -> list[str]:
    parts = re.split(r"(?m)^      - ", job_text)
    return parts[1:]


def command_lines(text: str, needle: str) -> list[str]:
    """Lines that execute ``needle``; a commented-out command executes nothing.

    ``actions/attest`` can be declared without ever being verified, and a step that
    echoes a pass label whose verification line has been commented out is the exact
    shape this audit must refuse, so detection is by command rather than by keyword.
    """
    return [
        line
        for body in run_bodies(text)
        for line in body.split("\n")
        if needle in line and not line.strip().startswith("#")
    ]


def step_with_command(job_text: str, needle: str) -> int:
    for index, step in enumerate(step_texts(job_text)):
        if command_lines(step, needle):
            return index
    raise AssertionError("no step executes %r" % needle)


def invocation_step_indexes(job_text: str) -> list[tuple[int, str]]:
    """(step index, mode) for every validator mode a step really executes."""
    return [
        (index, mode)
        for index, step in enumerate(step_texts(job_text))
        for mode in validator_modes(step)
    ]


def step_index(job_text: str, needle: str) -> int:
    for index, step in enumerate(step_texts(job_text)):
        if needle in step:
            return index
    raise AssertionError(f"no step mentioning {needle!r}")


def imported_modules(source: str) -> set[str]:
    """Top-level modules this file imports, taken from the syntax tree."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def called_tails(source: str) -> list[str]:
    """The final name of every callable expression, e.g. ``Path(x).write_text``."""
    tails: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            cursor = node.func
            while isinstance(cursor, ast.Attribute):
                cursor = cursor.value
            if isinstance(node.func, ast.Attribute):
                tails.append(node.func.attr)
            elif isinstance(cursor, ast.Name):
                tails.append(cursor.id)
    return tails


def path_expressions(source: str) -> set[tuple[str, ...]]:
    """Each ``REPO_ROOT / "…"`` chain as its literal components."""
    found: set[tuple[str, ...]] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
            continue
        parts: list[str] = []
        cursor: ast.expr = node
        reached_root = True
        while isinstance(cursor, ast.BinOp) and isinstance(cursor.op, ast.Div):
            if isinstance(cursor.right, ast.Constant) and isinstance(cursor.right.value, str):
                parts.append(cursor.right.value)
                cursor = cursor.left
            else:
                reached_root = False
                break
        if reached_root and isinstance(cursor, ast.Name) and cursor.id == "REPO_ROOT":
            found.add(tuple(reversed(parts)))
    # A chain also contains its own prefixes as sub-expressions; only the full paths
    # describe a file, so the prefixes are dropped rather than judged.
    return {path for path in found if not any(other != path and other[: len(path)] == path for other in found)}


def path_arguments(source: str) -> set[str]:
    """Every argument passed to ``Path(...)``, as source text."""
    return {
        ast.unparse(node.args[0])
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Path" and node.args
    }


class WorkflowStructureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.jobs = job_blocks(self.text)

    def test_the_file_audited_is_the_one_the_lane_runs(self) -> None:
        self.assertTrue(WORKFLOW.is_file())
        self.assertIn("name: Protected Release", self.text)

    def test_job_splitter_sees_every_job_in_document_order(self) -> None:
        """The splitter's output order is load-bearing: several guards index by name."""
        self.assertEqual(list(JOB_ORDER), list(self.jobs))
        self.assertEqual(8, len(self.jobs))
        shrunk = self.text.replace("  sign-windows:", "  renamed-sign-windows:")
        self.assertNotIn("sign-windows", job_blocks(shrunk))
        self.assertEqual(8, len(job_blocks(shrunk)))

    def test_a_trigger_is_read_from_the_trigger_mapping_not_from_prose(self) -> None:
        """Mutation: add a real ``pull_request_target:`` trigger and this fails.

        The file discusses that trigger in a comment, which is why the check reads the
        mapping rather than searching the text.
        """
        self.assertEqual(["pull_request", "push", "workflow_dispatch"], trigger_names(self.text))
        self.assertNotIn("pull_request_target", trigger_names(self.text))
        widened = self.text.replace(
            "  pull_request:\n", "  pull_request:\n  pull_request_target:\n", 1
        )
        self.assertIn("pull_request_target", trigger_names(widened))

    def test_the_readers_distinguish_a_folded_condition_from_a_single_line_one(self) -> None:
        """Guards that read ``if:`` would silently pass on ``if: >-`` if they took the line."""
        self.assertIn("workflow_dispatch", job_condition(self.jobs["publish"]))
        self.assertEqual(
            "github.event_name == 'workflow_dispatch' && "
            "needs.probe-release-protection.outputs.proven == 'true'",
            job_condition(self.jobs["sign-windows"]),
        )
        folded = job_condition("    if: >-\n      alpha &&\n      beta\n    needs: []\n")
        self.assertEqual("alpha && beta", folded)
        self.assertEqual("alpha", job_condition("    if: alpha\n    needs: []\n"))


class LeastPrivilegeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.jobs = job_blocks(self.text)

    def test_repository_wide_permissions_are_read_only(self) -> None:
        top = re.search(r"^permissions:\n((?:^  \S.*\n)+)", self.text, re.MULTILINE)
        self.assertIsNotNone(top)
        self.assertEqual(["contents: read"], [line.strip() for line in top.group(1).splitlines()])
        widened = self.text.replace(
            "permissions:\n  contents: read\n", "permissions:\n  contents: write\n", 1
        )
        self.assertNotEqual(
            ["contents: read"],
            [
                line.strip()
                for line in re.search(
                    r"^permissions:\n((?:^  \S.*\n)+)", widened, re.MULTILINE
                ).group(1).splitlines()
            ],
        )

    def test_exactly_one_job_can_write_repository_content(self) -> None:
        writers = [name for name, block in self.jobs.items() if "contents" in permission_keys(block) and "contents: write" in block]
        self.assertEqual(["publish"], writers)
        for name in ("preflight", PROBE_JOB, *BUILD_JOBS, *CREDENTIAL_JOBS):
            self.assertIn("contents", permission_keys(self.jobs[name]), name)
        leaked = self.jobs["sign-windows"].replace("contents: read", "contents: write")
        widened = self.text.replace(self.jobs["sign-windows"], leaked, 1)
        self.assertEqual(
            {"publish", "sign-windows"},
            {
                name
                for name, block in job_blocks(widened).items()
                if "contents: write" in block
            },
        )

    def test_release_identity_permissions_reach_only_the_attestation_jobs(self) -> None:
        for name, block in self.jobs.items():
            granted = set(permission_keys(block))
            if name in BUILD_JOBS:
                self.assertEqual(set(OIDC_PERMISSIONS), granted & set(OIDC_PERMISSIONS), name)
            else:
                self.assertEqual(set(), granted & set(OIDC_PERMISSIONS), name)
        granted_away = self.jobs["publish"].replace(
            "permissions:\n      contents: write\n",
            "permissions:\n      contents: write\n      id-token: write\n",
            1,
        )
        widened = self.text.replace(self.jobs["publish"], granted_away, 1)
        self.assertIn("id-token", permission_keys(job_blocks(widened)["publish"]))

    def test_signing_jobs_hold_no_write_and_no_oidc_authority(self) -> None:
        for name in CREDENTIAL_JOBS:
            self.assertEqual(["contents"], permission_keys(self.jobs[name]), name)
            self.assertNotIn("id-token", self.jobs[name])


class CredentialReachabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.jobs = job_blocks(self.text)

    def test_every_environment_bound_job_is_dispatch_gated_and_probe_dependent(self) -> None:
        bound = [
            name
            for name, block in self.jobs.items()
            if re.search(r"^    environment: \S", block, re.MULTILINE)
        ]
        self.assertEqual(sorted([*CREDENTIAL_JOBS, "publish"]), sorted(bound))
        for name in bound:
            condition = job_condition(self.jobs[name])
            self.assertIn("workflow_dispatch", condition, name)
            self.assertIn("outputs.proven", condition, name)
            self.assertIn(PROBE_JOB, self.jobs[name], name)
        stripped = self.jobs["sign-windows"].replace(
            "if: github.event_name == 'workflow_dispatch' && needs.probe-release-protection.outputs.proven == 'true'",
            "if: needs.probe-release-protection.outputs.proven == 'true'",
            1,
        )
        widened = self.text.replace(self.jobs["sign-windows"], stripped, 1)
        self.assertNotIn(
            "workflow_dispatch", job_condition(job_blocks(widened)["sign-windows"])
        )

    def test_signing_authority_and_publication_authority_are_different_environments(self) -> None:
        """One environment would let a signing grant alone ever reach ``gh release``."""
        named = {
            name: re.search(r"^    environment: (\S+)", block, re.MULTILINE).group(1)
            for name, block in self.jobs.items()
            if re.search(r"^    environment: \S", block, re.MULTILINE)
        }
        self.assertEqual(
            {
                "sign-windows": SIGNING_ENVIRONMENT,
                "sign-and-notarize-macos": SIGNING_ENVIRONMENT,
                "publish": PUBLISH_ENVIRONMENT,
            },
            named,
        )
        for name in ("preflight", PROBE_JOB, *BUILD_JOBS):
            self.assertNotIn("environment:", self.jobs[name], name)

    def test_the_two_signing_stages_are_isolated_per_operating_system(self) -> None:
        self.assertEqual("windows-latest", re.search(r"runs-on: (\S+)", self.jobs["sign-windows"]).group(1))
        self.assertEqual("macos-latest", re.search(r"runs-on: (\S+)", self.jobs["sign-and-notarize-macos"]).group(1))
        for name in CREDENTIAL_JOBS:
            self.assertIn(f"{PROBE_JOB}.outputs.proven", self.jobs[name])
        merged = self.jobs["sign-and-notarize-macos"].replace(
            "runs-on: macos-latest", "runs-on: windows-latest"
        )
        widened = self.text.replace(self.jobs["sign-and-notarize-macos"], merged, 1)
        self.assertEqual(
            "windows-latest",
            re.search(r"runs-on: (\S+)", job_blocks(widened)["sign-and-notarize-macos"]).group(1),
        )

    def test_no_secret_reaches_a_command_line(self) -> None:
        """A secret in ``run:`` is readable by whoever can read the run log.

        Mutations: interpolate a secret into a command on either path and this fails.
        """
        for name, block in self.jobs.items():
            for body in run_bodies(block):
                self.assertNotIn("secrets.", body, name)
        interpolated = self.jobs["sign-windows"].replace(
            "for slot in AZURE_ARTIFACT_SIGNING_ENDPOINT",
            'gh auth login --with-token <<< "${{ secrets.GITHUB_TOKEN }}"\n          for slot in AZURE_ARTIFACT_SIGNING_ENDPOINT',
            1,
        )
        widened = self.text.replace(self.jobs["sign-windows"], interpolated, 1)
        self.assertTrue(
            any("secrets." in body for body in run_bodies(job_blocks(widened)["sign-windows"]))
        )

    def test_pull_request_reachable_jobs_fetch_nothing_with_a_token(self) -> None:
        for name in ("preflight", PROBE_JOB):
            self.assertNotIn("GH_TOKEN", self.jobs[name])
            self.assertNotIn("GITHUB_TOKEN", self.jobs[name])
        tokenned = self.jobs[PROBE_JOB].replace("curl -sS", "GH_TOKEN=x curl -sS", 1)
        widened = self.text.replace(self.jobs[PROBE_JOB], tokenned, 1)
        self.assertIn("GH_TOKEN", job_blocks(widened)[PROBE_JOB])


class EnvironmentProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.jobs = job_blocks(self.text)
        self.probe = self.jobs[PROBE_JOB]

    def test_the_probe_asks_the_validator_rather_than_shell_folk_law(self) -> None:
        calls = "\n".join(validator_invocations(self.probe))
        self.assertIn("--environment-protection", validator_modes(self.probe))
        self.assertIn("--environment-record", calls)
        self.assertIn("--environment-name", calls)
        moved = self.probe.replace("--environment-protection", "--gate")
        widened = self.text.replace(self.probe, moved, 1)
        self.assertNotIn("--environment-protection", validator_modes(job_blocks(widened)[PROBE_JOB]))
        self.assertNotIn(
            "--environment-protection",
            "\n".join(run_bodies(job_blocks(widened)[PROBE_JOB])),
        )

    def test_a_missing_environment_is_named_not_forgiven(self) -> None:
        """GitHub creates an absent environment instead of failing, so absence is a state."""
        self.assertIn("404", self.probe)
        self.assertIn("ENVIRONMENT_ABSENT", self.probe)
        self.assertIn("is neither a record nor an absence", self.probe)

    def test_the_probed_fields_are_the_protection_semantics_the_validator_judges(self) -> None:
        from tools.desktop.release_provenance import ENVIRONMENT_RECORD_KEYS, assess_protection

        source = read(VALIDATOR)
        for field in ENVIRONMENT_RECORD_KEYS:
            self.assertIn(field, source)
        self.assertIn("required_reviewers", source)
        self.assertIn("prevent_self_review", source)
        self.assertIn("can_admins_bypass", source)
        """The probe claims it reads real records, so the judge must reject a blank one."""
        with self.assertRaises(Exception):
            assess_protection({"name": PUBLISH_ENVIRONMENT})

    def test_an_unproven_gate_blocks_the_promotion_path(self) -> None:
        bodies = run_bodies(self.probe)
        refusal = [body for body in bodies if "BLOCKED_PROTECTED_ENVIRONMENT" in body]
        self.assertEqual(1, len(refusal))
        self.assertIn("exit 1", refusal[0])
        self.assertIn("can_admins_bypass", "\n".join(bodies))
        softened = self.probe.replace("exit 1\n", "exit 0\n", 1)
        widened = self.text.replace(self.probe, softened, 1)
        self.assertTrue(
            all(
                "exit 1" not in body
                for body in run_bodies(job_blocks(widened)[PROBE_JOB])
                if "BLOCKED_PROTECTED_ENVIRONMENT" in body
            )
        )

    def test_the_verdict_travels_as_a_job_output_not_as_a_remembered_string(self) -> None:
        self.assertRegex(
            self.probe, r"outputs:\n\s+proven: \$\{\{ steps\.[a-z]+\.outputs\.proven \}\}"
        )
        self.assertIn('echo "proven=$proven" >> "$GITHUB_OUTPUT"', self.probe)
        self.assertIn("YAML_INTENT_COUNTS_AS_EVIDENCE=NO", self.probe)


class ProvenanceStageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.jobs = job_blocks(self.text)

    def test_the_contract_is_exercised_end_to_end(self) -> None:
        for name in BUILD_JOBS:
            self.assertEqual(list(BUILD_MODE_SEQUENCE), validator_modes(self.jobs[name]), name)
        for name in CREDENTIAL_JOBS:
            self.assertEqual(list(SIGNING_MODE_SEQUENCE), validator_modes(self.jobs[name]), name)
        self.assertIn("--channel-gate", validator_modes(self.jobs["publish"]))
        self.assertIn("--channel-gate", validator_modes(self.jobs["preflight"]))
        generation_removed = self.jobs["build-attest-linux"].replace(
            "--build \\\n", "--verify \\\n"
        )
        widened = self.text.replace(self.jobs["build-attest-linux"], generation_removed, 1)
        self.assertNotIn("--build", validator_modes(job_blocks(widened)["build-attest-linux"]))

    def test_attestation_generation_and_independent_verification_are_different_steps(self) -> None:
        for name in BUILD_JOBS:
            block = self.jobs[name]
            produced = step_index(block, "uses: actions/attest@")
            checked = step_with_command(block, "gh attestation verify")
            self.assertLess(produced, checked, name)
            self.assertEqual([], command_lines(step_texts(block)[produced], "gh attestation verify"))
            self.assertEqual(1, len(command_lines(block, "gh attestation verify")), name)
            self.assertIn("ATTESTATION_VERIFICATION=PASSED", step_texts(block)[checked], name)
        victim = self.jobs["build-attest-linux"]
        with self.assertRaises(AssertionError):
            step_with_command(
                victim.replace("gh attestation verify", "# gh attestation verify", 1),
                "gh attestation verify",
            )

    def test_the_attested_subject_is_the_bound_inventory_bytes(self) -> None:
        for name in BUILD_JOBS:
            self.assertIn("canonical_bytes", self.jobs[name], name)
            self.assertIn("ATTESTATION_SUBJECT_IS_NOT_CANONICAL_INVENTORY_BYTES", self.jobs[name], name)
            self.assertIn("subject-path:", self.jobs[name], name)
        unbound = self.jobs["build-attest-linux"].replace(
            "ATTESTATION_SUBJECT_IS_NOT_CANONICAL_INVENTORY_BYTES", "echo fine"
        )
        widened = self.text.replace(self.jobs["build-attest-linux"], unbound, 1)
        self.assertNotIn(
            "ATTESTATION_SUBJECT_IS_NOT_CANONICAL_INVENTORY_BYTES",
            job_blocks(widened)["build-attest-linux"],
        )

    def test_the_attestation_state_advances_in_two_proved_steps(self) -> None:
        for name in BUILD_JOBS:
            block = self.jobs[name]
            self.assertIn('"status": "generated"', block, name)
            self.assertIn('attestation["status"] = "verified"', block, name)
            self.assertEqual(2, validator_modes(block).count("--transition"), name)
            self.assertLess(
                step_index(block, '"status": "generated"'),
                step_index(block, 'attestation["status"] = "verified"'),
                name,
            )
        victim = self.jobs["build-attest-macos"]
        at = victim.index("--transition")
        collapsing = victim[:at] + "--verify" + victim[at + len("--transition") :]
        self.assertEqual(1, validator_modes(collapsing).count("--transition"))
        self.assertEqual(2, validator_modes(victim).count("--transition"))

    def test_a_verified_attestation_never_clears_publisher_signing(self) -> None:
        for name, label in SEPARATION_PROOFS.items():
            bodies = "\n".join(run_bodies(self.jobs[name]))
            self.assertIn("RELEASE_GATE=DENY", bodies, name)
            self.assertIn("publisher-signing-unverified", bodies, name)
            self.assertIn(label, bodies, name)
            self.assertIn("build-provenance-attestation-unverified", bodies, name)
        macos = "\n".join(run_bodies(self.jobs["build-attest-macos"]))
        for package_type in sorted(SIX_TARGETS["macos"]):
            self.assertIn(f"publisher-signing-unverified:{package_type}", macos)
            self.assertIn(f"platform-trust-unverified:{package_type}", macos)
        self.assertIn('grep -qx "REASON=$reason"', macos)
        self.assertIn("MISSING_REQUIRED_REFUSAL", macos)
        softened = self.jobs["build-attest-windows"].replace(
            'echo "$out" | grep -qx "REASON=publisher-signing-unverified:msi"', "true"
        )
        softened = softened.replace(
            "SEPARATION_PROOF=VERIFIED_ATTESTATION_DOES_NOT_SATISFY_PUBLISHER_SIGNING", "echo ok"
        )
        widened = self.text.replace(self.jobs["build-attest-windows"], softened, 1)
        windows_bodies = "\n".join(run_bodies(job_blocks(widened)["build-attest-windows"]))
        self.assertNotIn("REASON=publisher-signing-unverified:msi", windows_bodies)
        self.assertNotIn("VERIFIED_ATTESTATION_DOES_NOT_SATISFY", windows_bodies)

    def test_linux_is_never_charged_for_a_signature_it_cannot_have(self) -> None:
        """Linux has no publisher-trust model to satisfy, so the lane must demand none.

        The lane still *names* the refusal reason, because it fails the build if the
        gate ever emits it. What must be absent is a requirement for it.
        """
        bodies = "\n".join(run_bodies(self.jobs["build-attest-linux"]))
        self.assertIn("RELEASE_GATE=ALLOW", bodies)
        self.assertIn("GATE_INVENTED_A_PUBLISHER_REQUIREMENT_FOR_LINUX", bodies)
        self.assertIn("SEPARATION_PROOF=NO_PUBLISHER_TRUST_MODEL_DEMANDED", bodies)
        self.assertNotIn('grep -qx "REASON=publisher-signing-unverified', bodies)
        charged = self.jobs["build-attest-linux"].replace(
            'if echo "$out" | grep -q "publisher-signing-unverified"; then',
            'echo "$out" | grep -qx "REASON=publisher-signing-unverified:deb"\n          if echo "$out" | grep -q "publisher-signing-unverified"; then',
            1,
        )
        widened = self.text.replace(self.jobs["build-attest-linux"], charged, 1)
        linux_bodies = "\n".join(run_bodies(job_blocks(widened)["build-attest-linux"]))
        self.assertIn('grep -qx "REASON=publisher-signing-unverified', linux_bodies)
        self.assertIn("REASON=publisher-signing-unverified:deb", linux_bodies)


class PackagingPreservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.matrix = read(PACKAGE_MATRIX)
        self.jobs = job_blocks(self.text)

    def _bundle_sets(self, text: str) -> dict[str, set[str]]:
        sets: dict[str, set[str]] = {}
        for name, block in job_blocks(text).items():
            for match in re.finditer(r"--bundles ([a-z,]+)", block):
                platform = name.split("-")[-1]
                sets.setdefault(platform, set()).update(match.group(1).split(","))
        return sets

    def test_the_six_target_matrix_is_not_reduced(self) -> None:
        here = self._bundle_sets(self.text)
        self.assertEqual(SIX_TARGETS, here)
        self.assertEqual(SIX_TARGETS["macos"], self._bundle_sets(self.matrix)["macos"])
        reduced = self.jobs["build-attest-macos"].replace("--bundles app,dmg", "--bundles dmg")
        widened = self.text.replace(self.jobs["build-attest-macos"], reduced, 1)
        self.assertEqual({"app"}, SIX_TARGETS["macos"] - self._bundle_sets(widened)["macos"])

    def test_the_canonical_config_stays_immutable_in_this_lane(self) -> None:
        for name in BUILD_JOBS:
            block = self.jobs[name]
            self.assertEqual(1, len(re.findall(r"git diff --quiet", block)), name)
            self.assertIn("hive-bundle-overlay.json", block, name)
            self.assertIn("$RUNNER_TEMP", block, name)
        self.assertEqual(len(BUILD_JOBS), len(re.findall(r"git diff --quiet", self.text)))
        widened = self.text.replace("git diff --quiet", "git diff --stat", 1)
        self.assertEqual(len(BUILD_JOBS) - 1, len(re.findall(r"git diff --quiet", widened)))

    def test_the_overlay_is_never_uploaded(self) -> None:
        for name in BUILD_JOBS:
            self.assertIn("OVERLAY_UPLOADED=NO", self.jobs[name], name)
            uploaded = self.jobs[name].split("path: |")[-1]
            self.assertNotIn("hive-bundle-overlay.json", uploaded, name)
        leaking = self.jobs["build-attest-linux"].replace(
            "path: |\n", "path: |\n            apps/desktop/src-tauri/hive-bundle-overlay.json\n", 1
        )
        self.assertIn(
            "hive-bundle-overlay.json",
            job_blocks(self.text.replace(self.jobs["build-attest-linux"], leaking, 1))[
                "build-attest-linux"
            ].split("path: |")[-1],
        )

    def test_nothing_installs_executes_or_updates_a_produced_package(self) -> None:
        for name, block in self.jobs.items():
            for body in run_bodies(block):
                for form in INSTALL_OR_EXECUTE_FORMS:
                    self.assertNotIn(form, body, f"{name}: {form}")
        installing = self.jobs["build-attest-windows"].replace(
            'Write-Output "STRUCTURAL_CHECK_WINDOWS=PASS"',
            "Start-Process msiexec.exe -ArgumentList '/i', $msi.FullName -Wait",
            1,
        )
        widened = self.text.replace(self.jobs["build-attest-windows"], installing, 1)
        self.assertTrue(
            any(
                "msiexec" in body
                for body in run_bodies(job_blocks(widened)["build-attest-windows"])
            )
        )

    def test_the_publish_lane_cites_no_signing_endpoint(self) -> None:
        self.assertNotIn("AZURE", self.jobs["publish"])
        self.assertNotIn("APPLE_", self.jobs["publish"])
        self.assertNotIn("endpoint", self.jobs["publish"])


class SigningBarrierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.jobs = job_blocks(self.text)

    def test_each_signing_stage_ends_in_an_unconditional_refusal(self) -> None:
        for name in CREDENTIAL_JOBS:
            bodies = run_bodies(self.jobs[name])
            self.assertTrue(bodies, name)
            self.assertIn("exit 1", bodies[-1], name)
            self.assertIn("BLOCKED_EXTERNAL_CREDENTIALS_AND_UNIMPLEMENTED_SIGNING", bodies[-1], name)
        softened = self.jobs["sign-windows"].replace("exit 1", "echo PROVISIONED", 1)
        widened = self.text.replace(self.jobs["sign-windows"], softened, 1)
        self.assertNotIn("exit 1", run_bodies(job_blocks(widened)["sign-windows"])[-1])

    def test_the_refusal_does_not_depend_on_credential_presence(self) -> None:
        """Mutation: make the failure conditional on a slot and a provisioned run goes green."""
        for name in CREDENTIAL_JOBS:
            refusal = run_bodies(self.jobs[name])[-1]
            self.assertNotIn("SLOT_PRESENT", refusal, name)
            self.assertNotIn("[ -z", refusal, name)
            self.assertNotIn("printenv", refusal, name)
            self.assertEqual(0, len(re.findall(r"if ", refusal)), name)

    def test_slots_are_reported_as_class_name_and_condition_without_values(self) -> None:
        for name in CREDENTIAL_JOBS:
            block = self.jobs[name]
            self.assertIn("CREDENTIAL_CLASS=", block, name)
            self.assertIn("VERIFICATION_CONDITION=", block, name)
            self.assertIn("VALUES_READ=NO VALUES_PRINTED=NO VALUES_PERSISTED=NO", block, name)
            bodies = "\n".join(run_bodies(block))
            self.assertNotIn("echo \"$APPLE", bodies)
            self.assertNotIn("echo \"$AZURE", bodies)
            self.assertIsNone(re.search(r"echo \$\{?[A-Z_]*CERTIFICATE", bodies))
        printing = self.jobs["sign-and-notarize-macos"].replace(
            "if [ -z \"$(printenv \"$slot\")\" ]",
            "if [ -z \"$(printenv \"$slot\")\" ]; then echo \"$slot\"",
            1,
        )
        self.assertIn('echo "$slot"', printing)

    def test_the_handover_is_reverified_before_any_credential_is_reachable(self) -> None:
        for name in CREDENTIAL_JOBS:
            block = self.jobs[name]
            judged = [index for index, mode in invocation_step_indexes(block)]
            download = step_index(block, "download-artifact")
            slots = step_index(block, "SLOT_ABSENT")
            self.assertEqual(2, len(judged), name)
            self.assertLess(download, min(judged), name)
            self.assertLess(max(judged), slots, name)


class PublicationGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(WORKFLOW)
        self.jobs = job_blocks(self.text)
        self.publish = self.jobs["publish"]

    def test_publication_needs_both_an_environment_and_an_explicit_opt_in(self) -> None:
        self.assertIn(f"environment: {PUBLISH_ENVIRONMENT}", self.publish)
        condition = job_condition(self.publish)
        self.assertIn("github.event.inputs.publish_intended == 'true'", condition)
        self.assertIn("workflow_dispatch", condition)
        self.assertIn("outputs.proven", condition)
        silently_auto = self.text.replace(
            "      github.event.inputs.publish_intended == 'true' &&\n", "", 1
        )
        self.assertNotIn(
            "publish_intended", job_condition(job_blocks(silently_auto)["publish"])
        )

    def test_the_opt_in_default_is_false(self) -> None:
        block = re.search(r"publish_intended:.*?\n(?=\S|\n\S)", self.text, re.DOTALL)
        self.assertIsNotNone(block)
        self.assertIn("default: false", block.group(0))
        self.assertIn("type: boolean", block.group(0))
        opened = block.group(0).replace("default: false", "default: true")
        widened = self.text.replace(block.group(0), opened, 1)
        self.assertNotIn(
            "default: false",
            re.search(r"publish_intended:.*?\n(?=\S|\n\S)", widened, re.DOTALL).group(0),
        )

    def test_publication_requeries_the_gate_instead_of_trusting_its_needs(self) -> None:
        modes = validator_modes(self.publish)
        self.assertEqual(["--gate", "--channel-gate"], [m for m in modes if m != "--verify"])
        self.assertTrue(modes.index("--gate") < modes.index("--channel-gate"))
        gate = next(body for body in run_bodies(self.publish) if "--gate" in body)
        self.assertIn("for platform in windows linux macos", gate)
        self.assertIn("EVIDENCE_MISSING", gate)
        self.assertNotIn("|| true", gate)
        silenced = self.publish.replace(
            "-m tools.desktop.release_provenance --gate",
            "-m tools.desktop.release_provenance --verify",
            1,
        )
        self.assertNotIn("--gate", validator_modes(silenced))

    def test_nothing_is_published_without_a_protected_tag(self) -> None:
        bodies = "\n".join(run_bodies(self.publish))
        self.assertIn("--verify-tag", bodies)
        self.assertIn("PROTECTED_TAG_ABSENT", bodies)
        self.assertIn(
            "RELEASE_SUBSTRATE_STOPPED=BLOCKED_EXTERNAL_CREDENTIALS_AND_UNIMPLEMENTED_SIGNING",
            bodies,
        )

    def test_the_lane_names_the_slice_it_belongs_to(self) -> None:
        self.assertIn("HCODER-WO-0026", self.text)
        self.assertIn("DEC-030", self.text)


class NoSelfReferenceTests(unittest.TestCase):
    """The audit's own boundary, read from its syntax tree.

    A textual scan of this file for forbidden names fails for naming them, so the
    checks below walk the parsed module instead.
    """

    #: ``tools`` is here because the probe guard checks the field names against the
    #: validator it is the probe's job to call; it is the only local import allowed.
    ALLOWED_IMPORTS = {"__future__", "ast", "re", "unittest", "pathlib", "tools"}
    ALLOWED_TOP_LEVEL_DIRECTORIES = {".github", "tools"}

    def setUp(self) -> None:
        self.source = read(Path(__file__))

    def _path_roots(self) -> set[tuple[str, ...]]:
        return path_expressions(self.source)

    @classmethod
    def _outside(cls, paths) -> list[tuple[str, ...]]:
        """The predicate this test applies, kept in one place so it can be aimed."""
        return [
            parts
            for parts in paths
            if parts[0] not in cls.ALLOWED_TOP_LEVEL_DIRECTORIES
            or (parts[0] == ".github" and parts[1:2] != ("workflows",))
        ]

    def test_it_imports_no_execution_or_walking_surface(self) -> None:
        self.assertEqual(set(), imported_modules(self.source) - self.ALLOWED_IMPORTS)
        widened = imported_modules("import subprocess\nimport shutil\n")
        self.assertEqual({"subprocess", "shutil"}, widened - self.ALLOWED_IMPORTS)

    def test_it_makes_no_write_or_execution_call(self) -> None:
        forbidden = {
            "write_text", "write_bytes", "open", "mkdir", "unlink", "touch", "remove",
            "rename", "rmtree", "system", "popen", "run", "check_call", "check_output",
            "chmod", "chown", "symlink", "spawn",
        }
        tails = set(called_tails(self.source))
        self.assertEqual(set(), tails & forbidden, tails & forbidden)
        self.assertTrue(forbidden & set(called_tails("Path('x').write_text('y')\nsubprocess.run([])\n")))

    def test_it_reads_only_workflows_and_the_validator(self) -> None:
        roots = self._path_roots()
        self.assertEqual([], self._outside(roots), roots)
        self.assertEqual(3, len(roots), roots)
        self.assertIn((".github", "workflows", "protected-release.yml"), roots)
        self.assertIn(("tools", "desktop", "release_provenance.py"), roots)
        self.assertEqual({"__file__"}, path_arguments(self.source))

    def test_the_path_predicate_is_not_blind_to_an_escaping_read(self) -> None:
        """A guard that accepts every path is the same as no guard at all."""
        widened = "\n".join(
            (
                'A = REPO_ROOT / ".aws" / "credentials"',
                'B = REPO_ROOT / ".github" / "actions" / "x.yml"',
                'C = REPO_ROOT / ".github" / "workflows" / "other.yml"',
            )
        )
        self.assertEqual(
            {(".aws", "credentials"), (".github", "actions", "x.yml")},
            set(self._outside(path_expressions(widened))),
        )


if __name__ == "__main__":
    unittest.main()
