"""
Lexer for the small PHP expression grammar used by ``php_parser.py``.

Produces a flat list of ``Token`` objects for a single expression
fragment (the content that sits inside a Blade ``{{ }}`` / ``{!! !!}``
pair).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class TokType(Enum):
    STRING = auto()
    NUMBER = auto()
    VARIABLE = auto()
    IDENT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    DOUBLE_ARROW = auto()   # =>
    COLON_COLON = auto()    # ::
    ARROW = auto()          # ->
    DOT = auto()            # .
    QUESTION = auto()
    COLON = auto()
    EOF = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    type: TokType
    value: str
    pos: int


class LexError(Exception):
    pass


_IDENT_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_IDENT_CONT = _IDENT_START | set("0123456789")
_DIGITS = set("0123456789")


def tokenize(src: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(src)

    while i < n:
        c = src[i]

        if c.isspace():
            i += 1
            continue

        if c in ("'", '"'):
            start = i
            quote = c
            i += 1
            buf = []
            while i < n and src[i] != quote:
                if src[i] == "\\" and i + 1 < n:
                    nxt = src[i + 1]
                    if quote == "'" and nxt in ("'", "\\"):
                        buf.append(nxt)
                        i += 2
                        continue
                    if quote == '"' and nxt in ('"', "\\", "n", "t", "r", "$"):
                        mapping = {"n": "\n", "t": "\t", "r": "\r", "$": "$"}
                        buf.append(mapping.get(nxt, nxt))
                        i += 2
                        continue
                    buf.append(src[i])
                    i += 1
                    continue
                buf.append(src[i])
                i += 1
            if i >= n:
                raise LexError(f"Unterminated string starting at {start}")
            i += 1  # closing quote
            tokens.append(Token(TokType.STRING, "".join(buf), start))
            continue

        if c == "$":
            start = i
            i += 1
            while i < n and src[i] in _IDENT_CONT:
                i += 1
            tokens.append(Token(TokType.VARIABLE, src[start:i], start))
            continue

        if c in _DIGITS:
            start = i
            while i < n and (src[i] in _DIGITS or src[i] == "."):
                i += 1
            tokens.append(Token(TokType.NUMBER, src[start:i], start))
            continue

        if c in _IDENT_START:
            start = i
            while i < n and src[i] in _IDENT_CONT:
                i += 1
            tokens.append(Token(TokType.IDENT, src[start:i], start))
            continue

        if src.startswith("=>", i):
            tokens.append(Token(TokType.DOUBLE_ARROW, "=>", i))
            i += 2
            continue

        if src.startswith("::", i):
            tokens.append(Token(TokType.COLON_COLON, "::", i))
            i += 2
            continue

        if src.startswith("->", i):
            tokens.append(Token(TokType.ARROW, "->", i))
            i += 2
            continue

        if c == "(":
            tokens.append(Token(TokType.LPAREN, c, i)); i += 1; continue
        if c == ")":
            tokens.append(Token(TokType.RPAREN, c, i)); i += 1; continue
        if c == "[":
            tokens.append(Token(TokType.LBRACKET, c, i)); i += 1; continue
        if c == "]":
            tokens.append(Token(TokType.RBRACKET, c, i)); i += 1; continue
        if c == ",":
            tokens.append(Token(TokType.COMMA, c, i)); i += 1; continue
        if c == ".":
            tokens.append(Token(TokType.DOT, c, i)); i += 1; continue
        if c == "?":
            tokens.append(Token(TokType.QUESTION, c, i)); i += 1; continue
        if c == ":":
            tokens.append(Token(TokType.COLON, c, i)); i += 1; continue

        # Unknown character (operators like +, -, ==, etc.) - emit as UNKNOWN
        # so the parser can fall back to Raw() reconstruction.
        tokens.append(Token(TokType.UNKNOWN, c, i))
        i += 1

    tokens.append(Token(TokType.EOF, "", n))
    return tokens
