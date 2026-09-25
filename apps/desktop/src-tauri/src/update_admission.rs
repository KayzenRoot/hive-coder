//! Hive Update Admission Bridge v1 (HCODER-WO-0027 / DEC-031).
//!
//! This module is the trust choke point between the official Tauri updater and
//! the `hive-update-state-v1` law. Two independent gates must both pass before a
//! candidate becomes `ready`:
//!
//! - the cryptographic gate — the updater verified a minisign signature over the
//!   artifact, and the signature's trusted comment carried the version the
//!   endpoint announced;
//! - the policy gate — Hive's own DEC-028 same-channel strictly-newer law.
//!
//! Neither substitutes for the other, and nothing here is selectable by the
//! caller: endpoints, public key, channel, target, comparator and transport
//! flags are read from the trusted build configuration only. There is
//! deliberately no install or restart path in this module.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::sync::Mutex;
use tauri_plugin_updater::Update;

/// Compile-time proof that the pinned updater exposes the two controls this
/// bridge depends on. On `tauri-plugin-updater` 2.11.x neither key exists, and
/// because the upstream `Config` deserializer has no unknown-field rejection,
/// the same `tauri.conf.json` would parse cleanly while the protections it
/// advertises silently did nothing. A dependency downgrade must therefore fail
/// to compile rather than degrade quietly.
const _: fn(&tauri_plugin_updater::Config) -> bool = |config| config.require_signed_version;
const _: fn(&tauri_plugin_updater::Config) -> bool = |config| config.allow_downgrades;

/// Identity of the internal admission receipt (DEC-031 section 7).
pub const ADMISSION_RECEIPT_CONTRACT: &str = "hive-update-admission-v1";

/// The single authenticity scheme this build admits, and the only value that can
/// ever make a snapshot reach `ready`.
pub const ADMITTED_SCHEME: &str = "tauri-minisign-signed-version-v1";

const UPDATE_STATE_CONTRACT: &str = "hive-update-state-v1";

/// Key of this plugin's node inside `tauri.conf.json -> plugins`.
const PLUGIN_NAME: &str = "updater";

pub const CHANNEL_STABLE: &str = "stable";
pub const CHANNEL_BETA: &str = "beta";
pub const CHANNEL_DEV: &str = "dev";

/// Mirrors `MAX_VERSION_CHARS` in the canonical version contract.
pub const MAX_VERSION_CHARS: usize = 128;

/// Mirrors `MAX_CORE_IDENTIFIER`: the narrowest declared consumer of the
/// canonical version is npm, so a core identifier above this is refused even
/// though Cargo's own range is wider.
const MAX_CORE_IDENTIFIER: u64 = 9_007_199_254_740_991;

const MAX_DETAIL_CHARS: usize = 160;

// ---------------------------------------------------------------------------
// Bounded refusals
// ---------------------------------------------------------------------------

/// A refusal drawn from the closed `UPDATE_ERROR_CODES` vocabulary, with a
/// detail that satisfies the contract's redaction charset. Details never carry
/// an endpoint, key, hash, response body or credential.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Denial {
    pub code: &'static str,
    pub detail: &'static str,
}

impl Denial {
    const fn new(code: &'static str, detail: &'static str) -> Self {
        debug_assert!(detail.len() <= MAX_DETAIL_CHARS);
        Self { code, detail }
    }
}

/// Whether a refusal means the service cannot be used at all (`unavailable`) or
/// that an attempted admission was rejected (`failure`). Missing trust data is
/// the former; a bad candidate is the latter.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Refusal {
    Unavailable(Denial),
    Failed(Denial),
}

const TRUST_NOT_CONFIGURED: Denial = Denial::new(
    "service_unavailable",
    "the updater has no trusted public key and endpoint configured",
);

const SIGNED_VERSION_NOT_REQUIRED: Denial = Denial::new(
    "service_unavailable",
    "the updater configuration does not require a signed release version",
);

const DOWNGRADES_ALLOWED: Denial = Denial::new(
    "service_unavailable",
    "the updater configuration allows a non-newer release",
);

const UNSAFE_TRANSPORT: Denial = Denial::new(
    "service_unavailable",
    "the updater configuration allows an unsafe transport or tls verification bypass",
);

const UNSAFE_ENDPOINT: Denial = Denial::new(
    "service_unavailable",
    "a configured updater endpoint is not a trusted https origin",
);

const MALFORMED_CONFIG: Denial = Denial::new(
    "service_unavailable",
    "the updater configuration is malformed or carries unrecognised settings",
);

const UNKNOWN_CHANNEL: Denial = Denial::new(
    "unknown_channel",
    "the installed version does not belong to a recognised release channel",
);

const CANDIDATE_ALREADY_ADMITTED: Denial = Denial::new(
    "candidate_already_admitted",
    "an update candidate is already held and cannot be silently replaced",
);

const NO_ADMITTED_CANDIDATE: Denial = Denial::new(
    "no_admitted_candidate",
    "no checked update candidate is held by this build",
);

/// The two refusals whose entire subject is which candidate owns the slot.
///
/// They are the only codes a slot that already owns a candidate may swallow:
/// neither is evidence that the held candidate, or the bytes verified for it,
/// became invalid. Every other refusal reports something that actually went
/// wrong, and has to be recorded.
fn is_slot_occupancy_refusal(refusal: &Refusal) -> bool {
    let code = match refusal {
        Refusal::Unavailable(_) => return false,
        Refusal::Failed(denial) => denial.code,
    };
    code == CANDIDATE_ALREADY_ADMITTED.code || code == NO_ADMITTED_CANDIDATE.code
}

/// A failed update check does not own the candidate slot. Its failure can be
/// reported when the slot is empty, but cannot invalidate work another operation
/// already admitted or started downloading.
fn is_non_owning_check_failure(refusal: &Refusal) -> bool {
    matches!(refusal, Refusal::Failed(denial) if denial.code == SERVICE_UNREACHABLE.code)
}

const PLATFORM_UNSUPPORTED: Denial = Denial::new(
    "service_unavailable",
    "this build cannot determine the updater platform identity",
);

const PLATFORM_MISMATCH: Denial = Denial::new(
    "channel_not_eligible",
    "the announced candidate is not for this platform",
);

const SERVICE_UNREACHABLE: Denial = Denial::new(
    "service_unavailable",
    "the updater could not obtain a release manifest from a trusted endpoint",
);

const VERIFICATION_FAILED: Denial = Denial::new(
    "verification_failed",
    "the candidate signature or signed release version did not verify",
);

const DOWNLOAD_FAILED: Denial = Denial::new(
    "download_failed",
    "the admitted candidate could not be downloaded",
);

const IDENTITY_MISMATCH: Denial = Denial::new(
    "service_unavailable",
    "the updater checked a release against a version this build does not run",
);

const STATE_UNAVAILABLE: Denial = Denial::new(
    "service_unavailable",
    "trusted update state is unavailable",
);

// ---------------------------------------------------------------------------
// Version and channel law (mirrors contracts/version.ts + releaseChannel.ts)
// ---------------------------------------------------------------------------

/// Strict acceptance of a canonical Hive version. Anything `semver` rejects, or
/// that exceeds the declared profile bounds, is refused rather than coerced.
pub fn admit_version(raw: &str) -> Option<semver::Version> {
    if raw.is_empty() || raw.len() > MAX_VERSION_CHARS {
        return None;
    }
    let version = semver::Version::parse(raw).ok()?;
    if version.major > MAX_CORE_IDENTIFIER
        || version.minor > MAX_CORE_IDENTIFIER
        || version.patch > MAX_CORE_IDENTIFIER
    {
        return None;
    }
    Some(version)
}

/// Channel is derived from the version shape, never configured alongside it:
/// one version identifies exactly one channel, so the pair cannot drift.
pub fn channel_of(version: &semver::Version) -> Option<&'static str> {
    if version.pre.is_empty() {
        return Some(CHANNEL_STABLE);
    }
    match version.pre.as_str().split('.').next() {
        Some("beta") => Some(CHANNEL_BETA),
        Some("dev") => Some(CHANNEL_DEV),
        _ => None,
    }
}

