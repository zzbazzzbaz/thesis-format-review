# Phase 1 Text Format Rules Design

## Goal

Implement the first batch of newly prepared rule modules for the thesis review system while keeping the work scoped to paragraph/run-level checks. This phase covers `cover`, `references`, `acknowledgements`, `appendix`, and the `main-text` heading, normal paragraph, and reference citation rules.

Formula rules, figure caption rules, and table caption rules in `main-text` are intentionally excluded from this design. They require richer block extraction and object-adjacency analysis, and will be covered by a second spec.

## Current Context

The runtime review flow is already in place:

```text
UNO extractor -> DocumentModel -> detect_sections/build_rule_context -> registered checkers -> IssueFactory -> issues.json/marked.docx
```

Existing implemented rule modules are `abstract` and `table-of-contents`. The new modules already have `rule.yml`, `case.yml`, and manually prepared Word samples under `thesis_review/docs/rules/**`. The lightweight catalog contract currently passes.

The sample source matters for validation:

- `appendix`, `references`, and `cover` samples were edited with WPS on Windows.
- `acknowledgements` and `main-text` samples were edited with WPS on macOS.

Rules must not branch by sample source. Format checks use the effective values extracted by LibreOffice/UNO in the container.

## Scope

This phase implements these rule groups:

- `cover-title-*`
- `cover-info-*`
- `cover-date-*`
- `references-title-*`
- `references-entry-*`
- `acknowledgements-title-*`
- `acknowledgements-body-*`
- `appendix-title-*`
- `appendix-body-*`
- `main-text-heading-level-one-*`
- `main-text-heading-level-two-*`
- `main-text-heading-level-three-*`
- `main-text-paragraph-*`
- `main-text-reference-citation-*`

These rule groups remain `draft` after this phase:

- `main-text-formula-*`
- `main-text-figure-caption-*`
- `main-text-table-caption-*`

## Architecture

Use the existing checker architecture and add focused modules instead of introducing a YAML-driven rule engine. New code should follow the local pattern used by `abstract_rules.py` and `toc_rules.py`.

Add a small shared formatting helper module for repeated mechanics:

- Build block and run `Location` objects.
- Enumerate section paragraphs and non-empty paragraphs.
- Count consecutive empty paragraphs before or after a paragraph.
- Check and format font, size, bold, line spacing, first-line indent, alignment, and superscript values.
- Format `actual` strings consistently, such as `12pt`, `1.5 倍`, `2 字符`, `居中`, `两端对齐`, and `未识别`.
- Append only the first bad run for the same paragraph/rule where repeated run-level issues would create noisy annotations.

Do not migrate `abstract_rules.py` or `toc_rules.py` as part of this work. They can keep their current helper functions to avoid widening the change.

Add these rule modules:

- `thesis_review/src/thesis_review/rules/cover_rules.py`
- `thesis_review/src/thesis_review/rules/references_rules.py`
- `thesis_review/src/thesis_review/rules/acknowledgements_rules.py`
- `thesis_review/src/thesis_review/rules/appendix_rules.py`
- `thesis_review/src/thesis_review/rules/main_text_rules.py`

Register their checker classes in `thesis_review/src/thesis_review/rules/registry.py`.

## Data Model Change

Extend `RunSpan` with:

```python
superscript: bool = False
```

Update `adapters.uno.extractor` to populate it from UNO run properties. The intended source is `CharEscapement`: values greater than zero are treated as superscript. This supports `main-text-reference-citation-002`.

The field defaults to `False` so existing tests and builder helpers can remain simple. Update `tests/support/model_builders.py` to accept the field when a test needs it.

No block-level model changes are part of this phase.

## Object Recognition

All object recognition is limited to the section ranges from `detect_sections()` to avoid scanning table-of-contents entries or trailing modules by accident.

### Cover

Use `sections["cover"]`, which runs from document start to the first abstract section.

Recognized objects:

- Title line: first non-empty paragraph whose normalized text starts with `题目`.
- Info lines: non-empty paragraphs whose normalized text starts with one of `学生姓名`, `学号`, `院系`, `专业年级`, `指导教师`.
- Date line: non-empty paragraph in the cover section containing `年`, `月`, and `日`.

Checks:

- Title line: Chinese font `黑体`, size `18pt`.
- Info lines: Chinese font `仿宋`, size `16pt`, bold.
- Date line: Chinese font `仿宋`, size `16pt`, bold.

This phase does not report missing cover fields. If an object cannot be found, no issue is emitted for that object.

### Acknowledgements And Appendix

Use `sections["acknowledgements"]` and `sections["appendix"]`.

For each section:

- The title is the first non-empty paragraph in the section.
- Title text must be exactly `致    谢` or `附    录`.
- Title font is `黑体`, size is `16pt`, alignment is center.
- There must be exactly one empty paragraph after the title.
- Body paragraphs are non-empty paragraphs after the title and its following empty paragraphs.

Body checks:

- Size `12pt`.
- Chinese font `宋体`.
- Latin/digit font `Times New Roman` only for runs containing ASCII letters or digits.
- Line spacing `1.5`.
- First-line indent `2` characters.
- Alignment `justify`.

Appendix subsection text such as `附录A...` is treated as body text in this phase. There is no separate appendix subsection-heading rule.

