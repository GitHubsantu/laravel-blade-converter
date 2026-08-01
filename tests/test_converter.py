"""
Unit tests for the framework-agnostic conversion core.
Run with:  python3 -m pytest tests/  (or)  python3 tests/test_converter.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.converter_engine import ConverterEngine
from core.blade_formatter import BladeFormatter
from core.php_parser import parse_value
from core.php_ast import StaticCall, StringLit, ArrayLit, Raw


class TestPhpParser(unittest.TestCase):
    def test_simple_string_call(self):
        v = parse_value("Form::text('name')")
        self.assertIsInstance(v, StaticCall)
        self.assertEqual(v.class_name, "Form")
        self.assertEqual(v.method, "text")
        self.assertEqual(v.args[0], StringLit("name"))

    def test_nested_array_with_variable_property(self):
        v = parse_value("Form::open(['route' => ['posts.update', $post->id]])")
        self.assertIsInstance(v, StaticCall)
        options = v.args[0]
        self.assertIsInstance(options, ArrayLit)
        key, val = options.items[0]
        self.assertEqual(key.value, "route")
        self.assertIsInstance(val, ArrayLit)
        self.assertIsInstance(val.items[1][1], Raw)
        self.assertEqual(val.items[1][1].text, "$post->id")

    def test_concatenation_falls_back_to_raw(self):
        v = parse_value("'/items/' . $item->id")
        self.assertIsInstance(v, Raw)

    def test_non_collective_call_untouched(self):
        v = parse_value("route('home')")
        self.assertEqual(v.name, "route")

    def test_does_not_hang_on_deeply_nested_trailers(self):
        # Regression test for the depth-tracking bug in trailer consumption.
        v = parse_value("Form::hidden('id', $model->relation->child->id, [])")
        self.assertIsInstance(v, StaticCall)


class TestConverterEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ConverterEngine()

    def convert(self, blade: str) -> str:
        return self.engine.convert(blade).converted_text

    def test_form_open_close_with_route(self):
        out = self.convert("{!! Form::open(['route' => 'posts.store']) !!}{!! Form::close() !!}")
        self.assertIn('<form method="POST" action="{{ route(\'posts.store\') }}">', out)
        self.assertIn("@csrf", out)
        self.assertIn("</form>", out)

    def test_form_model_put_method(self):
        out = self.convert(
            "{!! Form::model($post, ['route' => ['posts.update', $post->id], 'method' => 'PUT']) !!}"
        )
        self.assertIn("@method('PUT')", out)

    def test_text_input(self):
        out = self.convert("{!! Form::text('title', null, ['class' => 'form-control']) !!}")
        self.assertIn('<input type="text" name="title" class="form-control">', out)

    def test_checkbox_with_static_checked(self):
        out = self.convert("{!! Form::checkbox('agree', 1, true) !!}")
        self.assertIn('<input type="checkbox" name="agree" value="1" checked>', out)

    def test_select_with_dynamic_options(self):
        out = self.convert("{!! Form::select('cat', $categories, $selected) !!}")
        self.assertIn("@foreach($categories as $option_key => $option_label)", out)

    def test_link_to_route(self):
        out = self.convert("{!! link_to_route('posts.index', 'Back') !!}")
        self.assertIn('<a href="{{ route(\'posts.index\') }}">Back</a>', out)

    def test_leaves_unrelated_echo_untouched(self):
        out = self.convert("{{ asset('css/app.css') }}")
        self.assertEqual(out, "{{ asset('css/app.css') }}")

    def test_leaves_plain_html_untouched(self):
        out = self.convert("<div class='wrapper'>@if($x)Hi@endif</div>")
        self.assertEqual(out, "<div class='wrapper'>@if($x)Hi@endif</div>")

    def test_report_counts(self):
        result = self.engine.convert(
            "{!! Form::open(['route' => 'x']) !!}"
            "{!! Form::text('a') !!}"
            "{!! Form::close() !!}"
        )
        self.assertEqual(result.report.forms_replaced, 2)
        self.assertEqual(result.report.inputs_replaced, 1)
        self.assertEqual(result.report.total_replacements, 3)


class TestBladeFormatter(unittest.TestCase):
    def test_basic_indent(self):
        formatter = BladeFormatter(indent_size=2)
        out = formatter.format("<div>\n<span>hi</span>\n</div>")
        self.assertEqual(out, "<div>\n  <span>hi</span>\n</div>")


if __name__ == "__main__":
    unittest.main()