/// DEC-028 eligibility law: same channel, strictly newer, nothing else.
pub fn evaluate_eligibility(
    current: &semver::Version,
    current_channel: &str,
    candidate_raw: &str,
) -> Result<semver::Version, Refusal> {
    let candidate = admit_version(candidate_raw)
        .ok_or(Refusal::Failed(Denial::new(
            "malformed_version",
            "the announced candidate version is not a canonical hive version",
        )))?;
    let candidate_channel = channel_of(&candidate).ok_or(Refusal::Failed(Denial::new(
        "cross_channel_not_permitted",
        "the announced candidate does not belong to a recognised release channel",
    )))?;
    if candidate_channel != current_channel {
        return Err(Refusal::Failed(Denial::new(
            "cross_channel_not_permitted",
            "the announced candidate belongs to a different release channel",
        )));
    }
    match candidate.cmp(current) {
        std::cmp::Ordering::Greater => Ok(candidate),
        std::cmp::Ordering::Less => Err(Refusal::Failed(Denial::new(
            "downgrade_not_permitted",
            "the announced candidate is older than the installed version",
        ))),
        std::cmp::Ordering::Equal => Err(Refusal::Failed(Denial::new(
            "channel_not_eligible",
            "the announced candidate is the version already installed",
        ))),
    }
}

// ---------------------------------------------------------------------------
// Trusted configuration capsule
// ---------------------------------------------------------------------------

/// The exact admissible key set of `tauri.conf.json -> plugins.updater`.
///
/// Hive re-reads the node itself because upstream ignores keys it does not
/// model: an absent, extra or misspelled control must be a refusal here, not a
/// default that happens to look safe.
#[derive(Debug, Clone, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct UpdaterTrustProbe {
    pub pubkey: String,
    pub endpoints: Vec<String>,
    pub require_signed_version: bool,
    pub allow_downgrades: bool,
    pub dangerous_insecure_transport_protocol: bool,
    pub dangerous_accept_invalid_certs: bool,
    pub dangerous_accept_invalid_hostnames: bool,
}

/// Non-secret trusted configuration admitted for one check cycle.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UpdateTrustConfig {
    pub channel: &'static str,
    pub current_version: String,
    pub endpoints: Vec<String>,
    /// Identity of the verification key, never its content.
    pub public_key_fingerprint: String,
}

/// Read the trusted `plugins.updater` node out of this build's own configuration.
///
/// Hive parses its own strict shape instead of reusing the plugin's `Config`
/// because upstream's deserializer has no unknown-field rejection and defaults
/// every control but `pubkey`. A missing, misspelled or unrecognised setting
/// must be a refusal here, never a default that happens to look safe.
pub fn probe_from_config(config: &tauri::Config) -> Result<UpdaterTrustProbe, Refusal> {
    let Some(value) = config.plugins.0.get(PLUGIN_NAME) else {
        return Err(Refusal::Unavailable(MALFORMED_CONFIG));
    };
    serde_json::from_value(value.clone()).map_err(|_| Refusal::Unavailable(MALFORMED_CONFIG))
}

/// HTTPS-only, origin-shaped endpoint test. Upstream parses these as URLs and
/// validates the scheme too; this is the second, explicit gate that keeps an
/// authority the build cannot trust out of the request path.
fn is_trust_https_endpoint(raw: &str) -> bool {
    let Some(authority) = raw.strip_prefix("https://") else {
        return false;
    };
    if authority.is_empty() || authority.contains(char::is_whitespace) || authority.contains('@') {
        return false;
    }
    let host = authority
        .split(['/', '?', '#'])
        .next()
        .unwrap_or_default();
    let host = match host.rsplit_once('@') {
        Some((_, after)) => after,
        None => host,
    };
    let host = host.split(':').next().unwrap_or_default();
    !host.is_empty()
}

pub fn resolve_trust(
    probe: &UpdaterTrustProbe,
    current_version: &str,
) -> Result<UpdateTrustConfig, Refusal> {
    if !probe.require_signed_version {
        return Err(Refusal::Unavailable(SIGNED_VERSION_NOT_REQUIRED));
    }
    if probe.allow_downgrades {
        return Err(Refusal::Unavailable(DOWNGRADES_ALLOWED));
    }
    if probe.dangerous_insecure_transport_protocol
        || probe.dangerous_accept_invalid_certs
        || probe.dangerous_accept_invalid_hostnames
    {
        return Err(Refusal::Unavailable(UNSAFE_TRANSPORT));
    }
    let version = admit_version(current_version)
        .ok_or(Refusal::Unavailable(MALFORMED_CONFIG))?;
    let channel = channel_of(&version).ok_or(Refusal::Unavailable(UNKNOWN_CHANNEL))?;
    // Empty trust data is the already-approved missing-trust-root state, not a
    // placeholder that can be used. Nothing may reach the network past this.
    if probe.pubkey.trim().is_empty() {
        return Err(Refusal::Unavailable(TRUST_NOT_CONFIGURED));
    }
    if probe.endpoints.is_empty() {
        return Err(Refusal::Unavailable(TRUST_NOT_CONFIGURED));
    }
    if !probe.endpoints.iter().all(|endpoint| is_trust_https_endpoint(endpoint)) {
        return Err(Refusal::Unavailable(UNSAFE_ENDPOINT));
    }
    Ok(UpdateTrustConfig {
        channel,
        current_version: current_version.to_owned(),
        endpoints: probe.endpoints.clone(),
        public_key_fingerprint: hex_sha256(probe.pubkey.as_bytes()),
    })
}

/// The complete admission law for one announced candidate: trusted config,
/// installed identity, channel/version eligibility and platform, evaluated with
/// no state and no network.
///
/// Everything a caller could otherwise steer is an explicit argument here, which
/// is what makes the law testable end to end without a live release endpoint.
pub fn evaluate_admission(
    probe: &UpdaterTrustProbe,
    announced: &AnnouncedCandidate,
    current_version: &str,
) -> Result<AdmittedCandidate, Refusal> {
    let trust = resolve_trust(probe, current_version)?;
    let current = admit_version(&trust.current_version).ok_or(Refusal::Unavailable(MALFORMED_CONFIG))?;
    if announced.checked_against != trust.current_version {
        return Err(Refusal::Unavailable(IDENTITY_MISMATCH));
    }
    evaluate_eligibility(&current, trust.channel, &announced.version)?;
    let platform = expected_platform()?;
    if announced.target != platform {
        return Err(Refusal::Failed(PLATFORM_MISMATCH));
    }
    let binding = platform_binding()?;
    Ok(AdmittedCandidate::new(&trust, &announced.version, &binding))
}

// ---------------------------------------------------------------------------
// Candidate identity and verified bytes
// ---------------------------------------------------------------------------

