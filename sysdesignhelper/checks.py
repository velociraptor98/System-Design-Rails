"""Evaluates a Question's Checks against a Design.

A rule is a mapping with exactly one of these keys:

    has_block:      {<selector>}
    each_block:     {where: {<selector>}, require: {<selector>}}
    has_connection: {from: {<selector>}, to: {<selector>}, where: {<matchers>}}
    no_connection:  {from: {<selector>}, to: {<selector>}}
    has_path:       {from: {<selector>}, to: {<selector>}, via: {<selector>}}
    all_of / any_of: [<rule>, ...]

A selector maps Block properties to matchers; `extras.<key>` reaches into a
Block's extras. A matcher is a scalar (equality, case-insensitive for text),
a list (any of), or a mapping using gte / lte / ne / present.
"""
from __future__ import annotations

from dataclasses import dataclass

from .content import Check
from .design import Block, Connection, Design


class RuleError(Exception):
    pass


@dataclass(frozen=True)
class CheckResult:
    check: Check
    passed: bool


def run_checks(checks, design: Design) -> list[CheckResult]:
    return [CheckResult(check=check, passed=evaluate(check.rule, design)) for check in checks]


def evaluate(rule: dict, design: Design) -> bool:
    if len(rule) != 1:
        raise RuleError(f"a rule must have exactly one key, got {sorted(rule)}")
    (kind, body), = rule.items()
    if kind == "all_of":
        return all(evaluate(child, design) for child in body)
    if kind == "any_of":
        return any(evaluate(child, design) for child in body)
    if kind == "has_block":
        return bool(_select(design, body))
    if kind == "each_block":
        # An empty selection fails: "every database is replicated" should not
        # pass on a Design that has no database at all.
        selected = _select(design, body["where"])
        return bool(selected) and all(_block_matches(b, body["require"]) for b in selected)
    if kind == "has_connection":
        return bool(_connections(design, body))
    if kind == "no_connection":
        return not _connections(design, body)
    if kind == "has_path":
        return _has_path(design, body)
    raise RuleError(f"unknown rule {kind!r}")


def _select(design: Design, selector: dict) -> list[Block]:
    return [b for b in design.blocks if _block_matches(b, selector)]


def _block_matches(block: Block, selector: dict) -> bool:
    for key, matcher in selector.items():
        if key.startswith("extras."):
            value = block.extras.get(key.removeprefix("extras."), "")
        elif hasattr(block, key) and key not in ("extras", "id", "x", "y"):
            value = getattr(block, key)
        else:
            raise RuleError(f"unknown block property {key!r}")
        if not _matches(value, matcher):
            return False
    return True


def _connection_matches(connection: Connection, where: dict) -> bool:
    for key, matcher in where.items():
        if key not in ("mode", "protocol", "path", "label"):
            raise RuleError(f"unknown connection property {key!r}")
        if not _matches(getattr(connection, key), matcher):
            return False
    return True


def _connections(design: Design, body: dict) -> list[Connection]:
    sources = {b.id for b in _select(design, body["from"])}
    targets = {b.id for b in _select(design, body["to"])}
    where = body.get("where", {})
    return [
        c for c in design.connections
        if c.source in sources and c.target in targets and _connection_matches(c, where)
    ]


def _has_path(design: Design, body: dict) -> bool:
    sources = {b.id for b in _select(design, body["from"])}
    targets = {b.id for b in _select(design, body["to"])}
    if "via" not in body:
        return bool(_reachable(design, sources) & targets)
    via = {b.id for b in _select(design, body["via"])}
    reached_via = _reachable(design, sources) & via
    return bool(_reachable(design, reached_via) & targets)


def _reachable(design: Design, start: set[str]) -> set[str]:
    """Blocks reachable from `start` by following one or more Connections."""
    seen: set[str] = set()
    frontier = list(start)
    while frontier:
        current = frontier.pop()
        for connection in design.connections:
            if connection.source == current and connection.target not in seen:
                seen.add(connection.target)
                frontier.append(connection.target)
    return seen


def _matches(value, matcher) -> bool:
    if isinstance(matcher, dict):
        for op, operand in matcher.items():
            if op == "gte":
                ok = value >= operand
            elif op == "lte":
                ok = value <= operand
            elif op == "ne":
                ok = not _equal(value, operand)
            elif op == "present":
                ok = bool(str(value).strip()) == bool(operand)
            else:
                raise RuleError(f"unknown matcher {op!r}")
            if not ok:
                return False
        return True
    if isinstance(matcher, list):
        return any(_equal(value, option) for option in matcher)
    return _equal(value, matcher)


def _equal(value, expected) -> bool:
    if isinstance(value, str) and isinstance(expected, str):
        return value.strip().casefold() == expected.strip().casefold()
    return value == expected
