# Evidence Bundle — HCODER-WO-0026

**Status:** CORRECTION CANDIDATE READY FOR INDEPENDENT REVIEW — SECRET-INDEPENDENT SUBSTRATE, CANDIDATE IN A DRAFT PR, NOT PROMOTED
**Canonical base:** `HCODER-CP-0025` / `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`
**Issue:** `#85`
**Parent epic:** `HCODER-DIST-001` / Issue `#72`
**Slice:** `HCODER-DIST-001C`
**Decision:** `DEC-030` — PROPOSED / NOT CANONICAL, with no canonical force while this Work Order is unreviewed
**Correction authority:** `HCODER-WO-0026`; the canonical append-only delta history lives in `.engineering/context-locks/HCODER-WO-0026.md`, and no terminal delta number or range is mirrored here.
**Review round:** the Prompt 43 HEDS review of `374e642fb901ce21e1b8886fb80addccbfe89add` returned `CORRECTION_REQUIRED` at CRITICAL 0 / HIGH 1 / MEDIUM 2. What follows answers findings `H-43-01`, `M-43-02` and `M-43-03`; the findings, their dispositions and the proofs behind each are in `## Prompt 44 correction round`.

> **What this bundle is.** A record of what the repository now contains and of what was proven on the local host. It embeds **no** hosted receipt, and no sentence here is evidence that any credential, GitHub environment, protection rule, certificate or notarization account exists. Where a claim depends on that external state it is placed in `## Claims requiring external exact-head evidence` and left `UNKNOWN`.

## Source-materialized claims

These describe the repository as it exists and do not change as evidence advances:

- `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md` defines `hive-release-provenance-v1`: four guarantees held apart (artifact integrity, build provenance, publisher authenticity, platform trust) plus publication, each with its own closed ladder and its own admission rule; the transition law; the channel-coherence law; canonical serialization; and the environment-protection admission law.
- `tools/desktop/release_provenance.py` (1050 lines) is the validator: standard-library only, offline, non-mutating, one exception class, closed ordered key tuples, and modes `--build`, `--verify`, `--gate`, `--transition`, `--channel-gate`, `--environment-protection`, `--attest-subjects`. The last mode is read-only and mints nothing: it decodes the subject set out of an attestation bundle's own DSSE payload and compares it as a set against the package identities the inventory entails. It is an admission authority, not a claim-minting authority: `--build` hardcodes the credential-free baseline and exposes no flag capable of producing a signing, notarization, attestation or publication claim.
- `.github/workflows/protected-release.yml` (1493 lines) materializes eight jobs in a fixed order — `preflight`, `probe-release-protection`, `build-attest-windows`, `build-attest-linux`, `build-attest-macos`, `sign-windows`, `sign-and-notarize-macos`, `publish` — with workflow-level `permissions: contents: read`, all 23 action references pinned to full commit SHAs, and no `pull_request_target` and no `workflow_run` trigger. `id-token: write` is held by the three attestation jobs and by nothing else; the credential-bearing signing jobs hold no write permission of any kind and contain no expression able to resolve a secret slot.
- `tests/desktop/test_release_provenance.py` (1796 lines, 16 classes) and `tests/desktop/test_protected_release_workflow.py` (1091 lines, 9 classes) are materialized adversarial lanes; the second is a stdlib text-and-AST audit of the workflow file and needs no runner, no network and no credential.
- The CP-0025 substrate is consumed, not redefined: a provenance document binds to the real inventory through the SHA-256 of `serialize_inventory`'s canonical bytes, so tampering with upstream packaging evidence changes the binding rather than being papered over.
- What an attestation is about is derived, not discovered. `attestation_subjects()` reads names and digests only out of the validated `hive-package-inventory-v1` document — never a filesystem walk, a glob or the manifest file standing in for the packages it describes — and `render_attestation_checksums()` emits them in the `<digest>  <name>` grammar `actions/attest` takes as `subject-checksums`, which preserves a name verbatim where `subject-path` would collapse it to a basename. A directory bundle therefore keeps its own identity: `Hive Coder.app` is attested under `identity=sorted-tree`, a flat package under `identity=file-bytes`, and an inventory that claims one kind where the other is entailed is refused.
- The ledger carries a `DEC-030` entry marked PROPOSED / NOT CANONICAL (authorized by Context Lock Delta 001, pure append), and the `DEC-030` ADR points at that ledger entry in both directions so neither can be mistaken for promotion.
- `AGENTS.md` and `docs/project-brain/07-DEPLOYMENT.md` carry the bounded source-truth corrections the Context Lock allows: `AGENTS.md` no longer states `HCODER-CP-0022` as current execution state, and `07-DEPLOYMENT.md` no longer states packaging as merely `PLANNED`. Both defer to `11-CHECKPOINT.md` as the authority.