fn hex_sha256(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut out = String::with_capacity(digest.len() * 2);
    for byte in digest.iter() {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

/// Deterministic identity of the admitted candidate projection.
///
/// Fixed field order over an explicit vocabulary, not a serialized response
/// body: the endpoint may add or reorder JSON fields freely, and a metadata
/// hash that tracked raw JSON would not be a stable identity.
pub fn metadata_identity(
    channel: &str,
    current_version: &str,
    candidate_version: &str,
    target: &str,
    public_key_fingerprint: &str,
) -> String {
    let mut projection = String::from(ADMISSION_RECEIPT_CONTRACT);
    projection.push('\n');
    projection.push_str("scheme=");
    projection.push_str(ADMITTED_SCHEME);
    projection.push('\n');
    projection.push_str("channel=");
    projection.push_str(channel);
    projection.push('\n');
    projection.push_str("current=");
    projection.push_str(current_version);
    projection.push('\n');
    projection.push_str("candidate=");
    projection.push_str(candidate_version);
    projection.push('\n');
    projection.push_str("target=");
    projection.push_str(target);
    projection.push('\n');
    projection.push_str("key=");
    projection.push_str(public_key_fingerprint);
    projection.push('\n');
    hex_sha256(projection.as_bytes())
}

/// A candidate the policy gate admitted, bound to the trust data that produced
/// it.
///
/// The key fingerprint and the platform binding are inputs to `metadata_sha256`,
/// not fields this slice acts on, so they are deliberately not carried in
/// plaintext: the receipt binds them, and nothing on the wire or in this build
/// needs to read them back.
#[derive(Debug, Clone)]
pub struct AdmittedCandidate {
    pub channel: &'static str,
    pub current_version: String,
    pub candidate_version: String,
    pub metadata_sha256: String,
}

impl AdmittedCandidate {
    pub fn new(trust: &UpdateTrustConfig, candidate_version: &str, target: &str) -> Self {
        let metadata_sha256 = metadata_identity(
            trust.channel,
            &trust.current_version,
            candidate_version,
            target,
            &trust.public_key_fingerprint,
        );
        Self {
            channel: trust.channel,
            current_version: trust.current_version.clone(),
            candidate_version: candidate_version.to_owned(),
            metadata_sha256,
        }
    }
}

/// The presentation-only half of the admission receipt. It is evidence about a
/// verification that already happened in trusted Rust state; it is not an
/// authorization token and nothing in this build consumes it as one.
#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct AuthenticityProof {
    pub scheme: &'static str,
    pub artifact_sha256: String,
    pub metadata_sha256: String,
    pub verified_at_epoch_ms: u64,
}

/// The record of a verification that succeeded: the candidate that was admitted,
/// the proof derived from the bytes the updater returned, and those bytes
/// themselves.
///
/// R4 makes the bytes part of the owned candidate, not an implementation detail:
/// `ready` promises an artifact that is present, verified and waiting, so the
/// single pending candidate has to be the thing a later governed install consumes.
#[derive(Debug, Clone)]
pub struct VerifiedCandidate {
    pub admitted: AdmittedCandidate,
    pub proof: AuthenticityProof,
    /// Signature-verified artifact bytes, retained in trusted Rust state only.
    /// Nothing in this build writes them to a file, and the status wire has no
    /// field they could be serialised into.
    ///
    /// No consumer exists yet by design: reading them out is the install slice,
    /// which is separately governed authority. The field is the candidate the
    /// `ready` state promises, so it has to survive the download even though this
    /// build can only hold it.
    #[allow(dead_code)]
    pub bytes: Vec<u8>,
}

/// Hash verified bytes and bind them to the candidate that was checked.
///
/// `artifact_sha256` covers exactly what the updater returned, so a later
/// substitution cannot present different bytes under the same candidate name, and
/// the retained payload is bound to the same `metadata_sha256` the proof carries.
/// The bytes arrive here only after `Update::download` has verified the signature,
/// so no unverified byte can enter the slot.
pub fn admit_verified_bytes(
    admitted: &AdmittedCandidate,
    bytes: &[u8],
    verified_at_epoch_ms: u64,
) -> VerifiedCandidate {
    let artifact_sha256 = hex_sha256(bytes);
    VerifiedCandidate {
        admitted: admitted.clone(),
        proof: AuthenticityProof {
            scheme: ADMITTED_SCHEME,
            artifact_sha256,
            metadata_sha256: admitted.metadata_sha256.clone(),
            verified_at_epoch_ms,
        },
        bytes: bytes.to_vec(),
    }
}

// ---------------------------------------------------------------------------
// Bounded status wire
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct WireError {
    code: &'static str,
    detail: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct WireStatus {
    contract: &'static str,
    state: &'static str,
    channel: &'static str,
    current_version: String,
    candidate_version: Option<String>,
    authenticity_proof: Option<AuthenticityProof>,
    error: Option<WireError>,
    /// Always empty: this slice records no transition history in the backend,
    /// and the contract's key set is closed, so no extra field can ride along.
    events: &'static [&'static str],
}

// ---------------------------------------------------------------------------
// Held state
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
enum Held {
    /// Nothing checked.
    Empty,
    /// Policy-admitted candidate awaiting download.
    Admitted(AdmittedCandidate),
    /// A download is in flight; it owns the candidate.
    InFlight(AdmittedCandidate),
    /// Signature-verified bytes were obtained for this candidate.
    Verified(VerifiedCandidate),
    /// The last refusal, so a later status read cannot pose as a fresh idle.
    Refused(Refusal),
}

/// Trusted state behind the three named commands. The updater handle is kept
/// alongside its admitted identity so a download can only ever act on the exact
/// candidate the check admitted.
pub struct UpdateAdmissionBridge {
    inner: Mutex<BridgeInner>,
}

struct BridgeInner {
    held: Held,
    update: Option<Update>,
}

impl Default for UpdateAdmissionBridge {
    fn default() -> Self {
        Self::new()
    }
}

impl UpdateAdmissionBridge {
    pub fn new() -> Self {
        Self {
            inner: Mutex::new(BridgeInner {
                held: Held::Empty,
                update: None,
            }),
        }
    }

    fn snapshot_of(inner: &BridgeInner) -> Result<WireStatus, Refusal> {
        let (current_version, channel) = match &inner.held {
            Held::Admitted(candidate) | Held::InFlight(candidate) => {
                (candidate.current_version.clone(), candidate.channel)
            }
            Held::Verified(verified) => (
                verified.admitted.current_version.clone(),
                verified.admitted.channel,
            ),
            Held::Empty | Held::Refused(_) => bridge_identity()?,
        };
        let mut state = "idle";
        let mut proof = None;
        let mut candidate_version = None;
        let mut error = None;
        match &inner.held {
            Held::Empty => {}
            Held::Admitted(candidate) => {
                state = "available";
                candidate_version = Some(candidate.candidate_version.clone());
            }
            Held::InFlight(candidate) => {
                state = "available";
                candidate_version = Some(candidate.candidate_version.clone());
            }
            Held::Verified(verified) => {
                state = "ready";
                candidate_version = Some(verified.admitted.candidate_version.clone());
                proof = Some(verified.proof.clone());
            }
            Held::Refused(Refusal::Unavailable(denial)) => {
                state = "unavailable";
                error = Some(WireError {
                    code: denial.code,
                    detail: denial.detail.to_owned(),
                });
            }
            Held::Refused(Refusal::Failed(denial)) => {
                state = "failure";
                error = Some(WireError {
                    code: denial.code,
                    detail: denial.detail.to_owned(),
                });
            }
        }
        Ok(WireStatus {
            contract: UPDATE_STATE_CONTRACT,
            state,
            channel,
            current_version,
            candidate_version,
            authenticity_proof: proof,
            error,
            events: &[],
        })
    }

    /// Bounded snapshot of what trusted state currently holds. No network.
    pub fn snapshot(&self) -> Result<WireStatus, Refusal> {
        let inner = self.lock()?;
        Self::snapshot_of(&inner)
    }

    /// Whether the slot owns nothing: no candidate, no verified bytes, no
    /// recorded refusal.
    ///
    /// A status read consults this to decide whether it may answer `idle` at all.
    /// From the frontend's side "no attempt has happened yet" and "this build can
    /// never attempt" look identical unless the read says otherwise, so `idle` has
    /// to be earned by a configured trust root rather than granted by the absence
    /// of an attempt.
    pub fn holds_nothing(&self) -> Result<bool, Refusal> {
        Ok(matches!(self.lock()?.held, Held::Empty))
    }

    /// Admit exactly one candidate from a check the caller cannot steer.
    ///
    /// `announced` is projected from `update` by [`announced_of`], so the version,
    /// platform and checked-against identity cannot be supplied independently of
    /// the handle that is stored alongside them.
    pub fn admit_check(
        &self,
        probe: &UpdaterTrustProbe,
        announced: &AnnouncedCandidate,
        update: &Update,
        current_version: &str,
    ) -> Result<AdmittedCandidate, Refusal> {
        let admitted = evaluate_admission(probe, announced, current_version)?;
        self.begin(admitted.clone(), Some(update.clone()))?;
        Ok(admitted)
    }

    /// Claim the single pending-candidate slot, taking the handle that must be
    /// downloaded with it. A second admission attempt never replaces the first.
    ///
    /// A refused slot is the one state a check may take over: a refusal left no
    /// candidate behind, so retrying is the only way a transient fault can ever
    /// stop being the reported state. A candidate that is pending, in flight or
    /// verified is a different thing, and nothing here replaces it.
    fn begin(&self, admitted: AdmittedCandidate, update: Option<Update>) -> Result<(), Refusal> {
        let mut inner = self.lock()?;
        if !matches!(inner.held, Held::Empty | Held::Refused(_)) {
            return Err(Refusal::Failed(CANDIDATE_ALREADY_ADMITTED));
        }
        inner.held = Held::Admitted(admitted);
        inner.update = update;
        Ok(())
    }

    /// Take the admitted candidate so a concurrent call cannot act on it too.
    ///
    /// A candidate that is already in flight or already verified occupies the
    /// slot, so the refusal names that fact rather than pretending nothing was
    /// admitted.
    pub fn take_for_download(&self) -> Result<(AdmittedCandidate, Update), Refusal> {
        let mut inner = self.lock()?;
        let admitted = match &inner.held {
            Held::Admitted(candidate) => candidate.clone(),
            Held::InFlight(_) | Held::Verified(_) => {
                return Err(Refusal::Failed(CANDIDATE_ALREADY_ADMITTED));
            }
            Held::Empty | Held::Refused(_) => return Err(Refusal::Failed(NO_ADMITTED_CANDIDATE)),
        };
        let update = inner.update.take().ok_or(Refusal::Failed(NO_ADMITTED_CANDIDATE))?;
        inner.held = Held::InFlight(admitted.clone());
        Ok((admitted, update))
    }

    /// Record verified bytes, refusing to replace a candidate already verified.
    pub fn complete_download(
        &self,
        admitted: &AdmittedCandidate,
        bytes: &[u8],
        verified_at_epoch_ms: u64,
    ) -> Result<WireStatus, Refusal> {
        let verified = admit_verified_bytes(admitted, bytes, verified_at_epoch_ms);
        let mut inner = self.lock()?;
        let owns_this_candidate = matches!(
            &inner.held,
            Held::InFlight(held) if held.metadata_sha256 == admitted.metadata_sha256
        );
        if !owns_this_candidate {
            return Err(match &inner.held {
                Held::Verified(_) => Refusal::Failed(CANDIDATE_ALREADY_ADMITTED),
                _ => Refusal::Failed(NO_ADMITTED_CANDIDATE),
            });
        }
        inner.held = Held::Verified(verified);
        Self::snapshot_of(&inner)
    }

    /// Remember a refusal so the next status read reports it rather than idle.
    ///
    /// Two claims have to survive this call, because a refusal says something
    /// about the *attempt*, not always about the candidate:
    ///
    /// - A verified candidate is the strongest observation this bridge can make.
    ///   A later attempt, however it failed, cannot demote the ready claim back to
    ///   a failure and lose the bytes it verified.
    /// - A refusal whose whole subject is that the slot is already spoken for
    ///   (`candidate_already_admitted`, `no_admitted_candidate`) is not evidence
    ///   against the held candidate. Swallowing it keeps the pending candidate and
    ///   its updater handle intact, so a duplicate call is a no-op instead of a
    ///   state-destroying one.
    ///
    /// A failure owned by a pending or in-flight operation (such as its download
    /// or verification failing) releases that candidate so a later check can retry.
    /// A check failure is non-owning: it cannot invalidate a candidate admitted
    /// or downloaded by another operation, and is inert while that slot is occupied.
    pub fn record(&self, refusal: Refusal) {
        let Ok(mut inner) = self.inner.lock() else { return };
        if matches!(inner.held, Held::Verified(_)) {
            return;
        }
        let slot_is_occupied = !matches!(inner.held, Held::Empty | Held::Refused(_));
        if slot_is_occupied
            && (is_slot_occupancy_refusal(&refusal) || is_non_owning_check_failure(&refusal))
        {
            return;
        }
        inner.held = Held::Refused(refusal);
        inner.update = None;
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, BridgeInner>, Refusal> {
        self.inner
            .lock()
            .map_err(|_| Refusal::Unavailable(STATE_UNAVAILABLE))
    }
}

/// A candidate as the updater announced it, reduced to the fields Hive admits.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AnnouncedCandidate {
    pub version: String,
    pub target: String,
    /// The version the running build was checked against, as reported by the
    /// updater handle itself. Admission refuses a handle whose notion of
    /// "current" is not this build's canonical version.
    pub checked_against: String,
}

/// Project an updater handle onto the only announcement shape admission accepts.
///
/// This is the single place where an upstream `Update` becomes Hive input, so it
/// is also the place that decides nothing else about a candidate can be believed.
pub fn announced_of(update: &Update) -> AnnouncedCandidate {
    AnnouncedCandidate {
        version: update.version.clone(),
        target: update.target.clone(),
        checked_against: update.current_version.clone(),
    }
}

/// The platform name the official updater puts in `Update::target`: `windows`,
/// `darwin` or `linux`.
///
/// This is deliberately *not* `tauri_plugin_updater::target()`, which returns
/// the `{os}-{arch}` release-lookup key. Comparing an announced candidate
/// against the wrong shape would reject every genuine release, so the mapping is
/// restated here to match the field actually produced upstream.
pub fn expected_platform() -> Result<&'static str, Refusal> {
    if cfg!(target_os = "windows") {
        return Ok("windows");
    }
    if cfg!(target_os = "macos") {
        return Ok("darwin");
    }
    if cfg!(any(
        target_os = "linux",
        target_os = "dragonfly",
        target_os = "freebsd",
        target_os = "netbsd",
        target_os = "openbsd"
    )) {
        return Ok("linux");
    }
    Err(Refusal::Unavailable(PLATFORM_UNSUPPORTED))
}

