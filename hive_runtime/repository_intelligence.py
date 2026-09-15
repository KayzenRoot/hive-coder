"""Hive repository intelligence: RepoDNA, TruthWeave and GenomePulse.

The indexer is read-only and intentionally never imports or executes repository code.
Derived facts are descriptive evidence only and grant no execution authority.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Iterable, Mapping

from .expert_common import BenchmarkDimension, _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha
from .expert_context import ArchitecturalGenome, ArchitecturalInvariant, CodeTruthMap, TruthFact
from .orchestration import ProjectDigitalTwin


_LANGUAGE_BY_SUFFIX = {
    ".py": "python", ".pyi": "python", ".js": "javascript", ".mjs": "javascript",
    ".cjs": "javascript", ".ts": "typescript", ".tsx": "typescript", ".jsx": "javascript",
    ".rs": "rust", ".go": "go", ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".cs": "csharp", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c": "c",
    ".h": "c-header", ".hpp": "cpp-header", ".rb": "ruby", ".php": "php",
    ".swift": "swift", ".sql": "sql", ".sh": "shell", ".ps1": "powershell",
    ".json": "json", ".toml": "toml", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown",
}

_BINARY_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz",
    ".tar", ".7z", ".exe", ".dll", ".so", ".dylib", ".bin", ".woff", ".woff2",
    ".ttf", ".otf", ".mp3", ".wav", ".mp4", ".mov", ".avi", ".sqlite", ".db",
})

_DEFAULT_EXCLUDED_DIRS = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build",
    "target", ".mypy_cache", ".pytest_cache", "__pycache__", ".idea", ".vscode",
})

_SECRET_NAMES = frozenset({
    ".env", ".env.local", ".env.production", ".env.development", ".npmrc", ".pypirc",
    ".netrc", ".git-credentials", "credentials.json", "service-account.json",
    "service_account.json", "id_rsa", "id_ed25519",
})
_SECRET_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"})


def _content_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalized_relative(path: Path | str) -> str:
    raw = str(path).replace(os.sep, "/") if isinstance(path, Path) else str(path)
    if "\\" in raw:
        raise ValueError("repository path must use canonical forward slashes")
    normalized = PurePosixPath(raw)
    if (
        normalized.is_absolute() or not raw
        or any(part in ("", ".", "..") for part in normalized.parts)
        or (normalized.parts and ":" in normalized.parts[0])
    ):
        raise ValueError("repository path is not a safe relative path")
    return normalized.as_posix()


def _path_tag(path: str) -> str:
    return f"pathsha:{hashlib.sha256(path.encode()).hexdigest()[:20]}"


def _language_for(path: str) -> str:
    name = PurePosixPath(path).name.lower()
    if name == "dockerfile":
        return "dockerfile"
    if name in {"makefile", "gnumakefile"}:
        return "make"
    return _LANGUAGE_BY_SUFFIX.get(PurePosixPath(path).suffix.lower(), "text")


def _kind_for(path: str) -> str:
    lower = path.lower()
    name = PurePosixPath(lower).name
    if name in {"package.json", "pyproject.toml", "cargo.toml", "go.mod", "pom.xml"}:
        return "manifest"
    if lower.startswith("tests/") or "/tests/" in lower or name.startswith("test_") or name.endswith("_test.py"):
        return "test"
    if lower.startswith("docs/") or name.endswith(".md"):
        return "documentation"
    if name.startswith("dockerfile") or name in {"compose.yaml", "compose.yml"} or lower.startswith(".github/workflows/"):
        return "delivery"
    if PurePosixPath(lower).suffix in {".json", ".toml", ".yaml", ".yml"}:
        return "configuration"
    return "source"


@dataclass(frozen=True)
class RepositoryFileRecord:
    path: str
    content_digest: str
    size_bytes: int
    language: str
    kind: str

    def validate(self) -> None:
        if _normalized_relative(self.path) != self.path:
            raise ValueError("repository file path must already be canonical")
        if not _SHA256.fullmatch(self.content_digest):
            raise ValueError("repository file digest must be sha256")
        if not 0 <= self.size_bytes <= 100_000_000:
            raise ValueError("invalid repository file size")
        if not _SAFE_TOKEN.fullmatch(self.language) or not _SAFE_TOKEN.fullmatch(self.kind):
            raise ValueError("invalid repository file classification")


@dataclass(frozen=True)
class RepositorySnapshot:
    repository_id: str
    files: tuple[RepositoryFileRecord, ...]
    extractor_version: str = "repodna-v1"

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.repository_id) or not _SAFE_TOKEN.fullmatch(self.extractor_version):
            raise ValueError("invalid repository snapshot identity")
        if not self.files:
            raise ValueError("repository snapshot cannot be empty")
        paths: set[str] = set()
        for record in self.files:
            record.validate()
            if record.path in paths:
                raise ValueError("duplicate repository path")
            paths.add(record.path)
        if tuple(sorted(paths)) != tuple(record.path for record in self.files):
            raise ValueError("repository snapshot files must be path-sorted")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "repository_id": self.repository_id,
            "extractor_version": self.extractor_version,
            "files": [
                {"path": item.path, "digest": item.content_digest, "size": item.size_bytes,
                 "language": item.language, "kind": item.kind}
                for item in self.files
            ],
        })


@dataclass(frozen=True)
class IndexedRepository:
    snapshot: RepositorySnapshot
    texts: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "texts", MappingProxyType(dict(self.texts)))
        self.validate()

    def validate(self) -> None:
        self.snapshot.validate()
        if set(self.texts) != {item.path for item in self.snapshot.files}:
            raise ValueError("indexed repository text set differs from snapshot")
        by_path = {item.path: item for item in self.snapshot.files}
        for path, text in self.texts.items():
            if not isinstance(text, str):
                raise TypeError("indexed repository text must be unicode")
            if _content_sha(text.encode("utf-8")) != by_path[path].content_digest:
                raise ValueError("indexed repository text digest mismatch")


class RepoDNAIndexer:
    """Bounded read-only repository scanner. It never imports or executes indexed code."""

    def __init__(self, *, max_files: int = 20_000, max_total_bytes: int = 64_000_000,
                 max_file_bytes: int = 2_000_000,
                 excluded_dirs: Iterable[str] = _DEFAULT_EXCLUDED_DIRS) -> None:
        if not 1 <= max_files <= 500_000:
            raise ValueError("invalid RepoDNA file ceiling")
        if not 1_024 <= max_total_bytes <= 2_000_000_000:
            raise ValueError("invalid RepoDNA total-byte ceiling")
        if not 1_024 <= max_file_bytes <= max_total_bytes:
            raise ValueError("invalid RepoDNA per-file ceiling")
        self.max_files = max_files
        self.max_total_bytes = max_total_bytes
        self.max_file_bytes = max_file_bytes
        self.excluded_dirs = frozenset(excluded_dirs)
        if any(not item or "/" in item or "\\" in item for item in self.excluded_dirs):
            raise ValueError("RepoDNA excluded directories must be simple names")

    def _read_regular_file(self, candidate: Path, root_path: Path, relative: str) -> bytes | None:
        if candidate.is_symlink():
            return None
        try:
            candidate.resolve(strict=True).relative_to(root_path)
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"RepoDNA path escaped root: {relative}") from exc
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(candidate, flags)
        except OSError as exc:
            if candidate.is_symlink():
                return None
            raise RuntimeError(f"RepoDNA could not safely open file: {relative}") from exc
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                return None
            if metadata.st_size > self.max_file_bytes:
                raise RuntimeError(f"RepoDNA per-file ceiling exceeded: {relative}")
            with os.fdopen(fd, "rb", closefd=True) as handle:
                fd = -1
                data = handle.read(self.max_file_bytes + 1)
            if len(data) > self.max_file_bytes:
                raise RuntimeError(f"RepoDNA per-file ceiling exceeded while reading: {relative}")
            if len(data) != metadata.st_size:
                raise RuntimeError(f"repository file changed during RepoDNA scan: {relative}")
            return data
        finally:
            if fd >= 0:
                os.close(fd)

    def scan(self, root: str | os.PathLike[str], *, repository_id: str = "repository") -> IndexedRepository:
        supplied_root = Path(root)
        if supplied_root.is_symlink():
            raise ValueError("RepoDNA root symlink is not allowed")
        root_path = supplied_root.resolve(strict=True)
        if not root_path.is_dir():
            raise ValueError("RepoDNA root must be a directory")
        if not _SAFE_ID.fullmatch(repository_id):
            raise ValueError("invalid RepoDNA repository id")

        records: list[RepositoryFileRecord] = []
        texts: dict[str, str] = {}
        total_bytes = 0

        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True, followlinks=False):
            current = Path(dirpath)
            safe_dirs: list[str] = []
            for dirname in sorted(dirnames):
                child = current / dirname
                if dirname in self.excluded_dirs or child.is_symlink():
                    continue
                try:
                    child.resolve(strict=True).relative_to(root_path)
                except (OSError, ValueError):
                    continue
                safe_dirs.append(dirname)
            dirnames[:] = safe_dirs

            for filename in sorted(filenames):
                candidate = current / filename
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                relative = _normalized_relative(candidate.relative_to(root_path))
                lower_name = filename.lower()
                suffix = candidate.suffix.lower()
                if lower_name in _SECRET_NAMES or lower_name.startswith(".env.") or suffix in _SECRET_SUFFIXES:
                    continue
                if suffix in _BINARY_SUFFIXES:
                    continue
                data = self._read_regular_file(candidate, root_path, relative)
                if data is None or b"\x00" in data:
                    continue
                try:
                    text = data.decode("utf-8", errors="strict")
                except UnicodeDecodeError:
                    continue
                if len(records) + 1 > self.max_files:
                    raise RuntimeError("RepoDNA file-count ceiling exceeded")
                if total_bytes + len(data) > self.max_total_bytes:
                    raise RuntimeError("RepoDNA total-byte ceiling exceeded")
                total_bytes += len(data)
                record = RepositoryFileRecord(
                    relative, _content_sha(data), len(data), _language_for(relative), _kind_for(relative),
                )
                records.append(record)
                texts[relative] = text

        records.sort(key=lambda item: item.path)
        snapshot = RepositorySnapshot(repository_id, tuple(records))
        return IndexedRepository(snapshot, texts)


class TruthWeave:
    """Turns exact RepoDNA observations into facts verifiable against the same snapshot."""

    VERSION = "truthweave-v1"

    def __init__(self, indexed: IndexedRepository) -> None:
        indexed.validate()
        self.indexed = indexed
        self._facts = self._extract()
        self._fingerprints = MappingProxyType({fact.fact_id: fact.fingerprint() for fact in self._facts})

    def _fact(self, *, path: str, rule: str, predicate: str, object_digest: str,
              tags: Iterable[str], subject: str | None = None) -> TruthFact:
        record = next(item for item in self.indexed.snapshot.files if item.path == path)
        provenance = _sha({
            "technology": self.VERSION, "snapshot": self.indexed.snapshot.fingerprint(),
            "path": path, "file_digest": record.content_digest, "rule": rule,
            "predicate": predicate, "object": object_digest,
        })
        fact_id = f"repo.{hashlib.sha256((path + '|' + rule + '|' + object_digest).encode()).hexdigest()[:28]}"
        return TruthFact(
            fact_id=fact_id, subject=subject or path, predicate=predicate,
            object_digest=object_digest, provenance_digest=provenance, tags=frozenset(tags),
        )

    def _extract_python(self, path: str, text: str) -> list[TruthFact]:
        facts: list[TruthFact] = []
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as exc:
            facts.append(self._fact(
                path=path, rule="python.parse-error", predicate="parse_error",
                object_digest=_sha({"line": exc.lineno or 0, "offset": exc.offset or 0}),
                tags={"repository", "parse-error", "language:python", _path_tag(path)},
            ))
            return facts
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
        for module in sorted(imports):
            facts.append(self._fact(
                path=path, rule=f"python.import:{module}", predicate="imports",
                object_digest=_sha({"module": module}),
                tags={"repository", "dependency", "language:python", _path_tag(path)},
            ))
        return facts

    def _extract_manifest(self, path: str, text: str) -> list[TruthFact]:
        facts: list[TruthFact] = []
        name = PurePosixPath(path).name.lower()
        dependencies: dict[str, str] = {}
        try:
            if name == "package.json":
                payload = json.loads(text)
                for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    values = payload.get(field, {})
                    if isinstance(values, dict):
                        dependencies.update({str(k): str(v) for k, v in values.items()})
            elif name == "pyproject.toml":
                payload = tomllib.loads(text)
                project = payload.get("project", {})
                if isinstance(project, dict):
                    raw = project.get("dependencies", [])
                    if isinstance(raw, list):
                        for item in raw:
                            if isinstance(item, str) and item.strip():
                                dep = item.split(";", 1)[0].strip()
                                dependencies[dep] = dep
        except (json.JSONDecodeError, tomllib.TOMLDecodeError, TypeError, ValueError):
            facts.append(self._fact(
                path=path, rule="manifest.parse-error", predicate="manifest_parse_error",
                object_digest=_sha({"path": path}),
                tags={"repository", "manifest", "parse-error", _path_tag(path)},
            ))
            return facts
        for dependency, spec in sorted(dependencies.items()):
            facts.append(self._fact(
                path=path,
                rule=f"manifest.dependency:{hashlib.sha256(dependency.encode()).hexdigest()[:12]}",
                predicate="declares_dependency",
                object_digest=_sha({"dependency": dependency, "spec": spec}),
                tags={"repository", "manifest", "dependency", _path_tag(path)},
            ))
        return facts

    def _extract(self) -> tuple[TruthFact, ...]:
        facts: list[TruthFact] = []
        by_path = {item.path: item for item in self.indexed.snapshot.files}
        for path in sorted(self.indexed.texts):
            record = by_path[path]
            facts.append(self._fact(
                path=path, rule="file.present", predicate="file_content",
                object_digest=record.content_digest,
                tags={"repository", "file", f"kind:{record.kind}", f"language:{record.language}", _path_tag(path)},
            ))
            text = self.indexed.texts[path]
            if record.language == "python":
                facts.extend(self._extract_python(path, text))
            if record.kind == "manifest":
                facts.extend(self._extract_manifest(path, text))
        facts.sort(key=lambda fact: fact.fact_id)
        ids = [fact.fact_id for fact in facts]
        if len(ids) != len(set(ids)):
            raise RuntimeError("TruthWeave generated duplicate fact identity")
        return tuple(facts)

    def facts(self) -> tuple[TruthFact, ...]:
        return self._facts

    def verify(self, fact: TruthFact) -> bool:
        expected = self._fingerprints.get(fact.fact_id)
        if expected is None:
            return False
        try:
            return fact.fingerprint() == expected
        except ValueError:
            return False

    def truth_map(self) -> CodeTruthMap:
        return CodeTruthMap(self._facts, self.verify)


@dataclass(frozen=True)
class GenomePulseResult:
    genome: ArchitecturalGenome
    fact_to_invariants: Mapping[str, tuple[str, ...]]
    covered_nodes: tuple[str, ...]

    def __post_init__(self) -> None:
        frozen: dict[str, tuple[str, ...]] = {}
        for fact_id, invariant_ids in self.fact_to_invariants.items():
            if not _SAFE_ID.fullmatch(fact_id):
                raise ValueError("invalid GenomePulse fact id")
            values = tuple(invariant_ids)
            if not values or any(not _SAFE_ID.fullmatch(item) for item in values):
                raise ValueError("invalid GenomePulse invariant binding")
            frozen[fact_id] = tuple(sorted(set(values)))
        object.__setattr__(self, "fact_to_invariants", MappingProxyType(frozen))
        object.__setattr__(self, "covered_nodes", tuple(self.covered_nodes))


class GenomePulseMiner:
    """Mines evidence-bound repository-footprint invariants without model inference."""

    VERSION = "genomepulse-v1"

    def mine(self, twin: ProjectDigitalTwin, truth: CodeTruthMap,
             node_path_bindings: Mapping[str, str], *, critical_nodes: Iterable[str] = ()) -> GenomePulseResult:
        if not node_path_bindings:
            raise ValueError("GenomePulse requires node/path bindings")
        node_ids = frozenset(node_path_bindings)
        twin.validate_targets(node_ids)
        critical = frozenset(critical_nodes)
        if not critical.issubset(node_ids):
            raise ValueError("critical GenomePulse node is not bound")
        verified = truth.query((), verified_only=True)
        invariants: list[ArchitecturalInvariant] = []
        fact_to_invariants: dict[str, list[str]] = {}
        covered: list[str] = []
        for node_id in sorted(node_path_bindings):
            prefix = _normalized_relative(node_path_bindings[node_id].strip().strip("/"))
            selected = tuple(
                fact for fact in verified
                if fact.subject == prefix or fact.subject.startswith(prefix + "/")
            )
            if not selected:
                raise ValueError(f"GenomePulse node has no verified repository facts: {node_id}")
            fact_ids = frozenset(fact.fact_id for fact in selected)
            invariant_id = f"genome.{node_id}"
            statement_digest = _sha({
                "technology": self.VERSION, "node": node_id, "path_prefix": prefix,
                "facts": sorted((fact.fact_id, fact.fingerprint()) for fact in selected),
            })
            invariants.append(ArchitecturalInvariant(
                invariant_id, statement_digest, frozenset({node_id}), fact_ids, node_id in critical,
            ))
            covered.append(node_id)
            for fact_id in fact_ids:
                fact_to_invariants.setdefault(fact_id, []).append(invariant_id)
        genome = ArchitecturalGenome(twin, truth, invariants)
        return GenomePulseResult(
            genome,
            {key: tuple(sorted(value)) for key, value in sorted(fact_to_invariants.items())},
            tuple(covered),
        )


@dataclass(frozen=True)
class ExpertiseCapsuleExtension:
    """Descriptive language/framework specialization. It grants no authority or rank."""

    extension_id: str
    version: str
    base_capsule_fingerprint: str
    languages: frozenset[str]
    frameworks: frozenset[str]
    principles: tuple[str, ...]
    review_lenses: tuple[str, ...]
    benchmark_dimensions: frozenset[BenchmarkDimension]
    provenance_digest: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.extension_id) or not _SAFE_TOKEN.fullmatch(self.version):
            raise ValueError("invalid expertise extension identity")
        if not _SHA256.fullmatch(self.base_capsule_fingerprint) or not _SHA256.fullmatch(self.provenance_digest):
            raise ValueError("expertise extension digests must be sha256")
        if not self.languages and not self.frameworks:
            raise ValueError("expertise extension requires a language or framework")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.languages | self.frameworks):
            raise ValueError("invalid language/framework token")
        if not self.principles or not self.review_lenses or not self.benchmark_dimensions:
            raise ValueError("expertise extension requires doctrine and benchmark dimensions")
        if any(not item.strip() for item in self.principles + self.review_lenses):
            raise ValueError("expertise extension doctrine cannot be empty")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "id": self.extension_id, "version": self.version,
            "base": self.base_capsule_fingerprint,
            "languages": sorted(self.languages), "frameworks": sorted(self.frameworks),
            "principles": list(self.principles), "review_lenses": list(self.review_lenses),
            "benchmarks": sorted(item.value for item in self.benchmark_dimensions),
            "provenance": self.provenance_digest,
        })