## Verification executed locally

| What | Exact command | Result |
| --- | --- | --- |
| Provenance contract lane | `python -m unittest tests.desktop.test_release_provenance` | `Ran 159 tests … OK` |
| Workflow structural lane | `python -m unittest tests.desktop.test_protected_release_workflow` | `Ran 45 tests … OK` |
| Both lanes together | `python -m unittest tests.desktop.test_release_provenance tests.desktop.test_protected_release_workflow` | `Ran 204 tests … OK` |
| Full discovered suite, final candidate content | `PYTHONWARNINGS=error::ResourceWarning python -m unittest discover -s tests -p "test_*.py"` | `Ran 809 tests … OK (skipped=58)` |
| Same suite at the canonical base `1a56224` | identical command | `Ran 605 tests … OK (skipped=58)` |
| Workflow step bodies executed verbatim, outside any runner | `python …/subject_lane.py …/run4` (driver kept outside the repository, Git Bash pinned explicitly) | `ALL SUBJECT-LANE CHECKS PASSED` |
| Desktop security gate, shadow run over the tracked file set only | `python …/shadow_gate.py` (driver outside the repository; `security_gate.py` unmodified) | `DESKTOP_SECURITY_GATE=PASS` |

The delta is exactly `+204`, which is this Work Order's two lanes, with no pre-existing test altered, skipped or deleted; the 58 skips are the base's own and are unchanged.

Every row above was re-run on the shipped candidate content after the last edit to it, not carried forward from an earlier round. The Prompt 43 counts for the same two lanes were 132 and 42, so the correction round added 27 provenance cases and 3 workflow cases and removed none.

## Non-vacuity proofs

A green adversarial suite is worth nothing if the guard it tests cannot fail. Three independent mutation campaigns were run, all driven from scripts kept **outside** the repository (no Context Lock delta authorizes a new in-lane path), and each verified afterwards that the mutated file had been restored byte-identically — the scripts assert it themselves (`RESTORED_OK True`) and the assertion was re-checked independently with `sha256sum -c`. Campaigns A and B describe the Prompt 43 structure; Campaign A was re-run on the shipped source after the correction round and Campaign C covers the guards the correction added.

### Campaign A — validator guard neutralization

Method: every `if` / `elif` condition in `tools/desktop/release_provenance.py` is replaced, one at a time, with a constant-false condition, and the provenance lane is re-run. A guard whose removal leaves the suite green proves nothing.

- First campaign: **119 candidates, 115 killed, 4 survivors.**
- Three of the four survivors were real gaps — a guard with no test behind it, not a wrong guard — and are closed on this head by a test plus one truthfulness fix:

| Line | Neutralized guard | Disposition |
| --- | --- | --- |
| 345 | `elif asset_set:` — a `staged` publication pinning an artifact set it has not released | closed by `test_staged_publication_may_not_pin_an_artifact_set_it_has_not_released` |
| 595 | `not isinstance(record, dict)` — a non-object environment record read as an empty, passing gate | closed by `test_a_record_that_is_not_an_object_is_the_wrong_shape_not_an_empty_gate` |
| 766 | `report.status != "LOCKED"` — a drifting or versionless source admitted to a channel | closed by `test_a_drifting_or_versionless_source_is_never_admitted_to_a_channel` and `test_a_locked_source_that_names_no_version_is_incoherent_too`, and by splitting the combined drift/no-version condition so each refusal prints its own true reason instead of one message covering two different failures |
| 831 | `if __name__ == "__main__":` | **accepted survivor** — a module-entry condition that carries no admission decision. Recorded rather than silenced or excluded from the count |

- Final campaign on the shipped source, at the corrected 1050-line validator: **151 candidates, 149 killed, 2 survivors.** Both survivors are recorded rather than silenced or excluded from the count, and neither carries an admission decision any input can reach:

| Line | Neutralized guard | Disposition |
| --- | --- | --- |
| 1049 | `if __name__ == "__main__":` | **accepted survivor** — a module-entry condition. The lane calls `main(argv)` directly, so constant-falsing it changes nothing a test can observe |
| 318 | `if not separator or algorithm != SUBJECT_DIGEST_ALGORITHM:` in `render_attestation_checksums` | **accepted survivor** — the value it re-checks is the `f"{SUBJECT_DIGEST_ALGORITHM}:{digest}"` the same function assembles a few lines above, after `attestation_subjects` has already refused a foreign algorithm and a non-hex digest. It is defense in depth at the point where the checksums grammar is written, and no input reaches its false branch. It was **not** deleted to make the campaign look clean and **not** papered over with a mock that would test the mock rather than the tool |

