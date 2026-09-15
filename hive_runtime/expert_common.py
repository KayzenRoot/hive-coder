"""Shared types and hashing primitives for Hive expert agents."""
from __future__ import annotations
import hashlib
import json
import re
from enum import Enum

_SAFE_ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,128}$")
_SAFE_TOKEN = re.compile(r"^[a-zA-Z0-9_.:/+-]{1,160}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

def _sha(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

class ContextKind(str, Enum):
    SOURCE = "source"
    TEST = "test"
    ARCHITECTURE = "architecture"
    REQUIREMENT = "requirement"
    DECISION = "decision"
    RUNTIME = "runtime"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    HISTORY = "history"
    EXTERNAL = "external"


class BenchmarkDimension(str, Enum):
    REPOSITORY_REASONING = "repository_reasoning"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    CODE_REVIEW = "code_review"
    LONG_HORIZON = "long_horizon"
    TOOL_RELIABILITY = "tool_reliability"
    TAMPER_RESISTANCE = "tamper_resistance"


class CompetenceLevel(str, Enum):
    QUALIFIED = "qualified"
    SENIOR = "senior"
    PRINCIPAL = "principal"
    DISTINGUISHED = "distinguished"


class ChallengeKind(str, Enum):
    COUNTERPLAN = "counterplan"
    FAILURE_ORACLE = "failure_oracle"
