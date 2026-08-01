"""
BladeFormatter: a heuristic, line-based re-indenter for the mixed
HTML/Blade output produced by ConverterEngine.

This intentionally does NOT re-parse or rewrite the content itself
(so comments, spacing inside literal text, and Blade directives are
preserved exactly) -- it only recomputes leading whitespace on each
line based on a simple open/close tag & directive stack. This mirrors
how a "beautify" pass in an editor like VS Code's HTML formatter
behaves for hand-written Blade templates.
"""

from __future__ import annotations

import re
from typing import List

_BLOCK_OPEN_DIRECTIVES = re.compile(
    r"^@(if|unless|foreach|forelse|for|while|switch|section|component|slot|push|prepend|"
    r"once|auth|guest|can|cannot|canany|env|production|isset|empty|error)\b"
)
_BLOCK_CONTINUE_DIRECTIVES = re.compile(r"^@(else|elseif|empty|break|continue|default|case)\b")
_BLOCK_CLOSE_DIRECTIVES = re.compile(
    r"^@(endif|endunless|endforeach|endforelse|endfor|endwhile|endswitch|endsection|"
    r"endcomponent|endslot|endpush|endprepend|endonce|endauth|endguest|endcan|"
    r"endcannot|endcanany|endenv|endproduction|endisset|endempty|endempty|enderror|stop|show|overwrite)\b"
)

_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

_TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9:-]*)([^>]*?)(/?)>")


class BladeFormatter:
    def __init__(self, indent_size: int = 4, use_tabs: bool = False):
        self.indent_size = indent_size
        self.use_tabs = use_tabs

    def _indent_unit(self) -> str:
        return "\t" if self.use_tabs else " " * self.indent_size

    def format(self, content: str) -> str:
        lines = content.split("\n")
        out: List[str] = []
        depth = 0

        for raw_line in lines:
            stripped = raw_line.strip()
            if stripped == "":
                out.append("")
                continue

            this_line_depth = depth
            leading_closers = self._count_leading_closers(stripped)
            this_line_depth = max(0, depth - leading_closers)

            indent = self._indent_unit() * this_line_depth
            out.append(indent + stripped)

            depth = max(0, depth - leading_closers)
            depth += self._net_depth_change(stripped)

        return "\n".join(out)

    # ------------------------------------------------------------------
    def _count_leading_closers(self, line: str) -> int:
        if _BLOCK_CLOSE_DIRECTIVES.match(line):
            return 1
        if _BLOCK_CONTINUE_DIRECTIVES.match(line):
            return 1
        if line.startswith("</"):
            return 1
        if line == "</form>":
            return 1
        return 0

    def _net_depth_change(self, line: str) -> int:
        depth_change = 0

        if _BLOCK_OPEN_DIRECTIVES.match(line):
            depth_change += 1
        elif _BLOCK_CONTINUE_DIRECTIVES.match(line):
            depth_change += 1
        elif _BLOCK_CLOSE_DIRECTIVES.match(line):
            depth_change -= 1
            depth_change += 0  # already handled via leading closer

        for match in _TAG_RE.finditer(line):
            is_close, tag, attrs, self_close = match.groups()
            tag_lower = tag.lower()
            if tag_lower in _VOID_TAGS or self_close == "/":
                continue
            if is_close:
                depth_change -= 1
            else:
                depth_change += 1

        return depth_change

    def beautify_html_fragment(self, fragment: str) -> str:
        """Format a single generated HTML fragment (used for live preview
        of an individual conversion) independent of surrounding context."""
        return self.format(fragment)