### Campaign B — workflow structural mutation

Method: throwaway degradations of `.github/workflows/protected-release.yml` — removed `if:` guards, widened permissions, an unauthenticated job reaching a credential stage, a dropped `--verify` step, a `--gate` reordered before `--verify`, an unpinned action, a weakened barrier — each expected to be caught by the workflow audit lane. Run against the Prompt 43 workflow; the stages the correction round rewrote are re-mutated in Campaign C below.

- **28 mutants: 26 killed.** The two survivors are deliberate controls that must survive because they change no structure: `control-comment-only` (comment text edited only) and `control-reworded-prose`.
- Two mutants exposed **defects in the audit itself**, and both were fixed by making the audit stronger, never by relaxing an assertion:
  1. Keyword-based step detection let a comment line plus an echoed `ATTESTATION_VERIFICATION=PASSED` satisfy an attestation guard. The lane now reads commands (`command_lines`, `step_with_command`, `validator_invocations` with line-continuation joining) instead of scanning prose for words.
  2. A comment merely *naming* `--environment-protection` satisfied a mode guard. Every mode guard now reads resolved invocations only, so the flag must actually appear in a command.
- A third fix was in the workflow's own text: the install/execute prohibition is now stated in the verb forms the audit checks (`msiexec`, `Start-Process`, `dpkg -i`, `rpm -i`, `snap install`, `install hive`, `hdiutil attach`, `open -a`, `systemctl`, updater plugin) rather than the noun `installer`, which appears in preserved CP-0025 law about structural, non-installing validation and so could not be banned.

## Prompt 44 correction round

The Prompt 43 head was reviewed and returned `CORRECTION_REQUIRED`. This section records what each finding was, what the repository now says instead, and what was run to prove the replacement is not merely different but stronger. Scope came from the Context Lock's third delta and no other source; its allowed-path list is what bounds this round.

### What left the round untouched

`git status` on the candidate reports **12 modified paths and zero added paths**. The delta's refusals were honored literally, and each was checked rather than assumed:

| Path | Status | How that was established |
| --- | --- | --- |
| `docs/project-brain/10-DECISIONS-LEDGER.md` | byte-identical | Grepped for any assertion the findings would falsify; none exists, so the delta's claim that no finding requires an edit there holds |
| `AGENTS.md`, `docs/project-brain/07-DEPLOYMENT.md` | byte-identical | same test — the Prompt 43 corrections to these files remain accurate under the new subject model |
| `docs/project-brain/11-CHECKPOINT.md` | byte-identical | forbidden: no checkpoint delta may exist while the Work Order is unreviewed |
| `tools/desktop/package_inventory.py` | byte-identical | the subject set is *derived* from its output through `serialize_inventory`, not by editing it |
| `.github/workflows/governance.yml`, `desktop-shell.yml`, `native-package-matrix.yml` | byte-identical | no finding touches them |
| `apps/desktop/**`, manifests, lockfiles | byte-identical | out of scope by construction |
| `tauri.conf.json` | byte-identical, `bundle.active = false` | re-read at the end of the round |

### H-43-01 — a signing stage that could have read a secret

**Finding.** `sign-windows` and `sign-and-notarize-macos` bound `${{ secrets.AZURE_… }}` and `${{ secrets.APPLE_… }}` into step environments and then tested presence with `printenv`. Because no credential exists today the read yielded nothing, so the lane was honest *now*; the structure was not. The moment someone provisioned a slot, that stage would resolve a real signing credential into a runner environment, and the `VALUES_READ=NO` line it printed would become false without any edit to the workflow.

**Correction.** The credential-bearing stages now contain no expression, no `env:` binding and no presence test that could resolve a slot. Each requirement is declared as literal text — `echo "SLOT_REQUIRED=AZURE_ARTIFACT_SIGNING_ENDPOINT"` and its siblings — so the stage reports what provisioning would require while being structurally incapable of resolving it. `VALUES_RESOLVED=NOTHING VALUES_READ=NO VALUES_PRINTED=NO VALUES_PERSISTED=NO` is therefore true *after* provisioning, not only before it. Job permissions stay at `contents: read`; `id-token: write` is held by the three attestation jobs and by nothing else, and a signing job that will eventually need it does not have it.

**Proof.** The audit lane gained `test_a_signing_stage_executes_only_the_whitelisted_verifier_and_literals`, which is a whitelist rather than a blocklist: it walks every step body of both signing jobs and refuses any statement that is not the pinned verifier invocation or a literal `echo`. Five reintroduction mutants and one scope mutant were built against the shipped workflow and all six were killed:

