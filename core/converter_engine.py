"""
ConverterEngine: walks a tokenized Blade template and rewrites every
LaravelCollective ``Form::`` / ``Html::`` / ``link_to_route`` call it
can confidently understand into native Laravel 12 Blade/HTML, leaving
everything else (plain HTML, @directives, dynamic expressions it can't
safely resolve) untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .app_logger import get_logger
from .blade_tokenizer import Segment, SegmentType, tokenize_blade
from .conversion_report import ConversionReport
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
    to_php_source,
)
from .php_parser import parse_value

log = get_logger("converter_engine")

_KNOWN_FORM_METHODS = {
    "open", "model", "close", "text", "email", "password", "number",
    "hidden", "file", "textarea", "checkbox", "radio", "select", "button",
    "submit", "label", "date", "time", "url", "search", "tel", "color",
    "range", "month", "week",
}
_KNOWN_HTML_METHODS = {"link", "linkRoute", "linkAction", "image", "mailto", "script", "style"}
_KNOWN_FUNCTIONS = {"link_to_route", "link_to_action", "link_to"}

_INPUT_TYPE_METHODS = {
    "text", "email", "password", "number", "date", "time", "url",
    "search", "tel", "color", "range", "month", "week",
}


@dataclass
class ConversionResult:
    converted_text: str
    report: ConversionReport


def _arg(args: List[Value], idx: int) -> Optional[Value]:
    return args[idx] if idx < len(args) else None


def _is_literal_str(v: Optional[Value]) -> bool:
    return isinstance(v, StringLit)


def _literal_text(v: Value) -> str:
    """Render a value as plain literal text (for names/ids/labels)."""
    if isinstance(v, StringLit):
        return v.value
    if isinstance(v, NumberLit):
        return v.value
    return _embed(v)


def _embed(v: Optional[Value]) -> str:
    """Render a dynamic/unresolvable value as a Blade echo expression."""
    if v is None or isinstance(v, NullLit):
        return ""
    if isinstance(v, StringLit):
        return v.value
    if isinstance(v, NumberLit):
        return v.value
    return "{{ " + to_php_source(v) + " }}"


def _humanize(name: str) -> str:
    cleaned = name.replace("_", " ").replace("[]", "").replace(".", " ")
    return cleaned.strip().title()


def _escape_attr(text: str) -> str:
    return text.replace('"', "&quot;")


def _render_attrs(arr: Optional[ArrayLit], report: ConversionReport, extra: Optional[Dict[str, str]] = None) -> str:
    """Render an attributes array literal into a string of HTML attributes."""
    parts: List[str] = []
    if extra:
        for k, v in extra.items():
            if v is None:
                continue
            parts.append(f'{k}="{_escape_attr(v)}"')

    if isinstance(arr, ArrayLit):
        for key, val in arr.items:
            if key is None:
                report.add_warning("Skipped a positional item found inside an attributes array.")
                continue
            if isinstance(key, StringLit):
                key_text = key.value
            elif isinstance(key, NumberLit):
                key_text = key.value
            else:
                report.add_warning("Skipped a dynamic attribute key that could not be resolved statically.")
                continue

            if isinstance(val, BoolLit):
                if val.value:
                    parts.append(key_text)
                continue
            if isinstance(val, NullLit):
                continue

            val_text = _embed(val)
            parts.append(f'{key_text}="{_escape_attr(val_text)}"')
    elif arr is not None and not isinstance(arr, NullLit):
        report.add_warning("Attributes argument was not a literal array; it was skipped.")

    return (" " + " ".join(parts)) if parts else ""


def _extract_attr_value(arr: Optional[ArrayLit], key: str) -> Optional[Value]:
    if not isinstance(arr, ArrayLit):
        return None
    for k, v in arr.items:
        if isinstance(k, StringLit) and k.value == key:
            return v
    return None


def _remove_keys(arr: Optional[ArrayLit], keys: set) -> Optional[ArrayLit]:
    if not isinstance(arr, ArrayLit):
        return arr
    filtered = [(k, v) for k, v in arr.items if not (isinstance(k, StringLit) and k.value in keys)]
    return ArrayLit(filtered)


class ConverterEngine:
    """Translates a single Blade template's content."""

    def __init__(self) -> None:
        self._form_handlers: Dict[str, Callable[[List[Value], ConversionReport], Optional[str]]] = {
            "open": self._form_open,
            "model": self._form_model,
            "close": self._form_close,
            "textarea": self._form_textarea,
            "checkbox": lambda a, r: self._form_check_radio(a, r, "checkbox"),
            "radio": lambda a, r: self._form_check_radio(a, r, "radio"),
            "select": self._form_select,
            "button": self._form_button,
            "submit": self._form_submit,
            "label": self._form_label,
            "file": self._form_file,
            "hidden": lambda a, r: self._form_simple_input(a, r, "hidden"),
        }
        for input_type in _INPUT_TYPE_METHODS:
            self._form_handlers[input_type] = (
                lambda a, r, t=input_type: self._form_simple_input(a, r, t)
            )

    # ------------------------------------------------------------------
    def convert(self, content: str, file_name: str = "") -> ConversionResult:
        report = ConversionReport(file_name=file_name)
        segments = tokenize_blade(content)
        out_parts: List[str] = []

        for seg in segments:
            if seg.type in (SegmentType.RAW, SegmentType.COMMENT):
                out_parts.append(seg.text)
                continue

            replacement = self._convert_segment(seg, report)
            out_parts.append(replacement if replacement is not None else seg.text)

        converted = "".join(out_parts)
        log.info(
            "Conversion finished for %s: %d replacement(s), %d warning(s)",
            file_name or "<in-memory>",
            report.total_replacements,
            len(report.warnings),
        )
        return ConversionResult(converted, report)

    # ------------------------------------------------------------------
    def _convert_segment(self, seg: Segment, report: ConversionReport) -> Optional[str]:
        try:
            value = parse_value(seg.expr)
        except Exception as exc:  # pragma: no cover - defensive
            report.add_warning(f"Could not parse expression `{seg.expr.strip()}`: {exc}")
            log.warning("Parse failure on segment: %s (%s)", seg.expr.strip(), exc)
            return None

        if isinstance(value, StaticCall):
            if value.class_name == "Form" and value.method in self._form_handlers:
                try:
                    return self._form_handlers[value.method](value.args, report)
                except Exception as exc:  # pragma: no cover - defensive
                    report.add_warning(
                        f"Failed to convert Form::{value.method}(...): {exc}"
                    )
                    log.exception("Handler failure for Form::%s", value.method)
                    return None
            if value.class_name == "Html" and value.method in _KNOWN_HTML_METHODS:
                try:
                    return self._html_call(value.method, value.args, report)
                except Exception as exc:  # pragma: no cover - defensive
                    report.add_warning(f"Failed to convert Html::{value.method}(...): {exc}")
                    log.exception("Handler failure for Html::%s", value.method)
                    return None
            report.add_warning(
                f"Left `{value.class_name}::{value.method}(...)` unchanged (not a recognized LaravelCollective call)."
            )
            return None

        if isinstance(value, FuncCall) and value.name in _KNOWN_FUNCTIONS:
            try:
                return self._link_to_route(value.args, report)
            except Exception as exc:  # pragma: no cover - defensive
                report.add_warning(f"Failed to convert {value.name}(...): {exc}")
                log.exception("Handler failure for %s", value.name)
                return None

        # Not a LaravelCollective construct (asset(), route(), __(), variables,
        # etc.) -- leave untouched.
        return None

    # ------------------------------------------------------------------
    # Form:: handlers
    # ------------------------------------------------------------------
    def _resolve_action_and_method(self, options: Optional[ArrayLit], report: ConversionReport):
        method_val = _extract_attr_value(options, "method")
        method = "POST"
        if isinstance(method_val, StringLit):
            method = method_val.value.upper()

        action_html = "#"
        route_val = _extract_attr_value(options, "route")
        url_val = _extract_attr_value(options, "url")
        action_val = _extract_attr_value(options, "action")

        if route_val is not None:
            if isinstance(route_val, ArrayLit) and route_val.items:
                route_name_val = route_val.items[0][1]
                params = ArrayLit(route_val.items[1:]) if len(route_val.items) > 1 else None
                route_name = _literal_text(route_name_val) if isinstance(route_name_val, StringLit) else to_php_source(route_name_val)
                if params and params.items:
                    action_html = "{{ route('%s', %s) }}" % (route_name, to_php_source(params))
                else:
                    action_html = "{{ route('%s') }}" % route_name
            elif isinstance(route_val, StringLit):
                action_html = "{{ route('%s') }}" % route_val.value
            else:
                action_html = "{{ route(%s) }}" % to_php_source(route_val)
        elif url_val is not None:
            if isinstance(url_val, StringLit):
                action_html = "{{ url('%s') }}" % url_val.value
            else:
                action_html = "{{ url(%s) }}" % to_php_source(url_val)
        elif action_val is not None:
            action_html = "{{ action(%s) }}" % to_php_source(action_val)
        else:
            report.add_warning("Form open/model call had no 'route', 'url' or 'action' key; defaulted action to '#'.")

        remaining = _remove_keys(options, {"route", "url", "action", "method", "files"})
        return action_html, method, remaining

    def _form_open(self, args: List[Value], report: ConversionReport) -> str:
        options = _arg(args, 0)
        if options is not None and not isinstance(options, ArrayLit):
            options = None
        action_html, method, remaining = self._resolve_action_and_method(options, report)

        files_val = _extract_attr_value(_arg(args, 0) if isinstance(_arg(args, 0), ArrayLit) else None, "files")
        is_multipart = isinstance(files_val, BoolLit) and files_val.value

        real_method = method if method in ("GET", "POST") else "POST"
        extra = {"method": real_method, "action": action_html}
        if is_multipart:
            extra["enctype"] = "multipart/form-data"

        attrs = _render_attrs(remaining, report, extra)
        html = f"<form{attrs}>\n@csrf"
        if method not in ("GET", "POST"):
            html += f"\n@method('{method}')"
        report.bump("forms_replaced")
        return html

    def _form_model(self, args: List[Value], report: ConversionReport) -> str:
        # LaravelCollective supports both Form::model($options) with a 'model'
        # key inside, and the far more common Form::model($model, $options).
        first = _arg(args, 0)
        if isinstance(first, ArrayLit):
            options = first
        else:
            second = _arg(args, 1)
            options = second if isinstance(second, ArrayLit) else None

        action_html, method, remaining = self._resolve_action_and_method(options, report)
        method_explicit = _extract_attr_value(options, "method") is not None

        files_val = _extract_attr_value(options, "files")
        is_multipart = isinstance(files_val, BoolLit) and files_val.value

        real_method = method if method in ("GET", "POST") else "POST"
        extra = {"method": real_method, "action": action_html}
        if is_multipart:
            extra["enctype"] = "multipart/form-data"

        remaining = _remove_keys(remaining, {"model"})
        attrs = _render_attrs(remaining, report, extra)
        html = f"<form{attrs}>\n@csrf"
        if method_explicit and method not in ("GET", "POST"):
            html += f"\n@method('{method}')"
        elif not method_explicit:
            report.add_warning(
                "Form::model(...) had no explicit 'method' key; Form::model previously chose "
                "PUT/POST automatically based on the model. Please verify and add @method('PUT') "
                "if this is an edit form."
            )
        report.bump("forms_replaced")
        return html

    def _form_close(self, args: List[Value], report: ConversionReport) -> str:
        report.bump("forms_replaced")
        return "</form>"

    def _form_simple_input(self, args: List[Value], report: ConversionReport, input_type: str) -> str:
        name = _arg(args, 0)
        value = _arg(args, 1)
        attrs = _arg(args, 2)
        if not isinstance(attrs, ArrayLit):
            attrs = None

        name_text = _literal_text(name) if name is not None else ""
        extra = {"type": input_type, "name": name_text}
        if value is not None and not isinstance(value, NullLit):
            extra["value"] = _embed(value)

        rendered = _render_attrs(attrs, report, extra)
        report.bump("inputs_replaced")
        return f"<input{rendered}>"

    def _form_file(self, args: List[Value], report: ConversionReport) -> str:
        name = _arg(args, 0)
        attrs = _arg(args, 1)
        if not isinstance(attrs, ArrayLit):
            attrs = None
        name_text = _literal_text(name) if name is not None else ""
        extra = {"type": "file", "name": name_text}
        rendered = _render_attrs(attrs, report, extra)
        report.bump("inputs_replaced")
        return f"<input{rendered}>"

    def _form_textarea(self, args: List[Value], report: ConversionReport) -> str:
        name = _arg(args, 0)
        value = _arg(args, 1)
        attrs = _arg(args, 2)
        if not isinstance(attrs, ArrayLit):
            attrs = None
        name_text = _literal_text(name) if name is not None else ""
        rendered = _render_attrs(attrs, report, {"name": name_text})
        inner = _embed(value) if value is not None else ""
        report.bump("textareas_replaced")
        return f"<textarea{rendered}>{inner}</textarea>"

    def _form_check_radio(self, args: List[Value], report: ConversionReport, kind: str) -> str:
        name = _arg(args, 0)
        value = _arg(args, 1)
        checked = _arg(args, 2)
        attrs = _arg(args, 3)
        if not isinstance(attrs, ArrayLit):
            attrs = None

        name_text = _literal_text(name) if name is not None else ""
        extra = {"type": kind, "name": name_text}
        if value is not None and not isinstance(value, NullLit):
            extra["value"] = _embed(value)
        else:
            extra["value"] = "1"

        rendered = _render_attrs(attrs, report, extra)
        checked_attr = ""
        if isinstance(checked, BoolLit) and checked.value:
            checked_attr = " checked"
        elif checked is not None and not isinstance(checked, (NullLit, BoolLit)):
            checked_attr = " @checked(%s)" % to_php_source(checked)
            rendered = rendered  # keep as-is; @checked directive appended below instead of raw attr
            report.bump("checkboxes_replaced" if kind == "checkbox" else "radios_replaced")
            return f"<input{rendered}{checked_attr}>"

        report.bump("checkboxes_replaced" if kind == "checkbox" else "radios_replaced")
        return f"<input{rendered}{checked_attr}>"

    def _form_select(self, args: List[Value], report: ConversionReport) -> str:
        name = _arg(args, 0)
        options = _arg(args, 1)
        selected = _arg(args, 2)
        attrs = _arg(args, 3)
        if not isinstance(attrs, ArrayLit):
            attrs = None

        name_text = _literal_text(name) if name is not None else ""
        rendered = _render_attrs(attrs, report, {"name": name_text})
        report.bump("selects_replaced")

        if isinstance(options, ArrayLit):
            lines = [f"<select{rendered}>"]
            for key, val in options.items:
                opt_value = _literal_text(key) if key is not None else _literal_text(val)
                opt_label = _literal_text(val)
                selected_attr = ""
                if isinstance(selected, (StringLit, NumberLit)) and _literal_text(selected) == opt_value:
                    selected_attr = " selected"
                elif selected is not None and not isinstance(selected, NullLit):
                    selected_attr = " @selected(%s == '%s')" % (to_php_source(selected), opt_value)
                lines.append(f'    <option value="{_escape_attr(opt_value)}"{selected_attr}>{opt_label}</option>')
            lines.append("</select>")
            return "\n".join(lines)

        # Options come from a dynamic variable/expression -- emit a @foreach loop.
        options_src = to_php_source(options) if options is not None else "[]"
        selected_expr = to_php_source(selected) if selected is not None and not isinstance(selected, NullLit) else "null"
        report.add_warning(
            f"Form::select options for '{name_text}' were dynamic; generated a @foreach loop over {options_src}."
        )
        return (
            f"<select{rendered}>\n"
            f"    @foreach({options_src} as $option_key => $option_label)\n"
            f'        <option value="{{{{ $option_key }}}}" @selected($option_key == {selected_expr})>{{{{ $option_label }}}}</option>\n'
            f"    @endforeach\n"
            f"</select>"
        )

    def _form_button(self, args: List[Value], report: ConversionReport) -> str:
        value = _arg(args, 0)
        attrs = _arg(args, 1)
        if not isinstance(attrs, ArrayLit):
            attrs = None
        rendered = _render_attrs(attrs, report, {"type": "button"})
        inner = _embed(value) if value is not None else "Button"
        report.bump("buttons_replaced")
        return f"<button{rendered}>{inner}</button>"

    def _form_submit(self, args: List[Value], report: ConversionReport) -> str:
        value = _arg(args, 0)
        attrs = _arg(args, 1)
        if not isinstance(attrs, ArrayLit):
            attrs = None
        rendered = _render_attrs(attrs, report, {"type": "submit"})
        inner = _embed(value) if value is not None else "Submit"
        report.bump("buttons_replaced")
        return f"<button{rendered}>{inner}</button>"

    def _form_label(self, args: List[Value], report: ConversionReport) -> str:
        name = _arg(args, 0)
        value = _arg(args, 1)
        attrs = _arg(args, 2)
        if not isinstance(attrs, ArrayLit):
            attrs = None
        name_text = _literal_text(name) if name is not None else ""
        rendered = _render_attrs(attrs, report, {"for": name_text})
        inner = _embed(value) if value is not None and not isinstance(value, NullLit) else _humanize(name_text)
        report.bump("labels_replaced")
        return f"<label{rendered}>{inner}</label>"

    # ------------------------------------------------------------------
    # Html:: handlers
    # ------------------------------------------------------------------
    def _html_call(self, method: str, args: List[Value], report: ConversionReport) -> Optional[str]:
        if method == "link":
            url = _arg(args, 0)
            title = _arg(args, 1)
            attrs = _arg(args, 2)
            if not isinstance(attrs, ArrayLit):
                attrs = None
            href = _embed(url) if url is not None else "#"
            if isinstance(url, StringLit):
                href = "{{ url('%s') }}" % url.value
            rendered = _render_attrs(attrs, report, {"href": href})
            inner = _embed(title) if title is not None and not isinstance(title, NullLit) else href
            report.bump("links_replaced")
            return f"<a{rendered}>{inner}</a>"

        if method == "image":
            url = _arg(args, 0)
            alt = _arg(args, 1)
            attrs = _arg(args, 2)
            if not isinstance(attrs, ArrayLit):
                attrs = None
            src = "{{ asset('%s') }}" % url.value if isinstance(url, StringLit) else _embed(url)
            extra = {"src": src}
            if alt is not None and not isinstance(alt, NullLit):
                extra["alt"] = _embed(alt)
            rendered = _render_attrs(attrs, report, extra)
            report.bump("links_replaced")
            return f"<img{rendered}>"

        if method == "mailto":
            email = _arg(args, 0)
            title = _arg(args, 1)
            attrs = _arg(args, 2)
            if not isinstance(attrs, ArrayLit):
                attrs = None
            email_text = _literal_text(email) if email is not None else ""
            rendered = _render_attrs(attrs, report, {"href": f"mailto:{email_text}"})
            inner = _embed(title) if title is not None and not isinstance(title, NullLit) else email_text
            report.bump("links_replaced")
            return f"<a{rendered}>{inner}</a>"

        report.add_warning(f"Html::{method}(...) is recognized but not auto-converted; left unchanged.")
        return None

    # ------------------------------------------------------------------
    def _link_to_route(self, args: List[Value], report: ConversionReport) -> str:
        route_name = _arg(args, 0)
        title = _arg(args, 1)
        parameters = _arg(args, 2)
        attrs = _arg(args, 3)
        if not isinstance(attrs, ArrayLit):
            attrs = None

        route_name_text = route_name.value if isinstance(route_name, StringLit) else to_php_source(route_name)
        if isinstance(parameters, ArrayLit) and parameters.items:
            href = "{{ route('%s', %s) }}" % (route_name_text, to_php_source(parameters))
        elif parameters is not None and not isinstance(parameters, (NullLit, ArrayLit)):
            href = "{{ route('%s', %s) }}" % (route_name_text, to_php_source(parameters))
        else:
            href = "{{ route('%s') }}" % route_name_text

        rendered = _render_attrs(attrs, report, {"href": href})
        inner = _embed(title) if title is not None and not isinstance(title, NullLit) else route_name_text
        report.bump("links_replaced")
        return f"<a{rendered}>{inner}</a>"
