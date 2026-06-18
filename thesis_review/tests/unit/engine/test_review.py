"""engine.review 编排测试。"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from thesis_review.core.models import DocumentModel, Issue, Location, ParagraphBlock
from thesis_review.engine.review import ReviewDependencies, review


def make_document(path: str) -> DocumentModel:
    return DocumentModel(
        source_docx=path,
        blocks=[
            ParagraphBlock(
                id="b-0000",
                kind="paragraph",
                flow_index=0,
                type_index=0,
                text="目    录",
                style_name=None,
                outline_level=None,
                alignment="center",
                line_spacing=1.5,
                first_line_indent_chars=0.0,
                is_empty=False,
                runs=[],
            )
        ],
    )


def make_issue() -> Issue:
    return Issue(
        rule_id="table-of-contents-title-001",
        category="format",
        severity="error",
        message="目录标题文本应为“目    录”",
        expected="目    录",
        actual="目录",
        location=Location(
            target="block",
            block_id="b-0000",
            block_kind="paragraph",
            flow_index=0,
        ),
    )


class FakeSession:
    @contextmanager
    def open(self, path: str):
        yield {"path": path}


class FakeSessionFactory:
    def __init__(self):
        self.session = FakeSession()

    def __call__(self):
        return self

    def __enter__(self):
        return self.session

    def __exit__(self, *exc):
        return None


class FakeChecker:
    checker_id = "fake"
    rule_ids = ("table-of-contents-title-001",)

    def __init__(self, issue: Issue):
        self.issue = issue

    def check(self, context):
        return [self.issue]


def test_review_creates_out_dir_marked_docx_and_issues_json(tmp_path):
    input_docx = tmp_path / "input.docx"
    input_docx.write_bytes(b"docx")
    out_dir = tmp_path / "out"
    issue = make_issue()
    calls: list[tuple[str, str, list[str]]] = []

    def fake_extract(doc, source_path: str):
        assert doc == {"path": str(input_docx)}
        return make_document(source_path)

    def fake_build_context(document):
        assert document.source_docx == str(input_docx)
        return {"document": document}

    def fake_annotate(session, source: str, target: str, issues: list[Issue]):
        calls.append((source, target, [item.rule_id for item in issues]))
        Path(target).write_bytes(b"marked")

    deps = ReviewDependencies(
        session_factory=FakeSessionFactory(),
        extract=fake_extract,
        annotate=fake_annotate,
        build_rule_context=fake_build_context,
        get_checkers=lambda: [FakeChecker(issue)],
    )

    result = review(str(input_docx), out_dir, dependencies=deps)

    assert result.input_docx == input_docx
    assert result.out_dir == out_dir
    assert result.marked_docx == out_dir / "marked.docx"
    assert result.issues_json == out_dir / "issues.json"
    assert result.issues == [issue]
    assert result.marked_docx.read_bytes() == b"marked"
    assert result.issues_json.exists()
    assert calls == [
        (str(input_docx), str(out_dir / "marked.docx"), ["table-of-contents-title-001"])
    ]
