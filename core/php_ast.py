"""
A minimal AST for the subset of PHP expression syntax that appears
inside Blade echo statements ``{{ ... }}`` / ``{!! ... !!}`` when using
LaravelCollective helpers, e.g.::

    Form::text('name', null, ['class' => 'form-control', 'id' => 'x'])
    link_to_route('posts.show', 'View', ['id' => $post->id], ['class' => 'btn'])

This is intentionally NOT a full PHP parser. It understands just enough
grammar to statically resolve literal strings, numbers, booleans, null
and (nested) arrays, while gracefully degrading to a ``Raw`` node for
anything dynamic (variables, method chains, ternaries, concatenation,
nested function calls) so that dynamic content is preserved verbatim
in the converted output instead of being silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union


class Value:
    """Base class for all expression nodes."""

    def is_literal(self) -> bool:
        return False


@dataclass
class StringLit(Value):
    value: str

    def is_literal(self) -> bool:
        return True


@dataclass
class NumberLit(Value):
    value: str  # kept as text to preserve int/float formatting

    def is_literal(self) -> bool:
        return True


@dataclass
class BoolLit(Value):
    value: bool

    def is_literal(self) -> bool:
        return True


@dataclass
class NullLit(Value):
    def is_literal(self) -> bool:
        return True


@dataclass
class ArrayLit(Value):
    # Each item is (key_or_None, value). key is a Value (usually StringLit)
    items: List[Tuple[Optional[Value], Value]] = field(default_factory=list)


@dataclass
class VarRef(Value):
    name: str  # includes leading '$'
    # optional chain of ->prop / ->method(...) / [index] accesses, stored as raw text
    trailer: str = ""


@dataclass
class FuncCall(Value):
    name: str
    args: List[Value] = field(default_factory=list)


@dataclass
class StaticCall(Value):
    class_name: str
    method: str
    args: List[Value] = field(default_factory=list)


@dataclass
class Raw(Value):
    """Fallback: original source text for anything we can't/won't statically evaluate."""
    text: str


def to_php_source(value: Value) -> str:
    """Render a Value back to PHP-ish source text (used when we must re-embed
    a sub-expression we couldn't fully resolve, e.g. inside an attribute)."""
    if isinstance(value, StringLit):
        escaped = value.value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(value, NumberLit):
        return value.value
    if isinstance(value, BoolLit):
        return "true" if value.value else "false"
    if isinstance(value, NullLit):
        return "null"
    if isinstance(value, ArrayLit):
        parts = []
        for k, v in value.items:
            if k is None:
                parts.append(to_php_source(v))
            else:
                parts.append(f"{to_php_source(k)} => {to_php_source(v)}")
        return "[" + ", ".join(parts) + "]"
    if isinstance(value, VarRef):
        return value.name + value.trailer
    if isinstance(value, FuncCall):
        return f"{value.name}(" + ", ".join(to_php_source(a) for a in value.args) + ")"
    if isinstance(value, StaticCall):
        return f"{value.class_name}::{value.method}(" + ", ".join(
            to_php_source(a) for a in value.args
        ) + ")"
    if isinstance(value, Raw):
        return value.text
    return ""
