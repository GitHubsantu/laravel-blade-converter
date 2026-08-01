# Laravel Blade Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41cd52.svg)](https://doc.qt.io/qtforpython/)
[![Build Executables](https://img.shields.io/github/actions/workflow/status/githubsantu/laravel-blade-converter/build.yml?label=build)](../../actions)

A production-quality **PySide6 desktop application** that converts legacy
**LaravelCollective** Blade syntax (`Form::`, `Html::`, `link_to_route`) into
native **Laravel 12** Blade/HTML — using a real recursive-descent PHP
expression parser, not regex.

> Migrating a Laravel 8 → Laravel 12 app and tired of hand-converting
> hundreds of `Form::` calls across your Blade views? This tool automates it
> while preserving your existing business logic and flagging anything it
> can't safely convert instead of guessing.

---

## ✨ Features

- 🖱️ Drag & drop a `.blade.php` file, or **Open File**
- 🖊️ VS Code-like editor — line numbers, current-line highlight, bracket
  matching, syntax highlighting, auto-indent, zoom, Ctrl+F / Ctrl+H /
  Ctrl+S / Ctrl+Z / Ctrl+Y, right-click menu
- 🔀 **Original** / **Converted** tabs for side-by-side comparison
- 📊 Live **Statistics** panel (forms, inputs, labels, buttons, selects,
  textareas, checkboxes, radios, links, warnings, total)
- 🖥️ **Output Console** streaming load / convert / save / warning / error events
- 📁 **Batch Convert Folder** — recursively converts every `*.blade.php`
  under `resources/views` (or any folder), with a summary report
- 🛟 Automatic `filename.blade.php.bak` backup before any overwrite
- 🌗 Dark / light theme, adjustable font size & indent width

## 🧠 Why not just regex?

Because `Form::text('name', $value, ['class' => 'form-control'])` is real
PHP, not a fixed string pattern — arguments can be nested arrays, method
chains, variables, or string concatenation. This app tokenizes and parses
that PHP expression subset with a hand-written lexer + recursive-descent
parser (`core/php_lexer.py`, `core/php_parser.py`) and builds a small AST
(`core/php_ast.py`) before generating HTML. Anything it can't confidently
resolve statically (ternaries, chained method calls, unusual dynamic
expressions) is **left untouched** in the output and reported as a warning
— never silently guessed at.

## 🔁 Conversion coverage

| LaravelCollective | Laravel 12 output |
|---|---|
| `Form::open([...])` | `<form method="..." action="...">` + `@csrf` (+ `@method(...)` if needed) |
| `Form::model($m, [...])` | same as above, model-aware; warns if method can't be inferred |
| `Form::close()` | `</form>` |
| `Form::text/email/password/number/date/...()` | `<input type="...">` |
| `Form::hidden()` / `Form::file()` | `<input type="hidden">` / `<input type="file">` |
| `Form::textarea()` | `<textarea>...</textarea>` |
| `Form::checkbox()` / `Form::radio()` | `<input type="checkbox"/"radio">` with `checked` / `@checked(...)` |
| `Form::select()` | full `<select>` (static array) or `@foreach` loop (dynamic options) |
| `Form::button()` / `Form::submit()` | `<button>` / `<button type="submit">` |
| `Form::label()` | `<label for="...">` |
| `link_to_route()` | `<a href="{{ route(...) }}">` |
| `Html::link()` / `Html::image()` / `Html::mailto()` | `<a>` / `<img>` / `mailto:` link |
| `asset()`, `route()`, `__()`, `@if`, `@foreach`, `@csrf`, ... | left unchanged |

## 🏗️ Architecture

```
blade_converter/
├── main.py                     # entry point
├── requirements.txt
├── blade_converter.spec        # PyInstaller build spec
├── core/                       # NO Qt dependency — pure Python, unit tested
│   ├── app_logger.py           # logging + GUI log bridge
│   ├── php_lexer.py            # tokenizer for the PHP expression subset
│   ├── php_ast.py              # AST node definitions
│   ├── php_parser.py           # recursive-descent parser
│   ├── blade_tokenizer.py      # splits template into raw / echo segments
│   ├── converter_engine.py     # ConverterEngine: AST -> HTML/Blade
│   ├── blade_formatter.py      # BladeFormatter: indentation beautifier
│   ├── conversion_report.py    # ConversionReport statistics object
│   └── file_manager.py         # FileManager: read/write/backup/scan
├── ui/                         # PySide6 presentation layer
│   ├── main_window.py          # MainWindow (toolbar, docks, tabs, menu)
│   ├── editor_widget.py        # CodeEditor (VS Code-like QPlainTextEdit)
│   ├── syntax_highlighter.py   # BladeSyntaxHighlighter
│   ├── theme_manager.py        # ThemeManager (dark/light palette + QSS)
│   ├── find_replace_dialog.py  # FindReplaceDialog
│   ├── file_explorer.py        # FileExplorer (left dock, drag & drop)
│   ├── output_console.py       # OutputConsole (bottom dock)
│   ├── stats_panel.py          # StatsPanel (right dock)
│   └── settings_dialog.py      # SettingsDialog + AppSettings
├── tests/
│   └── test_converter.py       # unit tests for core/ (no GUI needed)
└── .github/workflows/build.yml # CI: builds Win/macOS/Linux executables on tag push
```

`core/` has zero PySide6 imports, so the parser/converter is fully unit
tested (and reusable, e.g. from a future CLI) without a display.

## 🚀 Getting started

```bash
git clone https://github.com/imdevops/laravel-blade-converter.git
cd laravel-blade-converter

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python3 main.py
```

### Prebuilt executables

Download the latest Windows/macOS/Linux build from the
[Releases](../../releases) page, or see [BUILD.md](BUILD.md) to build your
own with PyInstaller.

## 🧪 Running the tests

```bash
python3 -m unittest discover -s tests -v
```

## 🛟 Safety

- Every save creates `filename.blade.php.bak` next to the original
  (toggle in Settings) before it is overwritten.
- Anything the parser cannot statically resolve is **left untouched** and
  reported as a warning rather than silently mis-converted.
- Batch conversion logs every file in the Output Console plus a summary
  dialog (converted / skipped / warnings / total replacements).

## ⚠️ Known limitations

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for the current version's known
limitations and what's planned next.

## 🤝 Contributing

Issues and PRs welcome. Please run `python3 -m unittest discover -s tests`
before submitting, and keep `core/` free of any Qt/PySide6 imports.

## 📄 License

[MIT](LICENSE) © [imdevops](https://imdevops.in)
