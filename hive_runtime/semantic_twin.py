"""Hive Semantic Repository Twin.

Static repository semantics are descriptive evidence only. This module never imports or
executes indexed repository code and never grants authority.
"""
from __future__ import annotations

import ast
import json
import tomllib
from dataclasses import dataclass
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Iterable, Mapping

from .expert_common import _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha
from .repository_intelligence import IndexedRepository


@dataclass(frozen=True)
class SemanticNode:
    node_id: str
    kind: str
    path: str
    label_digest: str
    tags: frozenset[str] = frozenset()

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.node_id) or not _SAFE_TOKEN.fullmatch(self.kind):
            raise ValueError("invalid semantic node identity")
        if not self.path or self.path.startswith("/") or ".." in PurePosixPath(self.path).parts:
            raise ValueError("invalid semantic node path")
        if not _SHA256.fullmatch(self.label_digest):
            raise ValueError("semantic node label must be sha256")
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in self.tags):
            raise ValueError("invalid semantic node tag")


@dataclass(frozen=True)
class SemanticEdge:
    edge_id: str
    source: str
    target: str
    relation: str
    provenance_digest: str
    path: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.edge_id) or not _SAFE_ID.fullmatch(self.source) or not _SAFE_ID.fullmatch(self.target):
            raise ValueError("invalid semantic edge identity")
        if not _SAFE_TOKEN.fullmatch(self.relation) or not _SHA256.fullmatch(self.provenance_digest):
            raise ValueError("invalid semantic edge relation/provenance")
        if not self.path or self.path.startswith("/") or ".." in PurePosixPath(self.path).parts:
            raise ValueError("invalid semantic edge path")


@dataclass(frozen=True)
class SchemaObservation:
    schema_id: str
    path: str
    property_digests: tuple[str, ...]
    source_digest: str


class SchemaSense:
    """Static JSON/TOML schema-shape observations. No validation code is executed."""

    VERSION = "schemasense-v1"

    def observe(self, path: str, text: str) -> tuple[SchemaObservation, ...]:
        name = PurePosixPath(path).name.lower()
        payload: object
        try:
            if name.endswith(".json"):
                payload = json.loads(text)
            elif name.endswith(".toml"):
                payload = tomllib.loads(text)
            else:
                return tuple()
        except (json.JSONDecodeError, tomllib.TOMLDecodeError, TypeError, ValueError):
            return tuple()
        if not isinstance(payload, dict):
            return tuple()
        is_schema = "$schema" in payload or "properties" in payload or name.endswith("schema.json")
        if not is_schema:
            return tuple()
        props = payload.get("properties", {})
        keys = sorted(str(key) for key in props) if isinstance(props, dict) else []
        source_digest = _sha({"technology": self.VERSION, "path": path, "payload": payload})
        schema_id = f"schema.{source_digest[:28]}"
        return (SchemaObservation(schema_id, path, tuple(_sha({"property": key}) for key in keys), source_digest),)


@dataclass(frozen=True)
class RouteObservation:
    route_id: str
    path: str
    method: str
    function_digest: str
    route_digest: str


class APIVein:
    """Static Python decorator route observations for common HTTP-style decorators."""

    VERSION = "apivein-v1"
    METHODS = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})

    def observe(self, path: str, tree: ast.AST) -> tuple[RouteObservation, ...]:
        found: list[RouteObservation] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            function_digest = _sha({"path": path, "function": node.name, "line": node.lineno})
            for decorator in node.decorator_list:
                call = decorator if isinstance(decorator, ast.Call) else None
                target = call.func if call is not None else decorator
                method = target.attr.lower() if isinstance(target, ast.Attribute) else ""
                if method not in self.METHODS:
                    continue
                literal = "unknown"
                if call is not None and call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                    literal = call.args[0].value
                route_digest = _sha({
                    "technology": self.VERSION, "path": path, "method": method,
                    "route": literal, "function": function_digest,
                })
                found.append(RouteObservation(f"route.{route_digest[:28]}", path, method, function_digest, route_digest))
        return tuple(sorted(found, key=lambda item: item.route_id))


@dataclass(frozen=True)
class FlowObservation:
    flow_id: str
    path: str
    function_digest: str
    variable_digest: str
    mode: str


class DataflowEcho:
    """Conservative local Python read/write observations, not dynamic taint analysis."""

    VERSION = "dataflow-echo-v1"

    def observe(self, path: str, tree: ast.AST) -> tuple[FlowObservation, ...]:
        result: list[FlowObservation] = []
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            function_digest = _sha({"path": path, "function": function.name, "line": function.lineno})
            modes: set[tuple[str, str]] = set()
            for node in ast.walk(function):
                if isinstance(node, ast.Name):
                    mode = "write" if isinstance(node.ctx, ast.Store) else "read" if isinstance(node.ctx, ast.Load) else "other"
                    if mode != "other":
                        modes.add((node.id, mode))
            for variable, mode in sorted(modes):
                variable_digest = _sha({"variable": variable})
                flow_digest = _sha({
                    "technology": self.VERSION, "path": path, "function": function_digest,
                    "variable": variable_digest, "mode": mode,
                })
                result.append(FlowObservation(f"flow.{flow_digest[:28]}", path, function_digest, variable_digest, mode))
        return tuple(result)