### References

Use `sections["references"]`.

The title is the first non-empty paragraph in the section.

Checks:

- Title text must be exactly `参考文献`.
- There must be exactly one empty paragraph after the title.
- Entry paragraphs are non-empty paragraphs after the title and its following empty paragraphs.
- Entry numbering must start with `[\d+]`.
- Numbering and entry content must be separated by exactly one ordinary half-width space.
- Entry paragraph line spacing is `1.5`.
- Entry visible runs have size `12pt`.
- Runs containing Chinese text use Chinese font `宋体`.
- Runs containing ASCII letters or digits use Latin font `Times New Roman`.

GB/T 7714 bibliography content validation is out of scope.

### Main Text

Use `sections["main-text"]`.

Heading recognition:

- Level one candidates are non-empty paragraphs that begin with `第...章` and are not table-of-contents entries.
- Level two candidates are paragraphs beginning with `N.N`.
- Level three candidates are paragraphs beginning with `N.N.N`.

Level one checks:

- Numbering form must be `第X章`, with `X` using Chinese numerals.
- There must be exactly two half-width spaces between the chapter number and title text.
- Chinese font `黑体`.
- Size `16pt`.
- Exactly one empty paragraph after the heading before body text.
- `page_break_before` must be true for every chapter heading.

Level two checks:

- Numbering form `N.N`.
- Exactly one half-width space after the number.
- Chinese font `黑体`.
- Size `14pt`.
- Line spacing `1.5`.
- Runs containing ASCII letters or digits use Latin font `Times New Roman`.

Level three checks:

- Numbering form `N.N.N`.
- Exactly one half-width space after the number.
- First-line indent `2` characters.
- Chinese font `黑体`.
- Size `12pt`.
- Line spacing `1.5`.
- Runs containing ASCII letters or digits use Latin font `Times New Roman`.

Normal paragraph checks:

- Exclude empty paragraphs, recognized headings, figure captions, table captions, and formula-like paragraphs.
- Size `12pt`.
- Chinese font `宋体`.
- Runs containing ASCII letters or digits use Latin font `Times New Roman`.
- First-line indent `2` characters, including paragraphs beginning with `（1）`.
- Line spacing `1.5`.
- Alignment `justify`.

Reference citation checks:

- Scan normal narrative paragraphs inside the main-text section.
- Citation candidates are bracketed tokens that look like references, including invalid examples such as `[a1]`.
- Valid citation text is `[digits]`.
- For each citation candidate, check that all citation runs are superscript.
- Citation run size is `12pt`.
- Citation run Latin font is `Times New Roman`.

The first phase does not cross-check citations against `references` entries.

## Error Reporting

All issues are created through:

```python
context.issue_factory.create(rule_id=..., actual=..., location=...)
```

Rule code must not hard-code `message`, `expected`, or `severity`.

Location strategy:

- Text, spacing, line spacing, indent, alignment, and page-break issues use paragraph block locations.
- Run-level font, size, bold, and superscript issues use run locations.
- Within one paragraph, report the first failing run per rule to avoid excessive repeated annotations.
- Across different paragraphs, the same `rule_id` may be reported multiple times.

Missing or unrecognized effective format values are treated as failures for required checks and reported with `actual="未识别"`.

Font checks are text-aware:

- Chinese font checks apply to runs containing Chinese text or Chinese punctuation.
- Latin font checks apply to runs containing ASCII letters or digits.
- Pure whitespace runs are ignored.

## Rule Asset Updates

After implementation and verification:

- Mark implemented rules in `cover`, `references`, `acknowledgements`, `appendix`, and the covered `main-text` groups as `active`.
- Keep `main-text-formula-*`, `main-text-figure-caption-*`, and `main-text-table-caption-*` as `draft`.

The registry must declare every active rule id through registered checker classes so `test_active_rules_are_declared_by_registered_checkers` passes.

## Testing Strategy

Unit tests:

- Add focused tests for each new checker module.
- Cover title/body object recognition, exact blank-line counts, paragraph formatting, run formatting, and duplicate run-noise suppression.
- Add `RunSpan.superscript` model and builder coverage.
- Add extractor unit/integration coverage for UNO superscript extraction.
- Add section or helper tests only where object recognition exposes a gap.

Contract tests:

- `uv run pytest tests/contracts/rules/test_rule_catalog.py -q`
- `uv run pytest -m "not uno" -q`

UNO validation:

Use the container as the source of truth for effective WPS formatting:

```bash
docker run --rm -v "$PWD":/workspace -w /workspace \
  thesis-review-uno-dev \
  /opt/venv/bin/python -m pytest tests/contracts/rules/test_case_cli_contract.py -m uno -v
```

If the `thesis-review-uno-dev` image is missing, build it first:

```bash
docker build -f Dockerfile.uno-dev -t thesis-review-uno-dev .
```

## Acceptance Criteria

- All implemented rule ids are active and registered.
- Formula, figure caption, and table caption rules remain draft.
- All non-UNO tests pass.
- UNO sample contract tests pass for the phase-one modules, including Windows WPS samples for `cover`, `references`, and `appendix`.
- Existing `abstract` and `table-of-contents` behavior remains unchanged.
- Output issues use catalog metadata and include stable block/run locations for Word annotation.