| Mutant | Killed by |
| --- | --- |
| `signing-job-binds-a-secret-again` (`env: KEY: ${{ secrets.AZURE_ARTIFACT_SIGNING_KEY }}`) | `test_a_signing_stage_executes_only_the_whitelisted_verifier_and_literals` |
| `signing-job-probes-a-value-again` (`printenv \| grep -c APPLE_`) | same |
| `signing-job-logs-in-to-the-cloud` (`az login --federated-token …`) | same |
| `signing-job-imports-a-certificate` (`Import-PfxCertificate …`) | same |
| `signing-job-runs-a-signer` (`signtool sign /fd SHA256 …`) | same |
| `signing-job-gains-id-token` | `test_release_identity_permissions_reach_only_the_attestation_jobs` |

A blocklist of vendor command names would have survived a signer invoked any other way; the whitelist does not.

### M-43-02 — the attestation attested the manifest, not the packages

**Finding.** Each `build-attest-*` job passed `subject-path: hive-package-inventory.json`, so the emitted statement had exactly one subject — a JSON document — and the assertion guarding it, `ATTESTATION_SUBJECT_IS_NOT_CANONICAL_INVENTORY_BYTES`, only proved the design was that way on purpose. A green lane then attested *the manifest*, which is evidence about a manifest and not about the released packages. Worse, `gh attestation verify` matches one supplied artifact against the statement by digest alone and reports nothing about the remaining subjects, so even a statement covering one package out of six would verify.

**Correction.** Subjects are now derived from the validated inventory document and rendered through `subject-checksums`, which preserves a name verbatim where `subject-path` would collapse it to a basename and drop directories. Each lane attests exactly its own platform's package identities — Windows `msi/…` + `nsis/…`, Linux `appimage/…` + `deb/…`, macOS `Hive Coder.app` + `dmg/…` — with the directory bundle carrying its `sorted-tree` identity instead of impersonating a file. After `gh attestation verify` succeeds, a second step runs `--attest-subjects` and requires the decoded statement's subject set to equal the inventory's package set exactly. The manifest file is never a subject. The refusal surface is closed: no `BLOCKED_ATTESTATION_SUBJECT_MODEL` stop was needed, because the macOS `.app` *is* truthfully representable.

**Proof, three independent ways.**

1. **Unit lane** — two new classes carrying 24 of the 27 cases this round added to the lane: `AttestationSubjectTests` (10) for generation — name safety, digest algorithm and shape, identity-kind honesty in both misdeclaration directions, the 1024-subject ceiling at generation time, order determinism, the exact `subject-checksums` grammar round-tripping back to the same subjects — and `AttestationSubjectEvidenceTests` (14) for reading a bundle back: missing, extra, foreign-name, duplicate-name, empty statement, non-in-toto, non-provenance predicate, un-decodable envelope, strict base64, an oversized observed set, and the manifest standing in for the packages. The remaining three are the two `--attest-subjects` CLI cases and the offline-scan falsification case described below.
2. **Workflow audit** — `test_the_attested_subjects_are_the_packages_not_the_manifest`, `test_the_attested_subject_set_is_proved_equal_to_the_package_set`, `test_the_subjects_are_derived_from_inventory_and_never_discovered`, each carrying its own in-test synthetic mutation. Four workflow mutants were killed: pointing the input back at `subject-path`, pointing `subject-checksums` at the manifest, replacing the proof step with an `echo`, and aiming `gh attestation verify` at the manifest.
3. **Executed lane** — the actual step bodies were extracted from `protected-release.yml` and run verbatim as shell scripts against real inventories built from real bytes on disk, outside any runner. Receipts:

```
ATTESTATION_SUBJECT_COUNT=2
ATTESTATION_SUBJECT=Hive Coder.app identity=sorted-tree
ATTESTATION_SUBJECT=dmg/Hive Coder_0.1.0_aarch64.dmg identity=file-bytes
ATTESTATION_SUBJECT_SET=MATCHES_PACKAGES
ATTESTATION_SUBJECT_BOUND=msi/Hive Coder_0.1.0_x64_en-US.msi identity=file-bytes
=== proof over a one-package bundle: exit=2 ===
REASON=attestation subject set is not this release's package set: missing ['nsis/Hive Coder_0.1.0_x64-setup.exe'] …
=== proof over a neighbour's package: exit=2 ===
REASON=… missing ['msi/Hive Coder_0.1.0_x64_en-US.msi']; unexpected ['msi/other.msi'] …
=== proof over a non-provenance predicate: exit=2 ===
REASON=attestation predicate is not build provenance this contract can read: 'https://example.com/opinion/v1'
ALL SUBJECT-LANE CHECKS PASSED
```

The harness also asserted, independently of the tool, that every digest in the rendered checksums file equals the SHA-256 of the bytes on disk — otherwise `gh attestation verify` would be hashing something other than the released package — and that the derived `ATTESTATION_VERIFY_TARGET` is a real package path, not the manifest.

