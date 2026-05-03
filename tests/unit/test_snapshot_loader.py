"""Unit tests for demo/snapshot_loader.py.

Verifies round-trip serialisation and rehydration of a minimal Report snapshot,
with explicit assertions that Category enum keys are correctly restored.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from demo.snapshot_loader import SnapshotData, _SNAPSHOT_PATH, load_snapshot
from evaluation.report import MechanismStats, Report, RunMetrics, SampleResult
from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding


def _make_minimal_report() -> Report:
    """Build a small Report with one category and one sample for round-trip testing."""
    metrics = RunMetrics(tp=3, fp=1, fn=2, recall=0.6, precision=0.75, f1=0.666)
    finding = Finding(
        category=Category.PERSONNUMMER,
        start=5,
        end=16,
        text_span="850101-1236",
        confidence=0.95,
        source="pattern.regex_personnummer",
    )
    sample = SampleResult(text="test 850101-1236 text", false_positives=[finding], false_negatives=[])
    return Report(
        total=metrics,
        per_category={Category.PERSONNUMMER: metrics},
        per_layer={"pattern": metrics},
        samples=[sample],
        per_mechanism=MechanismStats(
            high_via_article9=1,
            medium_via_bypass=2,
            medium_via_mechanism3=3,
            low_count=4,
            none_count=5,
        ),
    )


def _make_snapshot_dict(report: Report) -> dict:
    return {
        "metadata": {
            "generated_at": "2026-05-03T12:00:00+00:00",
            "model": "qwen2.5:7b-instruct",
            "prompt_versions": {"article9": "v5", "combination": "v4"},
            "dataset": {"total_texts": 10, "iteration_1_texts": 10, "article9_texts": 0, "combination_texts": 0},
            "git_commit": "abc1234",
            "pipeline_layers": ["pattern", "entity", "article9", "combination"],
        },
        "report": dataclasses.asdict(report),
    }


def test_round_trip_returns_snapshot_data(tmp_path: Path) -> None:
    """load_snapshot() returns a SnapshotData for a valid snapshot file."""
    report = _make_minimal_report()
    snapshot_file = tmp_path / "test_snapshot.json"
    snapshot_file.write_text(
        json.dumps(_make_snapshot_dict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with patch("demo.snapshot_loader._SNAPSHOT_PATH", snapshot_file):
        result = load_snapshot()

    assert result is not None
    assert isinstance(result, SnapshotData)


def test_per_category_keys_are_category_instances(tmp_path: Path) -> None:
    """Category keys in per_category must be Category enum instances, not plain strings.

    Category(str, Enum) means isinstance(key, str) is True for both Category
    instances and plain strings - only isinstance(key, Category) distinguishes them.
    """
    report = _make_minimal_report()
    snapshot_file = tmp_path / "test_snapshot.json"
    snapshot_file.write_text(
        json.dumps(_make_snapshot_dict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with patch("demo.snapshot_loader._SNAPSHOT_PATH", snapshot_file):
        loaded = load_snapshot()

    assert loaded is not None
    for key in loaded.report.per_category:
        assert isinstance(key, Category), (
            f"Expected Category instance, got {type(key)} for key {key!r}. "
            "Rehydration must use Category(str) not raw string."
        )


def test_numeric_fields_are_int(tmp_path: Path) -> None:
    """RunMetrics fields (tp, fp, fn) must be int after rehydration, not strings."""
    report = _make_minimal_report()
    snapshot_file = tmp_path / "test_snapshot.json"
    snapshot_file.write_text(
        json.dumps(_make_snapshot_dict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with patch("demo.snapshot_loader._SNAPSHOT_PATH", snapshot_file):
        loaded = load_snapshot()

    assert loaded is not None
    assert isinstance(loaded.report.total.tp, int)
    assert isinstance(loaded.report.total.fp, int)
    assert isinstance(loaded.report.total.fn, int)
    assert loaded.report.total.tp == 3
    assert loaded.report.total.fp == 1
    assert loaded.report.total.fn == 2


def test_mechanism_stats_rehydrated(tmp_path: Path) -> None:
    """MechanismStats fields must survive round-trip correctly."""
    report = _make_minimal_report()
    snapshot_file = tmp_path / "test_snapshot.json"
    snapshot_file.write_text(
        json.dumps(_make_snapshot_dict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with patch("demo.snapshot_loader._SNAPSHOT_PATH", snapshot_file):
        loaded = load_snapshot()

    assert loaded is not None
    pm = loaded.report.per_mechanism
    assert pm.high_via_article9 == 1
    assert pm.medium_via_bypass == 2
    assert pm.medium_via_mechanism3 == 3
    assert pm.low_count == 4
    assert pm.none_count == 5


def test_returns_none_when_file_missing() -> None:
    """load_snapshot() returns None when the snapshot file does not exist."""
    missing = Path("/nonexistent/path/iteration_2_report.json")
    with patch("demo.snapshot_loader._SNAPSHOT_PATH", missing):
        result = load_snapshot()
    assert result is None


def test_returns_none_on_corrupt_json(tmp_path: Path) -> None:
    """load_snapshot() returns None for a file containing invalid JSON."""
    corrupt = tmp_path / "bad.json"
    corrupt.write_text("{ this is not valid json", encoding="utf-8")
    with patch("demo.snapshot_loader._SNAPSHOT_PATH", corrupt):
        result = load_snapshot()
    assert result is None
