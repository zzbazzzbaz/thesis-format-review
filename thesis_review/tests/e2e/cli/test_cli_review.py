"""CLI 端到端测试。"""
from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


def rules_root() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "rules"


def toc_clean_sample() -> Path:
    return (
        rules_root()
        / "table-of-contents"
        / "samples"
        / "table-of-contents-clean.docx"
    )


@pytest.mark.uno
def test_cli_review_writes_marked_docx_and_issues_json(tmp_path):
    sample = toc_clean_sample()
    if not sample.exists():
        pytest.skip(f"规则样本未准备：{sample}")

    out_dir = tmp_path / "review-output"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "thesis_review.interfaces.cli",
            "review",
            str(sample),
            "--out-dir",
            str(out_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "检查完成" in completed.stdout
    assert zipfile.is_zipfile(out_dir / "marked.docx")
    data = json.loads((out_dir / "issues.json").read_text(encoding="utf-8"))
    assert data["marked_docx"] == str(out_dir / "marked.docx")
    assert isinstance(data["issues"], list)
