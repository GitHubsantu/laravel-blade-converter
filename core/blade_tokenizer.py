"""
Splits a full Blade template into a linear list of segments so the
converter only ever attempts to interpret the parts that can actually
contain a LaravelCollective call: ``{{ ... }}`` and ``{!! ... !!}``
echo blocks. Everything else -- plain HTML, ``@directive`` blocks,
PHP ``@php`` sections and ``{{-- comments --}}`` -- is preserved
byte-for-byte.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class SegmentType(Enum):
    RAW = auto()
    ECHO = auto()          # {{ expr }}
    RAW_ECHO = auto()       # {!! expr !!}
    COMMENT = auto()        # {{-- ... --}}


@dataclass
class Segment:
    type: SegmentType
    text: str        # verbatim original text including delimiters
    expr: str = ""    # inner expression (only for ECHO / RAW_ECHO)


def tokenize_blade(content: str) -> List[Segment]:
    segments: List[Segment] = []
    i = 0
    n = len(content)
    raw_start = 0

    def flush_raw(end: int) -> None:
        if end > raw_start:
            segments.append(Segment(SegmentType.RAW, content[raw_start:end]))

    while i < n:
        if content.startswith("{{--", i):
            end = content.find("--}}", i)
            if end == -1:
                break
            end += len("--}}")
            flush_raw(i)
            segments.append(Segment(SegmentType.COMMENT, content[i:end]))
            i = end
            raw_start = i
            continue

        if content.startswith("{!!", i):
            end = content.find("!!}", i)
            if end == -1:
                break
            expr = content[i + 3:end]
            end += len("!!}")
            flush_raw(i)
            segments.append(Segment(SegmentType.RAW_ECHO, content[i:end], expr))
            i = end
            raw_start = i
            continue

        if content.startswith("{{", i) and not content.startswith("{{--", i):
            end = content.find("}}", i)
            if end == -1:
                break
            expr = content[i + 2:end]
            end += len("}}")
            flush_raw(i)
            segments.append(Segment(SegmentType.ECHO, content[i:end], expr))
            i = end
            raw_start = i
            continue

        i += 1

    flush_raw(n)
    return segments


def rebuild(segments: List[Segment]) -> str:
    return "".join(seg.text for seg in segments)