/// The full `{os}-{arch}` release target this build can install from, used to
/// bind the admission receipt to the machine it was produced on.
pub fn platform_binding() -> Result<String, Refusal> {
    tauri_plugin_updater::target().ok_or(Refusal::Unavailable(PLATFORM_UNSUPPORTED))
}

/// The installed identity this bridge describes: one version, and the one
/// channel that version entails.
pub fn bridge_identity() -> Result<(String, &'static str), Refusal> {
    let version = admit_version(crate::PACKAGE_VERSION).ok_or(Refusal::Unavailable(MALFORMED_CONFIG))?;
    let channel = channel_of(&version).ok_or(Refusal::Unavailable(UNKNOWN_CHANNEL))?;
    Ok((crate::PACKAGE_VERSION.to_owned(), channel))
}

// ---------------------------------------------------------------------------
// Upstream failure translation
// ---------------------------------------------------------------------------

/// Map a failed `Update::download` onto the closed Hive vocabulary.
///
/// Upstream messages embed endpoints, expected paths and signature text, so they
/// are classified and discarded rather than forwarded: a diagnostic detail that
/// quotes a release URL would be refused by the status contract anyway, and
/// quoting it at all would let a hostile endpoint write into product telemetry.
pub fn download_refusal(error: &tauri_plugin_updater::Error) -> Refusal {
    use tauri_plugin_updater::Error;
    match error {
        Error::Minisign(_)
        | Error::Base64(_)
        | Error::SignatureUtf8(_)
        | Error::SignedVersionMismatch { .. }
        | Error::MissingSignedVersion => Refusal::Failed(VERIFICATION_FAILED),
        _ => Refusal::Failed(DOWNLOAD_FAILED),
    }
}