### M-43-03 — the external handoff understated what provisioning requires

**Finding.** Documentation-only. The handoff named an Apple "Team ID" where notarization through an App Store Connect API key needs an issuer UUID, listed Tauri variables the installed version does not read, compressed the Azure Artifact Signing chain into a single slot name, and did not say that the signing executor a later slice writes will need `id-token: write` that this slice deliberately withholds.

**Correction, and where each piece lives.** The executor brief's provisioning table now separates secret-class slots from configuration identities: Azure needs `AZURE_ARTIFACT_SIGNING_ENDPOINT` / `AZURE_ARTIFACT_SIGNING_ACCOUNT` / `AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE` plus `ENTRA_APPLICATION_CLIENT_ID`, `ENTRA_DIRECTORY_TENANT_ID`, `ARTIFACT_SIGNING_SUBSCRIPTION_ID`, the federated-credential subject and a role assignment to **Artifact Signing Certificate Profile Signer** at certificate-profile scope, a region-aligned endpoint and an RFC 3161 timestamp authority; Apple needs `APPLE_SIGNING_IDENTITY`, `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD` for signing and `APPLE_API_KEY` (Key ID) / `APPLE_API_ISSUER` (issuer UUID) / `APPLE_API_KEY_PATH` (the `.p8`) for API-key notarization — with `APPLE_TEAM_ID` listed explicitly as **not** required and the reason given, because it authenticates the Apple-ID mode and is not an issuer. The `id-token: write` deferral is stated in the Work Order's Requirement 6, in `DEC-030` law 7 and its non-decision clause, in the brief's fourth provisioning row, in the acceptance map's W3, and in the implementation pack's law 6. No workflow text was narrowed or widened to make a document claim true: the delta authorizes workflow edits only for the two code findings, and the stage literals stay narrower than the provisioning table on purpose. The table closes with the rule that resolves the apparent mismatch — the workflow text is authoritative for what a stage declares, the table for what provisioning requires, and neither is a request for a value.

### What was removed, and why nothing got weaker

The Context Lock reauthorized the workflow audit lane as a live surface: additions and strengthening only, no method deleted, no expectation relaxed, no skip. The diff carries **one** `-def test_` line, so the accounting is small and checkable:

| Removed | Disposition |
| --- | --- |
| `test_the_attested_subject_is_the_bound_inventory_bytes` | replaced by the three M-43-02 tests named above; its subject assertion, `ATTESTATION_SUBJECT_IS_NOT_CANONICAL_INVENTORY_BYTES`, guarded a workflow line the correction deleted, so the assertion is obsolete rather than dropped — the new invariant is stronger: the manifest may not be a subject *and* the package set must be proved equal |
| `self.assertIn("subject-path:", …)` | inverted to `assertNotIn`, so the weaker input form is now forbidden rather than required |
| `self.assertIn("canonical_bytes", …)` | preserved verbatim inside the replacement test |
| three slot-name blocklist assertions (`echo "$APPLE…`, `echo "$AZURE…`, a regex banning any echoed `…CERTIFICATE`) | subsumed by the whitelist test, which refuses every non-whitelisted statement rather than three named shapes |
| the old `printenv`-probe assertions and their `SLOT_ABSENT` step index | the probe they required no longer exists; requiring its absence is the whole point of H-43-01 |
| local `run_bodies`-stitching loops inside two test bodies | relocated, not deleted: `run_bodies` remains defined and used 20 times, and `command_lines` / `step_texts` / `step_with_command` now serve more tests than before |

In the provenance lane, `test_module_imports_no_network_credential_or_execution_surface` became `test_module_reaches_no_network_credential_or_execution_surface` and gained a sibling, `test_the_surface_scan_reports_a_module_that_does_reach_one`, which falsifies the scanner itself by feeding it a module that does reach a forbidden surface. That sibling exists because an unsatisfiable scan is indistinguishable from a passing one.

### Campaign C — targeted mutation of the guards this round added

Campaign A and Campaign B both ran against Prompt 43's structure. The new guards needed their own campaign, built the same way: exact-span substitution in the shipped source, focused lane re-run, byte-exact restore verified by digest.