def _node_id(prefix: str, payload: object) -> str:
    return f"{prefix}.{_sha(payload)[:28]}"


class SemanticRepositoryTwin:
    VERSION = "semantic-twin-v1"

    def __init__(self, repository_snapshot_digest: str, nodes: Iterable[SemanticNode], edges: Iterable[SemanticEdge]) -> None:
        if not _SHA256.fullmatch(repository_snapshot_digest):
            raise ValueError("semantic twin repository snapshot must be sha256")
        node_map: dict[str, SemanticNode] = {}
        for node in nodes:
            node.validate()
            if node.node_id in node_map:
                raise ValueError("duplicate semantic node")
            node_map[node.node_id] = node
        if not node_map:
            raise ValueError("semantic twin requires nodes")
        edge_map: dict[str, SemanticEdge] = {}
        for edge in edges:
            edge.validate()
            if edge.edge_id in edge_map:
                raise ValueError("duplicate semantic edge")
            if edge.source not in node_map or edge.target not in node_map:
                raise ValueError("semantic edge references unknown node")
            edge_map[edge.edge_id] = edge
        self.repository_snapshot_digest = repository_snapshot_digest
        self.nodes: Mapping[str, SemanticNode] = MappingProxyType(dict(sorted(node_map.items())))
        self.edges: Mapping[str, SemanticEdge] = MappingProxyType(dict(sorted(edge_map.items())))

    def fingerprint(self) -> str:
        return _sha({
            "version": self.VERSION,
            "repository": self.repository_snapshot_digest,
            "nodes": [
                {"id": node.node_id, "kind": node.kind, "path": node.path,
                 "label": node.label_digest, "tags": sorted(node.tags)}
                for node in self.nodes.values()
            ],
            "edges": [
                {"id": edge.edge_id, "source": edge.source, "target": edge.target,
                 "relation": edge.relation, "provenance": edge.provenance_digest, "path": edge.path}
                for edge in self.edges.values()
            ],
        })

    def nodes_by_kind(self, kind: str) -> tuple[SemanticNode, ...]:
        return tuple(node for node in self.nodes.values() if node.kind == kind)


