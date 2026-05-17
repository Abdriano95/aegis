"""Snapshot loader for demo evaluation results.

Loads and rehydrates a pre-generated JSON snapshot back into typed Report dataclasses.
Returns None if the snapshot file is missing or malformed.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, fields
from pathlib import Path

from evaluation.dataset.labeled_finding import LabeledFinding
from evaluation.report import DimensionStats, Report, RunMetrics, SampleResult
from gdpr_classifier.core.category import Category
from gdpr_classifier.core.finding import Finding
from demo.snapshot_descriptions import get_description

_LOG = logging.getLogger(__name__)

_SNAPSHOT_PATH = (
    Path(__file__).resolve().parent / "snapshots" / "i7d_cross_validating.json"
)


@dataclass(frozen=True)
class SnapshotData:
    """Container for a loaded and rehydrated evaluation snapshot.

    ``evidence_basis_breakdown`` carries the optional top-level
    cross-validating mechanism breakdown (present in i7d-snapshots only);
    it is exposed raw so the report/analysis views can render it.
    """

    metadata: dict
    report: Report
    evidence_basis_breakdown: dict | None = None


@dataclass(frozen=True)
class SnapshotInfo:
    """Lightweight catalogue entry for a discoverable snapshot file."""

    filename: str
    path: Path
    metadata: dict
    description: str


def load_snapshot() -> SnapshotData | None:
    """Load the default snapshot and return a rehydrated SnapshotData, or None."""
    return load_snapshot_file(_SNAPSHOT_PATH)


def load_snapshot_file(path: Path) -> SnapshotData | None:
    """Load and rehydrate an arbitrary snapshot file, or None on failure.

    Extra top-level keys (cross_validation_mode, baseline_iteration_2,
    instrument_fn, sanity_check, llm_failures, ...) are ignored;
    ``evidence_basis_breakdown`` is captured when present.
    """
    if not path.exists():
        _LOG.info("Snapshot file not found at %s", path)
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        report = _rehydrate_report(raw["report"])
        return SnapshotData(
            metadata=raw.get("metadata", {}),
            report=report,
            evidence_basis_breakdown=raw.get("evidence_basis_breakdown"),
        )
    except (json.JSONDecodeError, FileNotFoundError, KeyError, ValueError):
        _LOG.exception("Failed to load or rehydrate snapshot from %s", path)
        return None


def list_snapshots() -> list[SnapshotInfo]:
    """Discover loadable top-level snapshots in the snapshots directory.

    Scans ``*.json`` at the top level only (non-recursive → the
    ``pre_num_ctx_fix/`` subdirectory and ``.log``/``.gitkeep`` files are
    excluded). Files that fail to load/rehydrate are skipped with a warning
    rather than aborting the scan. Sorted by filename.
    """
    snapshots_dir = _SNAPSHOT_PATH.parent
    infos: list[SnapshotInfo] = []
    for path in sorted(snapshots_dir.glob("*.json")):
        data = load_snapshot_file(path)
        if data is None:
            _LOG.warning("Skipping unloadable snapshot %s", path.name)
            continue
        infos.append(
            SnapshotInfo(
                filename=path.name,
                path=path,
                metadata=data.metadata,
                description=get_description(path.name),
            )
        )
    return infos


def _rehydrate_report(data: dict) -> Report:
    """Reconstruct a Report dataclass from a raw deserialized dict.

    Iteration 2-snapshot innehåller en ``per_mechanism``-nyckel som hörde
    till en tidigare modell (MechanismStats borttagen i fixup av Beslut 49
    reviderad). Nyckeln ignoreras tyst om den finns.

    Pre-I-5-snapshots bär ett äldre ``per_dimension``-schema
    (identifiability_low/medium/high, data_class_ordinary). Ett
    inkompatibelt schema degraderas tyst till tom DimensionStats — vi
    fabricerar inte värden — så att övriga nivåer ändå kan jämföras och
    analysvyn visar "Data saknas för denna nivå".
    """
    total = RunMetrics(**data["total"])
    per_category = {
        Category(k): RunMetrics(**v)
        for k, v in data["per_category"].items()
    }
    per_layer = {k: RunMetrics(**v) for k, v in data["per_layer"].items()}
    samples = [_rehydrate_sample(s) for s in data.get("samples", [])]
    pd_data = data.get("per_dimension", {})
    _dim_fields = {f.name for f in fields(DimensionStats)}
    if pd_data and set(pd_data).issubset(_dim_fields):
        per_dimension = DimensionStats(**pd_data)
    else:
        per_dimension = DimensionStats()
    return Report(
        total=total,
        per_category=per_category,
        per_layer=per_layer,
        samples=samples,
        per_dimension=per_dimension,
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