- **27 mutants: 17 validator, 10 workflow. 0 survivors.** Every mutant is named in the tables above or maps to a named case in `AttestationSubjectTests` / `AttestationSubjectEvidenceTests`.
- Two survivors appeared in the first sweep of this campaign and were **genuine audit gaps**, not wrong guards. `observed-count-ceiling-removed` survived because no case fed an oversized *observed* set, and `payload-base64-strictness-lost` survived because no case fed a payload that a lenient decoder would repair instead of refusing. Both were closed by adding the missing cases — `test_an_observed_set_too_large_for_anyone_to_verify_is_refused_before_comparing` and `test_the_payload_is_decoded_strictly_rather_than_repaired` — never by weakening a guard, after which the sweep reports zero survivors.
- Two earlier anchor mistakes in the campaign were fixed before any result was read, because a mutant whose anchor is absent proves nothing either way: the real payload line is `base64.b64decode(payload, validate=True)`, and the real attest input is `subject-checksums: ${{ runner.temp }}/hive-attestation-subjects.txt`. A third mutant, "delete the whole proof step", was replaced by `subject-set-proof-replaced-by-an-echo` after the first form was seen to fail an unrelated structural assertion instead of the one it claimed to test.
- After the sweep, `sha256sum -c` reports both mutated files restored byte-identically.

### A sweep that lied, and how it was caught

Two sweeps were launched concurrently by mistake — a re-run of Campaign A while its first run was still walking the file. Each one captures its baseline at start, so the second captured a baseline that was **already a mutant**, and its final `RESTORED_OK True` was true only against that corrupted snapshot. The result it reported — every candidate killed, no survivors at all, including a module-entry condition that no test can reach — was arithmetically clean and completely false, and the tell was exactly that: a campaign in which nothing survives has stopped testing the guards and started testing its own file writes.

Detection and repair, in order:

1. The independent cross-check was the one this bundle already claims: `sha256sum -c` against a snapshot taken **before any sweep in this round touched the source**. It reported `tools/desktop/release_provenance.py: FAILED` while the script itself asserted `RESTORED_OK True`. The script's assertion was self-referential; the external snapshot was not.
2. The residue was located as a single `if False:` at line 391 of `verify_attestation_subjects`, and it was not inert: the provenance lane then failed with `KeyError: 'sha256'` on a subject carrying a `sha512` digest, where the guard should have raised `ProvenanceError` — a neutralized digest-algorithm guard sitting on the shipped path.
3. The condition was restored from the round's own edit record, and the file was re-verified **byte-identical to the pre-sweep snapshot** (`sha256sum -c` → `OK` for both the validator and the workflow). `Ran 159 tests … OK` and `Ran 809 tests … OK (skipped=58)` were then re-earned on the repaired content.
4. The sweep driver now refuses to start unless the file it is about to mutate hashes to the shipped digest, so this failure mode cannot recur silently: a baseline it cannot name is a baseline it will not sweep.

Every Campaign A figure quoted in this bundle comes from a run that passed that guard.

### Host divergences recorded, not patched away



Three things on this host did not behave as the evidence would like. Each is stated with its evidence and its classification, and none was silenced by editing a tool or a test.

1. **`tools/desktop/security_gate.py` raises `UnicodeDecodeError` (byte `0xe4` at offset 4) on this host.** Classification: **environment noise, not a defect in this Work Order.** The file is one of 2029 scanned and is `apps/desktop/src-tauri/target/release/build/hive-coder-desktop-*/out/tauri-codegen-assets/97ff…css` — untracked, git-ignored local build output that is not valid UTF-8. A CI checkout has no `target/`, so hosted `Desktop Shell` never sees it. `security_gate.py` is not a path this delta authorizes, so it was not modified, and the user's build artifacts were not deleted. A shadow run over the tracked file set only reported `DESKTOP_SECURITY_GATE=PASS` with `FILESYSTEM_MUTATION_PRIMITIVES=0`, `GENERIC_PROCESS_EXECUTION=0`, `FIXED_RUNTIME_SIDECAR_PROCESS=1`, `LOCKFILES=COMMITTED`, over `tracked=414` files with `gate-scanned-in-CI=35`.
2. **An earlier claim in this round was wrong and is corrected here.** A lane failure was first attributed to "Git Bash discards a custom `env=` block". A direct probe disproved it: the `bash` that resolves from the process default is `C:\Windows\System32\bash.exe` — WSL interop — which cannot see a `C:/…` path and does not inherit the variables, while `C:\Program Files\Git\bin\bash.exe` reports `OS=cygwin` and reads both. Pinning the harness to Git Bash made the lane run end to end. The mis-attribution, not the toolchain, was the bug.
3. **HIVE is unavailable on this host: `no hive binary`, and `SearchKnowledge` reports no generated knowledge for the workspace.** Any statement in this bundle that would rest on a HIVE card is therefore resting on the repository text alone, and the requested HIVE refresh could not be performed. Recorded as an unmet deliverable rather than simulated.

### Receipts the new head invalidates