/// Map a failed `Updater::check`. Trust was validated before the request, so
/// this means the configured service could not answer, not that its trust root is
/// absent. A check does not own an already-held candidate.
pub fn check_refusal(_error: &tauri_plugin_updater::Error) -> Refusal {
    Refusal::Failed(SERVICE_UNREACHABLE)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};

    impl UpdateAdmissionBridge {
        /// Place a candidate in the pending slot without an updater handle.
        ///
        /// `Update` cannot be constructed outside the plugin crate, so this is the
        /// only way to exercise the pending-slot guard from a test. It proves the
        /// guard's refusing direction: an admitted candidate with no handle is not
        /// downloadable. That a real handle does download is upstream's behavior
        /// and is only observable against a live signed release.
        pub fn hold_for_test(&self, admitted: AdmittedCandidate) -> Result<(), Refusal> {
            self.begin(admitted, None)
        }

        /// Move the slot into the in-flight state a download owns it in, without
        /// an `Update` handle.
        ///
        /// Same limitation as [`Self::hold_for_test`]: the handle only exists
        /// inside the plugin crate. What is reachable this way is every guard that
        /// depends on slot ownership rather than on a live request — which is what
        /// the second-download and second-completion laws actually turn on.
        pub fn begin_download_for_test(&self, admitted: AdmittedCandidate) {
            let mut inner = self.inner.lock().expect("test bridge lock");
            inner.held = Held::InFlight(admitted);
            inner.update = None;
        }
    }

    const TEST_ENDPOINT: &str = "https://release.example.invalid/{{target}}/{{arch}}/{{current_version}}";

    /// Distinctive enough that a payload reaching any serialised surface is
    /// visible in the failing assertion rather than in a hex dump.
    const ARTIFACT_PAYLOAD: &[u8] = b"hive-signed-artifact-payload-must-not-leave-rust";

    /// Newer than any version this product is realistically going to ship as its
    /// canonical identity, and still inside the declared core bound.
    const NEWER: &str = "999999.0.0";

    fn probe_with(mutate: impl FnOnce(&mut UpdaterTrustProbe)) -> UpdaterTrustProbe {
        let mut probe = UpdaterTrustProbe {
            pubkey: "hive-test-updater-public-key".to_owned(),
            endpoints: vec![TEST_ENDPOINT.to_owned()],
            require_signed_version: true,
            allow_downgrades: false,
            dangerous_insecure_transport_protocol: false,
            dangerous_accept_invalid_certs: false,
            dangerous_accept_invalid_hostnames: false,
        };
        mutate(&mut probe);
        probe
    }

    fn probe() -> UpdaterTrustProbe {
        probe_with(|_| {})
    }

    fn announced_for(candidate: &str, current: &str) -> AnnouncedCandidate {
        AnnouncedCandidate {
            version: candidate.to_owned(),
            target: expected_platform().expect("test platform is supported").to_owned(),
            checked_against: current.to_owned(),
        }
    }

    fn denial_of(refusal: Refusal) -> Denial {
        match refusal {
            Refusal::Unavailable(denial) | Refusal::Failed(denial) => denial,
        }
    }

    fn is_unavailable(refusal: Refusal) -> bool {
        matches!(refusal, Refusal::Unavailable(_))
    }

    fn admitted(candidate: &str, current: &str) -> AdmittedCandidate {
        let trust = evaluate_admission(&probe(), &announced_for(candidate, current), current);
        trust.expect("candidate should be admitted")
    }

    /// Mirrors `SAFE_DETAIL_PATTERN` plus the long-opaque-run rule in
    /// `contracts/updateState.ts`. A refusal the contract cannot echo back is not
    /// a bounded refusal.
    fn detail_is_contract_safe(detail: &str) -> bool {
        let charset_ok = detail.chars().all(|c| {
            c.is_ascii_lowercase() || c.is_ascii_digit() || matches!(c, ' ' | '.' | '_' | ':' | '+' | '-')
        });
        let opaque_run = detail
            .split(|c: char| !(c.is_ascii_alphanumeric() || c == '+' || c == '/'))
            .any(|token| token.len() >= 32);
        detail.len() <= MAX_DETAIL_CHARS && charset_ok && !opaque_run
    }

    fn wire_keys(value: &Value) -> Vec<&str> {
        let mut keys: Vec<&str> = value.as_object().expect("wire status must be an object").keys().map(String::as_str).collect();
        keys.sort_unstable();
        keys
    }

    /// Collect every string a serialised status emits, at any depth, keys included.
    /// Used to prove the wire carries no room for an artifact, not just that the
    /// top-level object lacks an obvious field for one.
    fn wire_strings(value: &Value, found: &mut Vec<String>) {
        match value {
            Value::String(text) => found.push(text.clone()),
            Value::Array(items) => {
                for item in items {
                    wire_strings(item, found);
                }
            }
            Value::Object(entries) => {
                for (key, item) in entries {
                    found.push(key.clone());
                    wire_strings(item, found);
                }
            }
            _ => {}
        }
    }

    #[test]
    fn shipped_configuration_is_the_fail_closed_delta_001_node() {
        let updater_node = json!({
            "pubkey": "",
            "endpoints": [],
            "requireSignedVersion": true,
            "allowDowngrades": false,
            "dangerousInsecureTransportProtocol": false,
            "dangerousAcceptInvalidCerts": false,
            "dangerousAcceptInvalidHostnames": false
        });
        let raw = json!({ "identifier": "com.hive.hcoder.test", "plugins": { "updater": updater_node } });
        let config: tauri::Config =
            serde_json::from_value(raw).expect("delta-001 node must parse inside a tauri config");
        let probe = probe_from_config(&config).expect("delta-001 node must parse as a hive probe");
        assert_eq!(probe.pubkey, "");
        assert_eq!(probe.endpoints, Vec::<String>::new());
        assert!(probe.require_signed_version);
        assert!(!probe.allow_downgrades);
        assert!(!probe.dangerous_insecure_transport_protocol);
        assert!(!probe.dangerous_accept_invalid_certs);
        assert!(!probe.dangerous_accept_invalid_hostnames);
        // The shipped product configuration is exactly this node.
        let product: tauri::Config =
            serde_json::from_str(include_str!("../tauri.conf.json")).expect("shipped tauri.conf.json must parse");
        assert_eq!(probe_from_config(&product).unwrap(), probe);
        // Empty trust data is an unavailable service, not a request to attempt.
        let refusal = resolve_trust(&probe, crate::PACKAGE_VERSION).expect_err("empty trust must refuse");
        assert!(is_unavailable(refusal));
        assert_eq!(denial_of(refusal).code, "service_unavailable");
    }

    #[test]
    fn absent_updater_node_is_a_malformed_configuration() {
        let refusal = probe_from_config(&tauri::Config::default()).expect_err("absent node must refuse");
        assert!(is_unavailable(refusal));
        assert_eq!(denial_of(refusal).code, "service_unavailable");
    }

    #[test]
    fn probe_rejects_unknown_missing_and_alias_ed_keys() {
        let base = json!({
            "pubkey": "hive-test-updater-public-key",
            "endpoints": [TEST_ENDPOINT],
            "requireSignedVersion": true,
            "allowDowngrades": false,
            "dangerousInsecureTransportProtocol": false,
            "dangerousAcceptInvalidCerts": false,
            "dangerousAcceptInvalidHostnames": false
        });
        let admits = |value: Value| serde_json::from_value::<UpdaterTrustProbe>(value).is_ok();
        assert!(admits(base.clone()));
        let mut extra = base.as_object().unwrap().clone();
        extra.insert("allowInsecureTls".to_owned(), json!(true));
        assert!(!admits(Value::Object(extra)), "an unrecognised control must be refused");
        // Upstream accepts this kebab spelling; Hive must not, so a renamed control
        // can never fall back to a permissive default.
        let mut kebab = base.as_object().unwrap().clone();
        kebab.remove("requireSignedVersion");
        kebab.insert("require-signed-version".to_owned(), json!(true));
        assert!(!admits(Value::Object(kebab)));
        // Absence is a refusal, never a default.
        for missing in [
            "pubkey",
            "endpoints",
            "requireSignedVersion",
            "allowDowngrades",
            "dangerousInsecureTransportProtocol",
            "dangerousAcceptInvalidCerts",
            "dangerousAcceptInvalidHostnames",
        ] {
            let mut truncated = base.as_object().unwrap().clone();
            truncated.remove(missing);
            assert!(!admits(Value::Object(truncated)), "{missing} may have been omitted");
        }
    }

    #[test]
    fn unsafe_or_relaxed_controls_are_refused_as_unavailable() {
        let cases: [(fn(&mut UpdaterTrustProbe), &str); 6] = [
            (|p| p.require_signed_version = false, "signed release version not required"),
            (|p| p.allow_downgrades = true, "downgrades allowed"),
            (|p| p.dangerous_insecure_transport_protocol = true, "insecure transport"),
            (|p| p.dangerous_accept_invalid_certs = true, "invalid certificates"),
            (|p| p.dangerous_accept_invalid_hostnames = true, "invalid hostnames"),
            (|p| p.pubkey = "   ".to_owned(), "blank public key"),
        ];
        for (mutate, label) in cases {
            let mutated = probe_with(mutate);
            let refusal = resolve_trust(&mutated, "0.1.0").expect_err(label);
            assert!(is_unavailable(refusal), "{label} must be unavailable, not a candidate refusal");
            assert_eq!(denial_of(refusal).code, "service_unavailable");
        }
    }

    #[test]
    fn only_https_origin_endpoints_are_trusted() {
        for bad in [
            "http://release.example.invalid/updates",
            "https://",
            "https://release.example.invalid ",
            "https://user@release.example.invalid/updates",
            "file:///C:/release.json",
            "not a url",
            "",
        ] {
            let mutated = probe_with(|p| p.endpoints = vec![bad.to_owned()]);
            let refusal = resolve_trust(&mutated, "0.1.0").expect_err("endpoint must be refused");
            assert_eq!(denial_of(refusal).code, "service_unavailable", "{bad}");
        }
        assert!(resolve_trust(&probe(), "0.1.0").is_ok());
        let ported =
            probe_with(|p| p.endpoints = vec!["https://release.example.invalid:8443/updates".to_owned()]);
        assert!(resolve_trust(&ported, "0.1.0").is_ok());
    }

    #[test]
    fn channel_is_derived_from_the_installed_version_shape() {
        let cases = [
            ("1.2.3", Some(CHANNEL_STABLE)),
            ("1.2.3-beta.1", Some(CHANNEL_BETA)),
            ("1.2.3-dev.4", Some(CHANNEL_DEV)),
            ("1.2.3-rc.1", None),
            ("1.2.3+build.9", Some(CHANNEL_STABLE)),
        ];
        for (raw, expected) in cases {
            let derived = admit_version(raw).as_ref().map(channel_of).flatten();
            assert_eq!(derived, expected, "{raw}");
        }
    }

    #[test]
    fn eligibility_is_same_channel_and_strictly_newer_only() {
        let ok = evaluate_admission(&probe(), &announced_for(NEWER, "1.0.0"), "1.0.0").unwrap();
        assert_eq!(ok.candidate_version, NEWER);
        assert_eq!(ok.channel, CHANNEL_STABLE);
        assert_eq!(ok.current_version, "1.0.0");

        let equal = denial_of(evaluate_admission(&probe(), &announced_for("1.0.0", "1.0.0"), "1.0.0").unwrap_err());
        assert_eq!(equal.code, "channel_not_eligible");
        let older = denial_of(evaluate_admission(&probe(), &announced_for("0.9.9", "1.0.0"), "1.0.0").unwrap_err());
        assert_eq!(older.code, "downgrade_not_permitted");
        let malformed = denial_of(evaluate_admission(&probe(), &announced_for("v1.2.3", "1.0.0"), "1.0.0").unwrap_err());
        assert_eq!(malformed.code, "malformed_version");

        // Cross-channel in either direction requires a governed decision, never a
        // side effect of an upgrade.
        let to_beta =
            denial_of(evaluate_admission(&probe(), &announced_for("2.0.0-beta.1", "1.0.0"), "1.0.0").unwrap_err());
        assert_eq!(to_beta.code, "cross_channel_not_permitted");
        let to_stable =
            denial_of(evaluate_admission(&probe(), &announced_for("2.0.0", "1.0.0-beta.1"), "1.0.0-beta.1").unwrap_err());
        assert_eq!(to_stable.code, "cross_channel_not_permitted");
        // An unrecognised prerelease belongs to no channel at all.
        let rc = denial_of(evaluate_admission(&probe(), &announced_for("2.0.0-rc.1", "1.0.0"), "1.0.0").unwrap_err());
        assert_eq!(rc.code, "cross_channel_not_permitted");
    }

    #[test]
    fn prerelease_ordering_cannot_be_bypassed_by_string_length() {
        // `1.0.0-beta.10` is newer than `1.0.0-beta.2`; a lexical compare would
        // invert that and hide a downgrade behind a longer identifier.
        assert!(evaluate_admission(&probe(), &announced_for("1.0.0-beta.10", "1.0.0-beta.2"), "1.0.0-beta.2").is_ok());
        let back = denial_of(
            evaluate_admission(&probe(), &announced_for("1.0.0-beta.2", "1.0.0-beta.10"), "1.0.0-beta.10").unwrap_err(),
        );
        assert_eq!(back.code, "downgrade_not_permitted");
    }

    #[test]
    fn candidate_identity_substitution_is_refused() {
        let substituted = AnnouncedCandidate {
            checked_against: "0.0.1".to_owned(),
            ..announced_for(NEWER, "0.1.0")
        };
        let refusal = denial_of(evaluate_admission(&probe(), &substituted, "0.1.0").unwrap_err());
        assert_eq!(refusal.code, "service_unavailable");

        let wrong_platform = AnnouncedCandidate {
            target: "plan9".to_owned(),
            ..announced_for(NEWER, "0.1.0")
        };
        let refusal = denial_of(evaluate_admission(&probe(), &wrong_platform, "0.1.0").unwrap_err());
        assert_eq!(refusal.code, "channel_not_eligible");
    }

    #[test]
    fn version_profile_matches_the_shared_parity_vectors() {
        let vectors: Value =
            serde_json::from_str(include_str!("../../src/contracts/semverParityVectors.json")).unwrap();
        assert_eq!(vectors["contract"], "hive-version-v1");
        let accepted = vectors["accepted"].as_array().unwrap();
        let rejected = vectors["rejected"].as_array().unwrap();
        assert!(accepted.len() > 10, "parity corpus must be substantive");
        for raw in accepted {
            let raw = raw.as_str().unwrap();
            assert!(admit_version(raw).is_some(), "{raw} must be accepted");
        }
        for raw in rejected {
            // A non-string vector cannot even enter the Rust admission surface, which
            // takes `&str`; refusing is its only possible outcome. String vectors must
            // be refused by the shared profile itself.
            let refused = match raw.as_str() {
                Some(value) => admit_version(value).is_none(),
                None => true,
            };
            assert!(refused, "{raw} must be rejected");
        }
    }

    #[test]
    fn metadata_identity_is_deterministic_and_binds_every_input() {
        let base = metadata_identity("stable", "1.0.0", NEWER, "windows-x86_64", "key-a");
        assert_eq!(base, metadata_identity("stable", "1.0.0", NEWER, "windows-x86_64", "key-a"));
        assert_eq!(base.len(), 64);
        for variant in [
            metadata_identity("beta", "1.0.0", NEWER, "windows-x86_64", "key-a"),
            metadata_identity("stable", "1.0.1", NEWER, "windows-x86_64", "key-a"),
            metadata_identity("stable", "1.0.0", "1.0.2", "windows-x86_64", "key-a"),
            metadata_identity("stable", "1.0.0", NEWER, "windows-i686", "key-a"),
            metadata_identity("stable", "1.0.0", NEWER, "windows-x86_64", "key-b"),
        ] {
            assert_ne!(variant, base);
        }
    }

    #[test]
    fn proof_binds_artifact_and_metadata_without_exposing_trust_data() {
        let admitted = admitted(NEWER, "0.1.0");
        let proof = admit_verified_bytes(&admitted, b"artifact-bytes", 1_700_000_000_000).proof;
        assert_eq!(proof.scheme, ADMITTED_SCHEME);
        assert_eq!(proof.metadata_sha256, admitted.metadata_sha256);
        assert_eq!(proof.artifact_sha256, hex_sha256(b"artifact-bytes"));
        assert_eq!(proof.artifact_sha256.len(), 64);
        assert_eq!(proof.verified_at_epoch_ms, 1_700_000_000_000);
        assert_eq!(
            wire_keys(&serde_json::to_value(&proof).unwrap()),
            ["artifactSha256", "metadataSha256", "scheme", "verifiedAtEpochMs"]
        );
    }

    #[test]
    fn status_wire_carries_exactly_the_contract_key_set() {
        let value = serde_json::to_value(UpdateAdmissionBridge::new().snapshot().unwrap()).unwrap();
        assert_eq!(
            wire_keys(&value),
            [
                "authenticityProof",
                "candidateVersion",
                "channel",
                "contract",
                "currentVersion",
                "error",
                "events",
                "state"
            ]
        );
        assert_eq!(value["contract"], UPDATE_STATE_CONTRACT);
        assert_eq!(value["state"], "idle");
        assert_eq!(value["candidateVersion"], Value::Null);
        assert_eq!(value["authenticityProof"], Value::Null);
        assert_eq!(value["error"], Value::Null);
        assert_eq!(value["events"], json!([]));
        let (version, channel) = bridge_identity().unwrap();
        assert_eq!(value["currentVersion"], version);
        assert_eq!(value["channel"], channel);
    }

    #[test]
    fn verified_wire_claims_ready_with_a_proof_and_no_error() {
        let verified = admit_verified_bytes(&admitted(NEWER, "0.1.0"), b"bytes", 1_700_000_000_000);
        let inner = BridgeInner {
            held: Held::Verified(verified),
            update: None,
        };
        let value = serde_json::to_value(UpdateAdmissionBridge::snapshot_of(&inner).unwrap()).unwrap();
        assert_eq!(value["state"], "ready");
        assert_eq!(value["candidateVersion"], NEWER);
        assert_eq!(value["error"], Value::Null);
        assert_eq!(value["authenticityProof"]["scheme"], ADMITTED_SCHEME);
    }

    #[test]
    fn verified_candidate_retains_exactly_the_bytes_it_hashed() {
        let admission = admitted(NEWER, "0.1.0");
        let verified = admit_verified_bytes(&admission, ARTIFACT_PAYLOAD, 1_700_000_000_000);
        assert_eq!(verified.bytes, ARTIFACT_PAYLOAD);
        // The proof describes the payload the same record holds, under the same
        // admitted identity — nothing else could be `ready`.
        assert_eq!(verified.proof.artifact_sha256, hex_sha256(&verified.bytes));
        assert_eq!(verified.proof.metadata_sha256, admission.metadata_sha256);
        assert_eq!(verified.admitted.metadata_sha256, admission.metadata_sha256);
        // Different bytes under one identity is exactly the substitution the
        // retained hash exists to make visible.
        let swapped = admit_verified_bytes(&admission, b"substituted-bytes", 1_700_000_000_000);
        assert_ne!(swapped.proof.artifact_sha256, verified.proof.artifact_sha256);
        assert_eq!(swapped.proof.metadata_sha256, verified.proof.metadata_sha256);
        // One payload admitted under two candidates stays two separate bindings.
        let renamed =
            admit_verified_bytes(&admitted("999998.0.0", "0.1.0"), ARTIFACT_PAYLOAD, 1_700_000_000_000);
        assert_eq!(renamed.proof.artifact_sha256, verified.proof.artifact_sha256);
        assert_ne!(renamed.proof.metadata_sha256, verified.proof.metadata_sha256);
    }

    #[test]
    fn ready_status_carries_a_binding_and_never_the_payload() {
        let verified = admit_verified_bytes(&admitted(NEWER, "0.1.0"), ARTIFACT_PAYLOAD, 1_700_000_000_000);
        let inner = BridgeInner {
            held: Held::Verified(verified),
            update: None,
        };
        let status = UpdateAdmissionBridge::snapshot_of(&inner).unwrap();
        let value = serde_json::to_value(&status).unwrap();
        assert_eq!(value["state"], "ready");
        assert_eq!(value["authenticityProof"]["artifactSha256"], hex_sha256(ARTIFACT_PAYLOAD));
        // The closed key set has no field an artifact could ride in, and every
        // string the wire can emit stays inside the bounded vocabulary.
        assert_eq!(wire_keys(&value).len(), 8);
        assert_eq!(wire_keys(&value["authenticityProof"]).len(), 4);
        let mut text = Vec::new();
        wire_strings(&value, &mut text);
        let payload = std::str::from_utf8(ARTIFACT_PAYLOAD).expect("test payload is utf-8");
        assert!(
            text.iter().all(|seen| !seen.contains(payload)),
            "the verified payload reached the status wire"
        );
        assert!(
            text.iter().all(|seen| seen.len() <= MAX_DETAIL_CHARS),
            "an unbounded string reached the status wire"
        );
    }

    #[test]
    fn a_second_completion_cannot_replace_the_ready_candidates_bytes() {
        let bridge = UpdateAdmissionBridge::new();
        let candidate = admitted(NEWER, crate::PACKAGE_VERSION);
        bridge.begin_download_for_test(candidate.clone());
        let status = bridge
            .complete_download(&candidate, ARTIFACT_PAYLOAD, 1_700_000_000_000)
            .expect("the in-flight candidate may complete");
        assert_eq!(status.state, "ready");
        // The same candidate completing again is refused, and the held bytes are
        // still the ones the first completion verified.
        let refusal = bridge
            .complete_download(&candidate, b"late-substitution", 1_700_000_000_001)
            .err()
            .expect("a ready candidate is not a slot waiting for other bytes");
        assert_eq!(denial_of(refusal).code, "candidate_already_admitted");
        let after = bridge.snapshot().unwrap();
        assert_eq!(after.state, "ready");
        assert_eq!(
            after.authenticity_proof.expect("ready must still carry its proof").artifact_sha256,
            hex_sha256(ARTIFACT_PAYLOAD)
        );
    }

    #[test]
    fn completion_only_binds_the_candidate_the_slot_owns() {
        let bridge = UpdateAdmissionBridge::new();
        let held = admitted(NEWER, crate::PACKAGE_VERSION);
        let other = admitted("999998.0.0", crate::PACKAGE_VERSION);
        bridge.begin_download_for_test(held.clone());
        let refusal = bridge
            .complete_download(&other, ARTIFACT_PAYLOAD, 1_700_000_000_000)
            .err()
            .expect("an unclaimed candidate cannot complete");
        assert_eq!(denial_of(refusal).code, "no_admitted_candidate");
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "available");
        assert_eq!(value["candidateVersion"], NEWER);
        assert_eq!(value["authenticityProof"], Value::Null);
        // The attempt did not consume the in-flight candidate either.
        assert_eq!(
            denial_of(bridge.complete_download(&other, ARTIFACT_PAYLOAD, 1_700_000_000_000).err().unwrap()).code,
            "no_admitted_candidate"
        );
    }

    #[test]
    fn a_duplicate_check_leaves_the_pending_candidate_held() {
        let bridge = UpdateAdmissionBridge::new();
        let first = admitted(NEWER, crate::PACKAGE_VERSION);
        let second = admitted("999998.0.0", crate::PACKAGE_VERSION);
        bridge.hold_for_test(first.clone()).expect("an empty slot admits");
        let refusal = bridge
            .hold_for_test(second)
            .err()
            .expect("a held candidate cannot be replaced");
        // This is the exact sequence a second `check_for_update` produces, refusal
        // report included: the duplicate must not cost the build its candidate.
        bridge.record(refusal);
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "available");
        assert_eq!(value["candidateVersion"], NEWER);
        assert_eq!(value["error"], Value::Null);
    }

    #[test]
    fn a_second_download_attempt_leaves_the_in_flight_candidate_alone() {
        let bridge = UpdateAdmissionBridge::new();
        let candidate = admitted(NEWER, crate::PACKAGE_VERSION);
        bridge.begin_download_for_test(candidate.clone());
        let refusal = bridge.take_for_download().err().expect("the slot is already in flight");
        assert_eq!(denial_of(refusal).code, "candidate_already_admitted");
        bridge.record(refusal);
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "available");
        assert_eq!(value["candidateVersion"], NEWER);
    }

    #[test]
    fn a_verified_candidate_survives_every_later_refusal() {
        let bridge = UpdateAdmissionBridge::new();
        let candidate = admitted(NEWER, crate::PACKAGE_VERSION);
        bridge.begin_download_for_test(candidate.clone());
        bridge.complete_download(&candidate, ARTIFACT_PAYLOAD, 1_700_000_000_000).expect("ready");
        let refusal = bridge.take_for_download().err().expect("a ready candidate cannot be re-downloaded");
        bridge.record(refusal);
        bridge.record(Refusal::Unavailable(SERVICE_UNREACHABLE));
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        // `ready` claims bytes exist and were verified. A later attempt failing for
        // its own reasons cannot make that claim false, so it cannot erase them.
        assert_eq!(value["state"], "ready");
        assert_eq!(value["authenticityProof"]["artifactSha256"], hex_sha256(ARTIFACT_PAYLOAD));
    }

    #[test]
    fn a_failed_download_releases_the_slot_so_a_later_check_is_a_real_retry() {
        let bridge = UpdateAdmissionBridge::new();
        bridge.begin_download_for_test(admitted(NEWER, crate::PACKAGE_VERSION));
        // A genuine fault is not a slot-occupancy refusal: the attempt consumed
        // this candidate, so the failure is what the build reports.
        bridge.record(Refusal::Failed(DOWNLOAD_FAILED));
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "failure");
        assert_eq!(value["error"]["code"], "download_failed");
        // And because the refusal released the slot, the next check is a lawful
        // retry rather than a permanent `candidate_already_admitted`.
        bridge
            .hold_for_test(admitted("999998.0.0", crate::PACKAGE_VERSION))
            .expect("a refusal is retryable by a later check");
        assert_eq!(bridge.snapshot().unwrap().state, "available");
    }

    #[test]
    fn a_failed_check_is_a_failure_not_missing_configuration() {
        let refusal = check_refusal(&tauri_plugin_updater::Error::ReleaseNotFound);
        assert!(matches!(
            refusal,
            Refusal::Failed(denial) if denial.code == SERVICE_UNREACHABLE.code
        ));

        let bridge = UpdateAdmissionBridge::new();
        bridge.record(refusal);
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "failure");
        assert_eq!(value["error"]["code"], "service_unavailable");
    }

    #[test]
    fn a_non_owning_check_failure_does_not_replace_an_admitted_candidate() {
        let bridge = UpdateAdmissionBridge::new();
        bridge
            .hold_for_test(admitted(NEWER, crate::PACKAGE_VERSION))
            .expect("the bridge holds an admitted candidate");

        let refusal = check_refusal(&tauri_plugin_updater::Error::ReleaseNotFound);
        bridge.record(refusal);
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "available");
        assert_eq!(value["candidateVersion"], NEWER);
        assert_eq!(value["error"], Value::Null);
    }

    #[test]
    fn a_non_owning_check_failure_preserves_an_in_flight_download() {
        let bridge = UpdateAdmissionBridge::new();
        let candidate = admitted(NEWER, crate::PACKAGE_VERSION);
        bridge.begin_download_for_test(candidate.clone());

        let refusal = check_refusal(&tauri_plugin_updater::Error::ReleaseNotFound);
        bridge.record(refusal);
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "downloading");
        assert_eq!(value["candidateVersion"], NEWER);

        let ready = bridge
            .complete_download(&candidate, ARTIFACT_PAYLOAD, 1_700_000_000_000)
            .expect("the owner may complete after a non-owning check fails");
        assert_eq!(ready.state, "ready");
        assert_eq!(
            ready.authenticity_proof.expect("ready proof").artifact_sha256,
            hex_sha256(ARTIFACT_PAYLOAD)
        );
    }

    #[test]
    fn an_unreachable_service_is_reported_until_a_retrying_check_replaces_it() {
        let bridge = UpdateAdmissionBridge::new();
        assert!(bridge.holds_nothing().expect("fresh bridge"));
        bridge.record(Refusal::Unavailable(SERVICE_UNREACHABLE));
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "unavailable");
        assert_eq!(value["error"]["code"], "service_unavailable");
        assert!(!bridge.holds_nothing().expect("a refusal is an observation the bridge keeps"));
        bridge.hold_for_test(admitted(NEWER, crate::PACKAGE_VERSION)).expect("retry after refusal");
        assert!(!bridge.holds_nothing().expect("the slot is now held"));
        assert_eq!(bridge.snapshot().unwrap().state, "available");
    }

    #[test]
    fn pending_slot_holds_exactly_one_candidate() {
        let bridge = UpdateAdmissionBridge::new();
        assert_eq!(bridge.snapshot().unwrap().state, "idle");
        bridge.hold_for_test(admitted(NEWER, crate::PACKAGE_VERSION)).unwrap();
        assert_eq!(bridge.snapshot().unwrap().state, "available");
        let refusal = denial_of(bridge.hold_for_test(admitted("999998.0.0", crate::PACKAGE_VERSION)).unwrap_err());
        assert_eq!(refusal.code, "candidate_already_admitted");
        // The refusal must not have disturbed the candidate already held.
        assert_eq!(bridge.snapshot().unwrap().candidate_version.as_deref(), Some(NEWER));
    }

    #[test]
    fn admitted_without_handle_and_ready_without_download_both_refuse() {
        let bridge = UpdateAdmissionBridge::new();
        assert_eq!(denial_of(bridge.take_for_download().err().unwrap()).code, "no_admitted_candidate");

        bridge.hold_for_test(admitted(NEWER, crate::PACKAGE_VERSION)).unwrap();
        // An admitted candidate whose updater handle is absent cannot be
        // downloaded, and the pending slot is not consumed by the attempt.
        assert_eq!(denial_of(bridge.take_for_download().err().unwrap()).code, "no_admitted_candidate");
        assert_eq!(bridge.snapshot().unwrap().state, "available");

        let refusal = denial_of(
            bridge
                .complete_download(&admitted(NEWER, crate::PACKAGE_VERSION), b"bytes", 1_700_000_000_000)
                .unwrap_err(),
        );
        assert_eq!(refusal.code, "no_admitted_candidate");
    }

    #[test]
    fn recorded_refusal_is_reported_instead_of_a_fresh_idle() {
        let bridge = UpdateAdmissionBridge::new();
        bridge.record(Refusal::Failed(CANDIDATE_ALREADY_ADMITTED));
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "failure");
        assert_eq!(value["error"]["code"], "candidate_already_admitted");
        assert!(value["error"]["detail"].as_str().is_some_and(detail_is_contract_safe));
        assert_eq!(value["candidateVersion"], Value::Null);

        bridge.record(Refusal::Unavailable(TRUST_NOT_CONFIGURED));
        let value = serde_json::to_value(bridge.snapshot().unwrap()).unwrap();
        assert_eq!(value["state"], "unavailable");
        assert_eq!(value["error"]["code"], "service_unavailable");
    }

    #[test]
    fn every_refusal_uses_the_closed_vocabulary_and_safe_detail() {
        let denials = [
            TRUST_NOT_CONFIGURED,
            SIGNED_VERSION_NOT_REQUIRED,
            DOWNGRADES_ALLOWED,
            UNSAFE_TRANSPORT,
            UNSAFE_ENDPOINT,
            MALFORMED_CONFIG,
            UNKNOWN_CHANNEL,
            CANDIDATE_ALREADY_ADMITTED,
            NO_ADMITTED_CANDIDATE,
            PLATFORM_UNSUPPORTED,
            PLATFORM_MISMATCH,
            SERVICE_UNREACHABLE,
            VERIFICATION_FAILED,
            DOWNLOAD_FAILED,
            IDENTITY_MISMATCH,
            STATE_UNAVAILABLE,
        ];
        // Mirrors `UPDATE_ERROR_CODES` in `contracts/updateState.ts`.
        let admitted_codes = [
            "malformed_version",
            "unknown_channel",
            "channel_not_eligible",
            "downgrade_not_permitted",
            "cross_channel_not_permitted",
            "authenticity_proof_required",
            "verification_failed",
            "download_failed",
            "install_failed",
            "service_unavailable",
            "service_inert",
            "candidate_already_admitted",
            "no_admitted_candidate",
        ];
        assert_eq!(denials.len(), 16, "every declared denial must be checked");
        for denial in denials {
            assert!(admitted_codes.contains(&denial.code), "{} is not a contract code", denial.code);
            assert!(detail_is_contract_safe(denial.detail), "{} is not redaction-safe", denial.detail);
        }
    }

    #[test]
    fn upstream_faults_map_to_bounded_denials_and_never_forward_text() {
        use tauri_plugin_updater::Error;

        // Where an upstream message would carry remote text. A denial's detail is
        // `&'static str`, so a forwarded endpoint could not even compile; this
        // asserts the mapping rather than trusting it.
        let hostile = "https://release.invalid/a";
        let verification_faults = [
            Error::MissingSignedVersion,
            Error::SignedVersionMismatch {
                signed: hostile.to_owned(),
                announced: "0.9.9".to_owned(),
            },
            Error::SignatureUtf8(hostile.to_owned()),
        ];
        for fault in verification_faults {
            let denial = denial_of(download_refusal(&fault));
            assert_eq!(denial, VERIFICATION_FAILED, "{fault}");
            assert!(detail_is_contract_safe(denial.detail), "{fault}");
            assert!(!denial.detail.contains("release.invalid"), "{fault}");
        }

        // Everything that is not a signature fault is a transport failure, never
        // a silently-admitted release.
        for fault in [
            Error::Network(hostile.to_owned()),
            Error::Io(std::io::Error::other(hostile.to_owned())),
            Error::ReleaseNotFound,
        ] {
            let denial = denial_of(download_refusal(&fault));
            assert_eq!(denial, DOWNLOAD_FAILED, "{fault}");
        }

        // A failed check never reached a candidate, so it reports unavailability
        // rather than pretending a release was refused.
        for fault in [Error::EmptyEndpoints, Error::ReleaseNotFound] {
            let refusal = check_refusal(&fault);
            assert!(matches!(refusal, Refusal::Unavailable(_)), "{fault}");
            assert_eq!(denial_of(refusal).code, "service_unavailable", "{fault}");
        }
    }

    #[test]
    fn the_bridge_never_asserts_install_progress() {
        // `installing` and `success` need the separately governed install
        // authority, so no observation this module can produce may claim them.
        let bridge = UpdateAdmissionBridge::new();
        assert!(!matches!(bridge.snapshot().unwrap().state, "installing" | "success"));
        bridge.record(Refusal::Failed(DOWNLOAD_FAILED));
        assert!(!matches!(bridge.snapshot().unwrap().state, "installing" | "success"));
        assert!(!expected_platform().unwrap().is_empty());
    }
}

