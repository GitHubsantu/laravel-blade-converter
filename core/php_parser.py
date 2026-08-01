"""
Recursive-descent parser that turns the token stream produced by
``php_lexer.tokenize`` into the AST defined in ``php_ast``.

Design goal: understand LaravelCollective-style calls and their literal
array arguments precisely, while *never crashing* on constructs outside
that subset (ternaries, concatenation, method chains, dynamic
variables). Anything unsupported degrades to ``Raw`` holding the
original source text for that sub-expression, so the caller can decide
to leave it untouched rather than risk corrupting the template.
"""

from __future__ import annotations

from typing import List, Optional

from .php_ast import (
    ArrayLit,
    BoolLit,
    FuncCall,
    NullLit,
    NumberLit,
    Raw,
    StaticCall,
    StringLit,
    Value,
    VarRef,
)
from .php_lexer import Token, TokType, tokenize

_OPEN_TYPES = {TokType.LPAREN, TokType.LBRACKET}
_CLOSE_TYPES = {TokType.RPAREN, TokType.RBRACKET}
_BOUNDARY_TYPES = {TokType.COMMA, TokType.RPAREN, TokType.RBRACKET, TokType.EOF}


class ParseError(Exception):
    pass


class _Parser:
    def __init__(self, tokens: List[Token], src: str):
        self.tokens = tokens
        self.src = src
        self.idx = 0

    def peek(self, offset: int = 0) -> Token:
        i = min(self.idx + offset, len(self.tokens) - 1)
        return self.tokens[i]

    def advance(self) -> Token:
        tok = self.tokens[self.idx]
        if self.idx < len(self.tokens) - 1:
            self.idx += 1
        return tok

    def expect(self, ttype: TokType) -> Token:
        tok = self.peek()
        if tok.type != ttype:
            raise ParseError(f"Expected {ttype} but found {tok.type} ('{tok.value}') at {tok.pos}")
        return self.advance()

    # ------------------------------------------------------------------
    # Raw fallback helper: scan forward (tracking bracket/paren depth)
    # until we hit a top-level boundary token, and return the verbatim
    # source slice as a Raw() node without crashing the parser.
    # ------------------------------------------------------------------
    def _raw_until_boundary(self, start_pos: int) -> Raw:
        depth = 0
        while True:
            tok = self.peek()
            if depth == 0 and tok.type in _BOUNDARY_TYPES:
                end_pos = tok.pos
                text = self.src[start_pos:end_pos].strip()
                return Raw(text)
            if tok.type in _OPEN_TYPES:
                depth += 1
            elif tok.type in _CLOSE_TYPES:
                depth -= 1
            if tok.type == TokType.EOF:
                end_pos = tok.pos
                text = self.src[start_pos:end_pos].strip()
                return Raw(text)
            self.advance()

    # ------------------------------------------------------------------
    # Expression / value grammar
    # ------------------------------------------------------------------
    def parse_expression(self) -> Value:
        start_pos = self.peek().pos
        value = self.parse_primary(start_pos)
        nxt = self.peek()
        if nxt.type in (TokType.DOT, TokType.QUESTION, TokType.UNKNOWN):
            # Concatenation / ternary / unsupported operator: bail out to Raw
            # so we don't misinterpret dynamic PHP as something it isn't.
            self.idx = self._index_at(start_pos)
            return self._raw_until_boundary(start_pos)
        return value

    def _index_at(self, pos: int) -> int:
        for i, tok in enumerate(self.tokens):
            if tok.pos == pos:
                return i
        return self.idx

    def parse_primary(self, start_pos: int) -> Value:
        tok = self.peek()

        if tok.type == TokType.STRING:
            self.advance()
            return StringLit(tok.value)

        if tok.type == TokType.NUMBER:
            self.advance()
            return NumberLit(tok.value)

        if tok.type == TokType.VARIABLE:
            self.advance()
            trailer = self._consume_trailer()
            if trailer:
                return Raw((tok.value + trailer).strip())
            return VarRef(tok.value)

        if tok.type == TokType.LBRACKET:
            return self.parse_array_short()

        if tok.type == TokType.LPAREN:
            self.advance()
            inner = self.parse_expression()
            if self.peek().type == TokType.RPAREN:
                self.advance()
            return inner

        if tok.type == TokType.IDENT:
            lowered = tok.value.lower()
            if lowered == "true":
                self.advance()
                return BoolLit(True)
            if lowered == "false":
                self.advance()
                return BoolLit(False)
            if lowered == "null":
                self.advance()
                return NullLit()
            if lowered == "array" and self.peek(1).type == TokType.LPAREN:
                self.advance()  # 'array'
                self.advance()  # '('
                items = self._parse_array_items(TokType.RPAREN)
                if self.peek().type == TokType.RPAREN:
                    self.advance()
                return ArrayLit(items)

            # Class::method(...) or bareFunc(...)
            if self.peek(1).type == TokType.COLON_COLON:
                class_name = tok.value
                self.advance()  # ident
                self.advance()  # ::
                method_tok = self.expect(TokType.IDENT)
                if self.peek().type != TokType.LPAREN:
                    return Raw(self.src[start_pos:].strip())
                self.advance()  # (
                args = self._parse_args()
                if self.peek().type == TokType.RPAREN:
                    self.advance()
                return StaticCall(class_name, method_tok.value, args)

            if self.peek(1).type == TokType.LPAREN:
                func_name = tok.value
                self.advance()  # ident
                self.advance()  # (
                args = self._parse_args()
                if self.peek().type == TokType.RPAREN:
                    self.advance()
                return FuncCall(func_name, args)

            # Bare constant/identifier we don't specifically model.
            self.advance()
            return Raw(tok.value)

        # Anything else (unknown operator, unexpected token): raw fallback.
        return self._raw_until_boundary(start_pos)

    def _consume_trailer(self) -> str:
        """Consume ->prop / ->method(...) / [expr] chains after a variable
        and return their verbatim source text (empty string if none)."""
        start_idx = self.idx
        if self.peek().type not in (TokType.ARROW, TokType.LBRACKET):
            return ""
        start_pos = self.peek().pos
        depth = 0
        while True:
            tok = self.peek()
            if depth == 0 and tok.type in (
                TokType.COMMA,
                TokType.EOF,
                TokType.DOUBLE_ARROW,
                TokType.RPAREN,
                TokType.RBRACKET,
            ):
                break
            if tok.type in _OPEN_TYPES:
                depth += 1
                self.advance()
                continue
            if tok.type in _CLOSE_TYPES:
                depth -= 1
                self.advance()
                continue
            if depth == 0 and tok.type not in (
                TokType.ARROW,
                TokType.IDENT,
                TokType.LPAREN,
                TokType.LBRACKET,
                TokType.STRING,
                TokType.NUMBER,
                TokType.VARIABLE,
                TokType.DOT,
            ):
                break
            self.advance()
        end_pos = self.peek().pos
        return self.src[start_pos:end_pos]

    def parse_array_short(self) -> ArrayLit:
        self.expect(TokType.LBRACKET)
        items = self._parse_array_items(TokType.RBRACKET)
        if self.peek().type == TokType.RBRACKET:
            self.advance()
        return ArrayLit(items)

    def _parse_array_items(self, closing: TokType):
        items = []
        while self.peek().type not in (closing, TokType.EOF):
            key_or_val = self.parse_expression()
            if self.peek().type == TokType.DOUBLE_ARROW:
                self.advance()
                val = self.parse_expression()
                items.append((key_or_val, val))
            else:
                items.append((None, key_or_val))
            if self.peek().type == TokType.COMMA:
                self.advance()
                continue
            break
        return items

    def _parse_args(self) -> List[Value]:
        args: List[Value] = []
        while self.peek().type not in (TokType.RPAREN, TokType.EOF):
            args.append(self.parse_expression())
            if self.peek().type == TokType.COMMA:
                self.advance()
                continue
            break
        return args


def parse_value(src: str) -> Value:
    """Parse a single PHP expression fragment (the inside of a Blade echo)."""
    src = src.strip()
    tokens = tokenize(src)
    parser = _Parser(tokens, src)
    try:
        value = parser.parse_expression()
    except ParseError:
        return Raw(src)
    if parser.peek().type != TokType.EOF:
        return Raw(src)
    return value