`374e642fb901ce21e1b8886fb80addccbfe89add` was the Prompt 43 candidate. Every hosted check-run recorded against it — the four lane receipts cited in the Prompt 43 handoff — is **historical evidence for a superseded head** and is not current evidence for this one. The run identifiers themselves belong to the mutable hosted record and are carried in the PR body and the Issue `#85` handoff, not in this bundle, which by its own rule embeds no hosted receipt. What the bundle states instead is the law: a new head invalidates the old head's receipts, and `Governance`, `Desktop Shell`, `Native Package Matrix` and `Protected Release` must each be green on the exact head that is reviewed.



## Externally gated stages — never executable in this increment

Re-verified on the host at the time of writing, read-only, with no value read or printed: repository **visibility `public`**, **environments total `0`**, **repository Actions secrets total `0`**, **repository variables total `0`**. Consequences, each stated without values:

| Stage | Held back by | Would require |
| --- | --- | --- |
| `preflight` | nothing — designed to run secret-free as exact-head evidence | hosted execution on the candidate head |
| `build-attest-*` | an OIDC token mint and the hosted attestation service, neither of which a local run can reach | `actions/attest` over the `subject-checksums` body rendered from the validated inventory's package identities — one subject per declared package, the macOS `.app` under its sorted-tree identity — with the verification condition that `gh attestation verify` succeeds for a named package under `--signer-repo`, `--signer-workflow`, `--source-ref` and `--deny-self-hosted-runners`, **and** that the decoded statement's subject set equals the inventory's package set exactly. The second condition is not implied by the first: `gh attestation verify` matches a single digest and says nothing about the rest of the set |
| `sign-windows` | no publisher identity of any kind, and no scope able to mint one | Azure Artifact Signing certificate profile reached by a federated Microsoft Entra identity: slots `AZURE_ARTIFACT_SIGNING_ENDPOINT` / `AZURE_ARTIFACT_SIGNING_ACCOUNT` / `AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE`, plus the configuration identities `ENTRA_APPLICATION_CLIENT_ID` / `ENTRA_DIRECTORY_TENANT_ID` / `ARTIFACT_SIGNING_SUBSCRIPTION_ID` / `FEDERATED_CREDENTIAL_SUBJECT_REPO_ENVIRONMENT_IDENTITY` / `CERTIFICATE_PROFILE_SIGNER_ROLE_ASSIGNMENT` (identifiers, not key material), an RFC 3161 timestamp authority, and `id-token: write` on the signing job — which this increment does not grant. Verification condition: each package's signature verifies with an independent authenticode verification whose signer identity matches the recorded certificate subject and fingerprint, with a timestamp inside the certificate's validity window. The `signtool` + PKCS #12 fallback is recorded in `DEC-030` as the weaker option and is not used here |
| `sign-and-notarize-macos` | no signing certificate, no notarization credential | Developer ID Application certificate for `codesign` plus an App Store Connect API key for API-key `notarytool`: slots `APPLE_SIGNING_IDENTITY` / `APPLE_CERTIFICATE` / `APPLE_CERTIFICATE_PASSWORD` for signing and `APPLE_API_KEY` (Key ID) / `APPLE_API_ISSUER` (App Store Connect issuer UUID) / `APPLE_API_KEY_PATH` (path to the `.p8`) for notarization, which are Tauri 2.11's own names. `APPLE_TEAM_ID` is deliberately absent: it authenticates the Apple-ID notarization mode and is not an issuer, so substituting it would produce a submission that cannot be authorized. Verification condition: `codesign --verify --strict --deep` passes and `xcrun notarytool information` reports Acceptance for the submitted artifact |
| `probe-release-protection` | no named environment exists, so no protection semantics exist | GitHub environments `hive-release-signing` and `hive-release-publish`, each with a `required_reviewers` rule carrying at least one reviewer, `prevent_self_review` true and `can_admins_bypass` false, so the probe prints `RELEASE_PROTECTION=PROTECTED` for a real record. An environment name alone is never protection, and GitHub silently creates a named-but-missing environment unprotected rather than failing |
| `publish` | the unimplemented-signing barrier below, plus absent release authority | dispatch with `publish_intended=true`, a probe-verified protected environment, and every gate green |

**The signing barrier is intentional and cannot be satisfied by provisioning alone.** `sign-windows`, `sign-and-notarize-macos` and the publication stage each reach an unconditional refusal step emitting `RELEASE_SUBSTRATE_STOPPED=BLOCKED_EXTERNAL_CREDENTIALS_AND_UNIMPLEMENTED_SIGNING`. This increment builds the admission law for signing, not the signing executor. Supplying credentials would therefore not turn those lanes green, which is the point: a later head that *does* claim signing must add the executor as its own governed change, and a reviewer can see that the refusal was designed rather than discovered.

## Claims requiring external exact-head evidence

