# Release Notes

## v1.0.0 — Initial Release (2026-08-01)

First public release of **Laravel Blade Converter** — a PySide6 desktop
app that converts legacy LaravelCollective Blade syntax (`Form::`,
`Html::`, `link_to_route`) into native Laravel 12 Blade/HTML.

### ✨ Highlights

- **Real parser, not regex.** A hand-written recursive-descent PHP
  expression parser (`core/php_lexer.py` + `core/php_parser.py`) tokenizes
  and parses the arguments of every LaravelCollective call — nested
  arrays, strings, numbers, booleans, `null`, and dynamic PHP
  (`$model->id`, `old('name')`) — instead of pattern-matching text.
- **Conversion engine** (`core/converter_engine.py`) covers:
  - `Form::open()` / `Form::model()` / `Form::close()` → `<form>` + `@csrf` + `@method(...)`
  - `Form::text/email/password/number/date/time/url/search/tel/color/range/month/week()`
  - `Form::hidden()`, `Form::file()`, `Form::textarea()`
  - `Form::checkbox()` / `Form::radio()` (static `checked` or `@checked(...)` for dynamic conditions)
  - `Form::select()` — full static `<option>` list, or a `@foreach` loop when options are a variable
  - `Form::button()`, `Form::submit()`, `Form::label()`
  - `link_to_route()`, `Html::link()`, `Html::image()`, `Html::mailto()`
  - `asset()`, `route()`, `__()`, and all `@directives` are left untouched
- **Safety first:** anything the parser can't statically resolve (ternaries,
  method chains, unusual dynamic expressions) is left in the output
  unchanged and flagged as a warning instead of being guessed at.
- **VS Code-like editor:** line numbers, current-line highlight, bracket
  matching, Blade/HTML/PHP syntax highlighting, auto-indent, zoom
  (Ctrl+Scroll or toolbar), Ctrl+F / Ctrl+H / Ctrl+S / Ctrl+Z / Ctrl+Y,
  right-click context menu.
- **Original / Converted tabs** for side-by-side review before saving.
- **Live Statistics panel:** forms, inputs, labels, buttons, selects,
  textareas, checkboxes, radios, links, warnings, total replacements.
- **Output Console** streaming load/convert/save/warning/error events.
- **Batch Convert Folder:** recursively scans a Laravel project's
  `resources/views` (or any folder) and converts every `*.blade.php` file
  in one pass, with a summary report (converted / skipped / warnings).
- **Automatic backups:** a `filename.blade.php.bak` is created before any
  file on disk is overwritten (toggle in Settings).
- **Dark / light theme**, adjustable editor font size and indent width.
- Ships with a **PyInstaller build spec** (`blade_converter.spec`) and a
  **GitHub Actions workflow** that builds Windows/macOS/Linux executables
  automatically on every version tag.
- **15 unit tests** covering the parser and converter core (`tests/test_converter.py`), no display required.

### 📦 What's included

```
core/    Qt-free, unit-tested conversion engine (lexer, parser, AST, formatter, file I/O)
ui/      PySide6 presentation layer (editor, dialogs, docks, theming)
tests/   unittest suite for core/
```

### ⚠️ Known limitations

- `BladeFormatter` is a heuristic, line-based re-indenter — it recomputes
  leading whitespace only and never rewrites content, so it can drift on
  deeply nested multi-line generated blocks. It is not a full HTML/Blade
  re-parser.
- Fully dynamic PHP (ternaries, chained method calls, closures) inside a
  LaravelCollective call is preserved as a raw embedded expression rather
  than evaluated — this is intentional (accuracy over false confidence)
  but means very complex calls may need a quick manual check.
- `Form::model()`'s automatic PUT-vs-POST method inference (based on
  whether the bound model exists) can't be resolved statically; the tool
  warns when no explicit `method` key is present so you can add
  `@method('PUT')` yourself if needed.

### 🔜 Possibly next

- Optional web/CLI version of the same `core/` engine
- Custom Blade component / macro conversion support
- App icon + signed Windows/macOS installers
