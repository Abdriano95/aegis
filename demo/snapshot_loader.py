"""Snapshot loader for demo evaluation results.

Loads and rehydrates a pre-generated JSON snapshot back into typed Report dataclasses.
Returns None if the snapshot file is missing or malformed.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from evaluation.dataset.labeled_finding import LabeledFinding
from evaluation.report import MechanismStats, Report, RunMetrics, SampleResult
from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding

_LOG = logging.getLogger(__name__)

_SNAPSHOT_PATH = (
    Path(__file__).resolve().parent / "snapshots" / "iteration_2_report.json"
)


@dataclass(frozen=True)
class SnapshotData:
    """Container for a loaded and rehydrated evaluation snapshot."""

    metadata: dict
    report: Report


def load_snapshot() -> SnapshotData | None:
    """Load the snapshot file and return a rehydrated SnapshotData, or None on failure."""
    if not _SNAPSHOT_PATH.exists():
        _LOG.info("Snapshot file not found at %s", _SNAPSHOT_PATH)
        return None
    try:
        raw = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        report = _rehydrate_report(raw["report"])
        return SnapshotData(metadata=raw.get("metadata", {}), report=report)
    except (json.JSONDecodeError, FileNotFoundError, KeyError, ValueError):
        _LOG.exception("Failed to load or rehydrate snapshot from %s", _SNAPSHOT_PATH)
        return None


def _rehydrate_report(data: dict) -> Report:
    """Reconstruct a Report dataclass from a raw deserialized dict."""
    total = RunMetrics(**data["total"])
    per_category = {
        Category(k): RunMetrics(**v)
        for k, v in data["per_category"].items()
    }
    per_layer = {k: RunMetrics(**v) for k, v in data["per_layer"].items()}
    samples = [_rehydrate_sample(s) for s in data.get("samples", [])]
    pm_data = data.get("per_mechanism", {})
    per_mechanism = (
        MechanismStats(**pm_data) if pm_data else MechanismStats(0, 0, 0, 0, 0)
    )
    return Report(
        total=total,
        per_category=per_category,
        per_layer=per_layer,
        samples=samples,
        per_mechanism=per_mechanism,
    )


def _rehydrate_sample(s: dict) -> SampleResult:
    """Reconstruct a SampleResult from a raw dict."""
    fps = [_rehydrate_finding(f) for f in s.get("false_positives", [])]
    fns = [_rehydrate_labeled_finding(f) for f in s.get("false_negatives", [])]
    return SampleResult(text=s["text"], false_positives=fps, false_negatives=fns)


def _rehydrate_finding(f: dict) -> Finding:
    """Reconstruct a Finding from a raw dict, restoring Category enum."""
    return Finding(
        category=Category(f["category"]),
        start=f["start"],
        end=f["end"],
        text_span=f["text_span"],
        confidence=f["confidence"],
        source=f["source"],
        metadata=f.get("metadata"),
    )


def _rehydrate_labeled_finding(f: dict) -> LabeledFinding:
    """Reconstruct a LabeledFinding from a raw dict, restoring Category enum."""
    return LabeledFinding(
        category=Category(f["category"]),
        start=f["start"],
        end=f["end"],
        text_span=f["text_span"],
    )