Each holds only against a named exact head; that mutable state belongs to the Draft PR and Issues #30 and #85, never here:

- `Governance`, `Desktop Shell` and `Native Package Matrix` remain green and unweakened on the final candidate head. They were not modified, re-triggered or path-filtered by this Work Order.
- The new `Protected Release` lane's `preflight` job is green on that head, including its `--environment-protection` adjudication of a record it fetches unauthenticated, and its refusal when the named environment has no enforced protection.
- The credential-bearing and publication stages are `UNKNOWN` / `BLOCKED` on that head and are never reported as passing.
- An independent HEDS review of that head returns unresolved HIGH/CRITICAL `0/0`, and a governed expected-head merge completes. The executor may not issue, and does not issue, any of these.

## Claims never admitted by this slice

- That any package is signed, notarized, stapled, trusted, published, installable or production-distributable.
- That the `Protected Release` lane is green, or that any release job is protected. No credential, environment, protection rule or notarization account was proven to exist, and `DEC-030` is explicitly not evidence that one does.
- That a build-provenance attestation, an inventory digest or a `REASON=`-printing gate substitutes for publisher authenticity on Windows or macOS. The workflow prints positive `SEPARATION_PROOF=` markers on Windows and macOS precisely because the substitution is the failure mode this slice exists to prevent.
- That this increment created a tag, a GitHub Release, an environment, a secret, a variable, an application, a certificate or an account. It created none, and no such creation was attempted.
- That Linux has an enforceable OS publisher-trust model. `NO_PUBLISHER_TRUST_PLATFORMS` skips the signing and platform-trust requirements there rather than faking them, and that skip is an honest absence, not a pass.
- That `HCODER-CP-0026` exists, that `DEC-030` carries canonical force, or that `HCODER-DIST-001D`-`G` (updater, endpoint, update UI, rollback, install end-to-end) were touched. They were not.

## Known deferrals and design boundaries

- **Attestation identity stays bundle-level; only the subject set became package-level.** The `attestation` block of a provenance document records one verified bundle identity per release — `signerWorkflow`, `sourceRef`, `runId`, `bundleDigest` — not one per artifact, and a reviewer who wants a distinct attestation identity per artifact must still treat that as a contract extension rather than a capability present here. What Prompt 44 changed is what the bundle is *about*: its subjects are now this release's package identities, and `--attest-subjects` refuses a bundle whose subject set is not exactly that set, so a statement signing one package out of six no longer passes as provenance for the release. Package-level publisher trust remains where it was, in `packages[].signing` and `packages[].notarization`.
- **The `signing.identity` triple is structurally validated but not yet populated by any executor**, since no executor exists in this increment. Its immutability law (a certificate identity, once asserted, may not be swapped) is enforced and tested today so the first real signing stage cannot quietly change hands mid-release.
- **`environment-protection` adjudicates a record; it does not fetch one.** Keeping the validator offline and free of any network or token dependency was chosen over convenience: the workflow supplies the record, and the tool decides. The trust that the supplied record is genuine is therefore hosted-lifecycle evidence, and is listed above as such rather than assumed.

## Base-state facts to re-verify

Mutable external state decays. Re-read live before relying on any of these:

- `gh api` for `repos/…/environments`, `…/actions/secrets`, `…/actions/variables` — all zero at the time of writing.
- Repository visibility is `public`, which is the precondition for artifact attestation at no cost.
- Pinned toolchain inherited from CP-0025: `@tauri-apps/cli` 2.11.4, Node 24.21.0, Rust 1.98.1, and the six-target package matrix.
- `apps/desktop/src-tauri/tauri.conf.json` remains byte-unchanged by this Work Order with `bundle.active = false`.

## Promotion evidence template

For each exact technical head record: commit SHA; `Governance`, `Desktop Shell`, `Native Package Matrix` and `Protected Release` run and job IDs; whether `preflight` passed and what it adjudicated for each named environment, with `RELEASE_PROTECTION=` and `UNPROVEN_BECAUSE=` values; the per-lane `SEPARATION_PROOF=` markers actually emitted; HEDS unresolved HIGH/CRITICAL counts; and for any credentialed stage that ran, the credential class and verification condition only — never a value.

## STOP

`UNKNOWN` never becomes `PASS`. Exact-head evidence proves only the exact SHA it names, and a new head invalidates the old head's receipts. Mutable hosted receipts are recorded externally, never in this bundle. If external setup is required, report the credential class, the provider or mechanism, the documented slot name and the exact verification condition — never a value, and never a request for one. A missing secret is never a reason to downgrade to unsigned publication, and no green result obtained by weakening a gate, a guard or a test counts as a result. Canonical standing for this Work Order is determined only by its governed closeout, and this increment neither claims it nor can grant it.