class SemanticTwinBuilder:
    """Static evidence compiler for RepoDNA content."""

    VERSION = "semantic-builder-v1"

    def __init__(self, schema_sense: SchemaSense | None = None,
                 api_vein: APIVein | None = None, dataflow_echo: DataflowEcho | None = None) -> None:
        self.schema_sense = schema_sense or SchemaSense()
        self.api_vein = api_vein or APIVein()
        self.dataflow_echo = dataflow_echo or DataflowEcho()

    def build(self, indexed: IndexedRepository) -> SemanticRepositoryTwin:
        indexed.validate()
        snapshot_digest = indexed.snapshot.fingerprint()
        nodes: dict[str, SemanticNode] = {}
        edges: dict[str, SemanticEdge] = {}

        def add_node(kind: str, path: str, label_payload: object, tags: Iterable[str] = ()) -> str:
            node_id = _node_id(kind, {"path": path, "label": label_payload})
            node = SemanticNode(node_id, kind, path, _sha(label_payload), frozenset(tags))
            existing = nodes.get(node_id)
            if existing is not None and existing != node:
                raise RuntimeError("semantic node hash collision")
            nodes[node_id] = node
            return node_id

        def add_edge(source: str, target: str, relation: str, path: str, payload: object) -> None:
            provenance = _sha({"technology": self.VERSION, "snapshot": snapshot_digest, "path": path, "payload": payload})
            edge_id = _node_id("edge", {"source": source, "target": target, "relation": relation, "provenance": provenance})
            edge = SemanticEdge(edge_id, source, target, relation, provenance, path)
            existing = edges.get(edge_id)
            if existing is not None and existing != edge:
                raise RuntimeError("semantic edge hash collision")
            edges[edge_id] = edge

        by_path = {record.path: record for record in indexed.snapshot.files}
        for path in sorted(indexed.texts):
            record = by_path[path]
            file_node = add_node("file", path, {"digest": record.content_digest}, {f"language:{record.language}", f"kind:{record.kind}"})
            text = indexed.texts[path]
            if record.language == "python":
                try:
                    tree = ast.parse(text, filename=path)
                except SyntaxError:
                    add_node("parse_error", path, {"file": record.content_digest}, {"language:python"})
                    continue
                module_node = add_node("module", path, {"path": path}, {"language:python"})
                add_edge(file_node, module_node, "defines", path, {"kind": "module"})
                symbol_by_name: dict[str, str] = {}
                for top in getattr(tree, "body", []):
                    if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        kind = "class" if isinstance(top, ast.ClassDef) else "function"
                        symbol = add_node("symbol", path, {"kind": kind, "name": top.name, "line": top.lineno}, {f"symbol:{kind}", "language:python"})
                        symbol_by_name[top.name] = symbol
                        add_edge(module_node, symbol, "contains", path, {"name": top.name, "line": top.lineno})
                imports: set[str] = set()
                for item in ast.walk(tree):
                    if isinstance(item, ast.Import):
                        imports.update(alias.name.split(".", 1)[0] for alias in item.names)
                    elif isinstance(item, ast.ImportFrom) and item.module:
                        imports.add(item.module.split(".", 1)[0])
                for imported in sorted(imports):
                    dependency = add_node("dependency", path, {"module": imported}, {"language:python"})
                    add_edge(module_node, dependency, "imports", path, {"module": imported})
                for function in ast.walk(tree):
                    if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    source = symbol_by_name.get(function.name) or add_node("symbol", path, {"kind": "nested-function", "name": function.name, "line": function.lineno}, {"symbol:function", "language:python"})
                    calls: set[str] = set()
                    for item in ast.walk(function):
                        if isinstance(item, ast.Call):
                            if isinstance(item.func, ast.Name):
                                calls.add(item.func.id)
                            elif isinstance(item.func, ast.Attribute):
                                calls.add(item.func.attr)
                    for call_name in sorted(calls):
                        target = symbol_by_name.get(call_name) or add_node("symbol_ref", path, {"call": call_name}, {"language:python"})
                        add_edge(source, target, "calls", path, {"call": call_name})
                for route in self.api_vein.observe(path, tree):
                    route_node = add_node("route", path, {"route": route.route_digest}, {f"method:{route.method}", "api"})
                    add_edge(module_node, route_node, "exposes", path, {"route": route.route_digest})
                for flow in self.dataflow_echo.observe(path, tree):
                    function_node = add_node("flow_function", path, {"function": flow.function_digest}, {"dataflow"})
                    variable_node = add_node("data_symbol", path, {"variable": flow.variable_digest}, {"dataflow"})
                    relation = "writes" if flow.mode == "write" else "reads"
                    add_edge(function_node, variable_node, relation, path, {"flow": flow.flow_id})
            for schema in self.schema_sense.observe(path, text):
                schema_node = add_node("schema", path, {"schema": schema.source_digest}, {"schema"})
                add_edge(file_node, schema_node, "declares", path, {"schema": schema.schema_id})
                for prop in schema.property_digests:
                    prop_node = add_node("schema_property", path, {"property": prop}, {"schema"})
                    add_edge(schema_node, prop_node, "contains", path, {"property": prop})

        return SemanticRepositoryTwin(snapshot_digest, nodes.values(), edges.values())


class DependencyCortex:
    """Deterministic graph traversal over the semantic twin."""

    def __init__(self, twin: SemanticRepositoryTwin) -> None:
        self.twin = twin
        outgoing: dict[str, set[str]] = {node_id: set() for node_id in twin.nodes}
        incoming: dict[str, set[str]] = {node_id: set() for node_id in twin.nodes}
        for edge in twin.edges.values():
            outgoing[edge.source].add(edge.target)
            incoming[edge.target].add(edge.source)
        self._outgoing = {key: frozenset(value) for key, value in outgoing.items()}
        self._incoming = {key: frozenset(value) for key, value in incoming.items()}

    def impact(self, node_ids: Iterable[str], *, depth: int = 3, max_nodes: int = 500) -> frozenset[str]:
        roots = frozenset(node_ids)
        if not roots or not roots.issubset(self.twin.nodes):
            raise ValueError("Dependency Cortex roots must exist")
        if not 0 <= depth <= 20 or not 1 <= max_nodes <= 10_000:
            raise ValueError("invalid Dependency Cortex bound")
        seen = set(roots); frontier = set(roots)
        for _ in range(depth):
            nxt: set[str] = set()
            for node in sorted(frontier):
                nxt.update(self._incoming[node]); nxt.update(self._outgoing[node])
            nxt -= seen
            for node in sorted(nxt):
                if len(seen) >= max_nodes:
                    return frozenset(seen)
                seen.add(node)
            frontier = nxt
            if not frontier:
                break
        return frozenset(seen)


@dataclass(frozen=True)
class SemanticTwinDrift:
    added_nodes: tuple[str, ...]
    removed_nodes: tuple[str, ...]
    added_edges: tuple[str, ...]
    removed_edges: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(self.added_nodes or self.removed_nodes or self.added_edges or self.removed_edges)


def compare_semantic_twins(old: SemanticRepositoryTwin, new: SemanticRepositoryTwin) -> SemanticTwinDrift:
    old_nodes, new_nodes = set(old.nodes), set(new.nodes)
    old_edges, new_edges = set(old.edges), set(new.edges)
    return SemanticTwinDrift(
        tuple(sorted(new_nodes - old_nodes)), tuple(sorted(old_nodes - new_nodes)),
        tuple(sorted(new_edges - old_edges)), tuple(sorted(old_edges - new_edges)),
    )
