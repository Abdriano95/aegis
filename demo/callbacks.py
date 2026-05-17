"""Dash callbacks and evaluation logic."""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from pathlib import Path

from dash import Input, Output, State, callback, ctx, dash_table, dcc, html

from evaluation.dataset.loader import load_dataset
from evaluation.report import DimensionStats, Report
from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.config import get_llm_provider
from gdpr_classifier.core.classification import Classification
from gdpr_classifier.core.finding import Finding
from gdpr_classifier.layers.article9 import Article9Layer
from gdpr_classifier.layers.combination import CombinationLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.llm.provider import LLMProviderError
from gdpr_classifier.layers.pattern import PatternLayer
from demo.layout import _DEMO_TEXTS, analysis_tab_layout, freetext_tab_layout
from demo.snapshot_loader import (
    SnapshotData,
    SnapshotInfo,
    list_snapshots,
    load_snapshot,
    load_snapshot_file,
)

_LOG = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_DATASET_PATHS = {
    "iteration_1": _PROJECT_ROOT / "tests" / "data" / "iteration_1" / "test_dataset.json",
    "article9": _PROJECT_ROOT / "tests" / "data" / "iteration_2" / "article9_dataset.json",
    "combination": _PROJECT_ROOT / "tests" / "data" / "iteration_2" / "combination_dataset.json",
}


def _context_snippet(text: str, start: int, end: int, window: int = 20) -> str:
    """Return a short snippet of ``text`` around ``[start, end)`` with ellipses."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    prefix = "..." if ctx_start > 0 else ""
    suffix = "..." if ctx_end < len(text) else ""
    return f"{prefix}{text[ctx_start:ctx_end]}{suffix}"


def build_pipeline() -> Pipeline:
    """Construct the demo's iteration 2 four-layer pipeline."""
    provider = get_llm_provider("qwen3:14b")
    return Pipeline(
        layers=[
            PatternLayer(),
            EntityLayer(),
            Article9Layer(provider),
            CombinationLayer(provider),
        ],
        aggregator=Aggregator(),
    )


_FREETEXT_PIPELINE: Pipeline | None = None
_FREETEXT_PIPELINE_LOCK = threading.Lock()


def _get_freetext_pipeline() -> Pipeline:
    global _FREETEXT_PIPELINE
    with _FREETEXT_PIPELINE_LOCK:
        if _FREETEXT_PIPELINE is None:
            _FREETEXT_PIPELINE = build_pipeline()
    return _FREETEXT_PIPELINE


_SNAPSHOT_CACHE: SnapshotData | None = None
_SNAPSHOT_INITIALIZED: bool = False
_SNAPSHOT_LOCK = threading.Lock()


def _get_snapshot() -> SnapshotData | None:
    """Return the cached snapshot, retrying each call until a file is found."""
    global _SNAPSHOT_CACHE, _SNAPSHOT_INITIALIZED
    if not _SNAPSHOT_INITIALIZED:
        with _SNAPSHOT_LOCK:
            if not _SNAPSHOT_INITIALIZED:
                result = load_snapshot()
                if result is not None:
                    _SNAPSHOT_CACHE = result
                    _SNAPSHOT_INITIALIZED = True
    return _SNAPSHOT_CACHE


# ---------------------------------------------------------------------------
# Helper: build Dash DataTable from a list of dicts
# ---------------------------------------------------------------------------


def _make_table(
    table_id: str,
    columns: list[dict],
    data: list[dict],
    extra_conditional: list[dict] | None = None,
) -> dash_table.DataTable:
    conditional: list[dict] = [
        {"if": {"row_index": "odd"}, "backgroundColor": "#f9f9f9"},
    ]
    if extra_conditional:
        conditional = conditional + extra_conditional
    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=data,
        style_table={"overflowX": "auto", "marginBottom": "24px"},
        style_header={
            "backgroundColor": "#2c3e50",
            "color": "white",
            "fontWeight": "bold",
        },
        style_cell={
            "textAlign": "center",
            "padding": "8px",
            "minWidth": "80px",
        },
        style_data_conditional=conditional,
    )


# ---------------------------------------------------------------------------
# Column definitions (pure constants; safe at import time)
# ---------------------------------------------------------------------------

_TOTAL_COLUMNS = [
    {"name": "Metric", "id": "metric"},
    {"name": "TP", "id": "tp"},
    {"name": "FP", "id": "fp"},
    {"name": "FN", "id": "fn"},
    {"name": "Precision", "id": "precision"},
    {"name": "Recall", "id": "recall"},
    {"name": "F1", "id": "f1"},
]

_CATEGORY_COLUMNS = [
    {"name": "Kategori", "id": "category"},
    {"name": "TP", "id": "tp"},
    {"name": "FP", "id": "fp"},
    {"name": "FN", "id": "fn"},
    {"name": "Precision", "id": "precision"},
    {"name": "Recall", "id": "recall"},
    {"name": "F1", "id": "f1"},
]

_LAYER_COLUMNS = [
    {"name": "Lager", "id": "layer"},
    {"name": "TP", "id": "tp"},
    {"name": "FP", "id": "fp"},
    {"name": "FN", "id": "fn"},
    {"name": "Precision", "id": "precision"},
    {"name": "Recall", "id": "recall"},
    {"name": "F1", "id": "f1"},
]

_DIMENSION_COLUMNS = [
    {"name": "Dimension", "id": "dimension"},
    {"name": "Nivå", "id": "level"},
    {"name": "Antal", "id": "count"},
]

_FP_COLUMNS = [
    {"name": "Källa", "id": "source"},
    {"name": "Matchad text", "id": "text_span"},
    {"name": "Start", "id": "start"},
    {"name": "End", "id": "end"},
    {"name": "Kontext", "id": "context"},
]

_FN_COLUMNS = [
    {"name": "Kategori", "id": "category"},
    {"name": "Förväntad text", "id": "text_span"},
    {"name": "Start", "id": "start"},
    {"name": "End", "id": "end"},
    {"name": "Kontext", "id": "context"},
]

_TESTDATA_COLUMNS = [
    {"name": "#", "id": "index"},
    {"name": "Beskrivning", "id": "description"},
    {"name": "Text", "id": "text"},
    {"name": "Förväntade fynd", "id": "expected"},
]

# ---------------------------------------------------------------------------
# Row builders (pure functions over a Report/dataset)
# ---------------------------------------------------------------------------


def _total_rows(report: Report) -> list[dict]:
    return [
        {
            "metric": "Totalt",
            "tp": report.total.tp,
            "fp": report.total.fp,
            "fn": report.total.fn,
            "precision": f"{report.total.precision:.2%}",
            "recall": f"{report.total.recall:.2%}",
            "f1": f"{report.total.f1:.2%}",
        },
    ]


def _category_rows(report: Report) -> list[dict]:
    return [
        {
            "category": cat.value,
            "tp": m.tp,
            "fp": m.fp,
            "fn": m.fn,
            "precision": f"{m.precision:.2%}",
            "recall": f"{m.recall:.2%}",
            "f1": f"{m.f1:.2%}",
        }
        for cat, m in sorted(report.per_category.items(), key=lambda x: x[0].value)
    ]


def _layer_rows(report: Report) -> list[dict]:
    return [
        {
            "layer": layer,
            "tp": m.tp,
            "fp": m.fp,
            "fn": m.fn,
            "precision": f"{m.precision:.2%}",
            "recall": "N/A",
            "f1": "N/A",
        }
        for layer, m in sorted(report.per_layer.items())
    ]


def _dimension_rows(stats: DimensionStats) -> list[dict]:
    rows = [
        ("Identifiability", "NONE", stats.identifiability_none),
        ("Identifiability", "INDIRECT", stats.identifiability_indirect),
        ("Identifiability", "DIRECT", stats.identifiability_direct),
        ("Data class", "NONE", stats.data_class_none),
        ("Data class", "SPECIAL", stats.data_class_special),
        ("Data class", "CRIMINAL", stats.data_class_criminal),
    ]
    return [
        {"dimension": dim, "level": level, "count": count}
        for dim, level, count in rows
    ]


def _fp_rows(report: Report) -> list[dict]:
    return [
        {
            "source": fp.source,
            "text_span": fp.text_span,
            "start": fp.start,
            "end": fp.end,
            "context": _context_snippet(sample.text, fp.start, fp.end),
        }
        for sample in report.samples
        for fp in sample.false_positives
    ]


def _fn_rows(report: Report) -> list[dict]:
    return [
        {
            "category": fn.category.value,
            "text_span": fn.text_span,
            "start": fn.start,
            "end": fn.end,
            "context": _context_snippet(sample.text, fn.start, fn.end),
        }
        for sample in report.samples
        for fn in sample.false_negatives
    ]


def _testdata_rows(dataset: list) -> list[dict]:
    return [
        {
            "index": i + 1,
            "description": item.description,
            "text": item.text,
            "expected": ", ".join(
                f"{f.category.value} ({f.text_span})" for f in item.expected_findings
            )
            or "(inga)",
        }
        for i, item in enumerate(dataset)
    ]


# ---------------------------------------------------------------------------
# Curated metadata row + badges (shared by report & analysis tabs)
# ---------------------------------------------------------------------------


def _meta_mode(meta: dict) -> str:
    """Aggregator mode, defaulting to 'legacy' for pre-I-7g snapshots."""
    return meta.get("cross_validation_mode") or meta.get("mode") or "legacy"


def _badge(text: str, bg: str) -> html.Span:
    return html.Span(
        text,
        style={
            "backgroundColor": bg,
            "color": "white",
            "fontWeight": "bold",
            "borderRadius": "4px",
            "padding": "2px 8px",
            "marginRight": "8px",
            "fontSize": "12px",
        },
    )


def _metadata_row(meta: dict, prefix: str = "") -> html.Div:
    """Compact curated metadata row: model + mode badges then labelled text.

    Every field is read defensively so older snapshots that lack a field
    degrade to '?' rather than raising.
    """
    mode = _meta_mode(meta)
    mode_bg = "#27ae60" if mode == "cross_validating" else "#7f8c8d"
    date = (meta.get("generated_at") or "?")[:10]
    commit = (meta.get("git_commit") or "?")[:8]
    subset = meta.get("subset") or "all"
    texts = (meta.get("dataset") or {}).get("total_texts", "?")
    pv = meta.get("prompt_versions") or {}
    children: list = []
    if prefix:
        children.append(html.Strong(prefix))
    children.extend(
        [
            _badge(meta.get("model", "?"), "#2c3e50"),
            _badge(mode, mode_bg),
            html.Span(
                f"Datum: {date} · Commit: {commit} · Subset: {subset} · "
                f"Texter: {texts} · Prompts: article9 {pv.get('article9', '?')}, "
                f"combination {pv.get('combination', '?')}"
            ),
        ]
    )
    return html.Div(
        children,
        style={"marginBottom": "12px", "fontSize": "13px", "color": "#555"},
    )


def _snapshot_option_label(info: SnapshotInfo) -> str:
    """Dropdown label: description + filename + model + mode + subset (issue AC)."""
    m = info.metadata
    return (
        f"{info.description} — {info.filename} · "
        f"{m.get('model', '?')} · {_meta_mode(m)} · {m.get('subset') or 'all'}"
    )


# ---------------------------------------------------------------------------
# Evidence basis breakdown (i7d-snapshots only)
# ---------------------------------------------------------------------------

_EBB_MECHANISMS = (
    "structural_support",
    "high_confidence_no_support",
    "no_support_required",
)

_EBB_COLUMNS = [
    {"name": "Mekanism", "id": "mechanism"},
    {"name": "TP", "id": "tp"},
    {"name": "FP", "id": "fp"},
]


def _ebb_rows(block: dict) -> list[dict]:
    rows = []
    for m in _EBB_MECHANISMS:
        cell = block.get(m) or {}
        rows.append(
            {"mechanism": m, "tp": cell.get("tp", "–"), "fp": cell.get("fp", "–")}
        )
    return rows


def _evidence_basis_section(
    ebb: dict | None,
    heading: str,
    id_prefix: str,
) -> list:
    """Render the evidence-basis breakdown (total + context_kombination_only).

    Returns [] when ``ebb`` is missing/empty (section stays invisible).
    Falls back to a notice instead of crashing on an unexpected structure.
    """
    if not ebb:
        return []
    try:
        children: list = [html.H3(heading)]
        for key, label in (
            ("total", "Total"),
            ("context_kombination_only", "Endast context.kombination"),
        ):
            block = ebb.get(key)
            if not isinstance(block, dict):
                continue
            children.append(html.H4(label, style={"marginBottom": "4px"}))
            children.append(
                _make_table(f"{id_prefix}-ebb-{key}", _EBB_COLUMNS, _ebb_rows(block))
            )
        note = ebb.get("note")
        if note:
            children.append(
                html.P(
                    note,
                    style={
                        "fontSize": "12px",
                        "color": "#555",
                        "fontStyle": "italic",
                    },
                )
            )
        return children
    except (KeyError, TypeError, AttributeError):
        return [
            html.H3(heading),
            html.P("Evidence basis-data finns men kan inte renderas"),
        ]


# ---------------------------------------------------------------------------
# Snapshot comparison (analysis tab)
# ---------------------------------------------------------------------------

_COMPARE_DIMENSION_COLUMNS = [
    {"name": "Dimension", "id": "dimension"},
    {"name": "Nivå", "id": "level"},
    {"name": "A Antal", "id": "a_count"},
    {"name": "B Antal", "id": "b_count"},
    {"name": "Δ", "id": "d_count"},
]


def _compare_columns(level_name: str) -> list[dict]:
    cols = [{"name": level_name, "id": "level"}]
    for side in ("A", "B"):
        for f in ("TP", "FP", "FN", "P", "R", "F1"):
            cols.append({"name": f"{side} {f}", "id": f"{side.lower()}_{f.lower()}"})
    for f in ("P", "R", "F1"):
        cols.append({"name": f"Δ {f}", "id": f"d_{f.lower()}"})
    return cols


def _fmt_pct(x) -> str:
    return f"{x:.2%}" if isinstance(x, (int, float)) else "–"


def _delta_pp(a, b) -> str:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return f"{(b - a) * 100:+.1f} pp"
    return "—"


def _compare_metric_row(level: str, a, b, *, suppress_rf: bool = False) -> dict:
    """One comparison row for a pair of optional RunMetrics (A vs B).

    ``suppress_rf`` mirrors the report tab's per-layer convention where
    recall/F1 are not meaningful (cross-layer FN attribution) → shown N/A.
    """
    row: dict = {"level": level}
    for side, m in (("a", a), ("b", b)):
        if m is None:
            for k in ("tp", "fp", "fn", "p", "r", "f1"):
                row[f"{side}_{k}"] = "–"
            continue
        row[f"{side}_tp"] = m.tp
        row[f"{side}_fp"] = m.fp
        row[f"{side}_fn"] = m.fn
        row[f"{side}_p"] = _fmt_pct(m.precision)
        row[f"{side}_r"] = "N/A" if suppress_rf else _fmt_pct(m.recall)
        row[f"{side}_f1"] = "N/A" if suppress_rf else _fmt_pct(m.f1)
    row["d_p"] = _delta_pp(
        a.precision if a else None, b.precision if b else None
    )
    if suppress_rf:
        row["d_r"] = row["d_f1"] = "—"
    else:
        row["d_r"] = _delta_pp(a.recall if a else None, b.recall if b else None)
        row["d_f1"] = _delta_pp(a.f1 if a else None, b.f1 if b else None)
    return row


def _compare_total_rows(a_rep, b_rep) -> list[dict]:
    return [_compare_metric_row("Totalt", a_rep.total, b_rep.total)]


def _compare_category_rows(a_rep, b_rep) -> list[dict]:
    cats = sorted(
        set(a_rep.per_category) | set(b_rep.per_category), key=lambda c: c.value
    )
    return [
        _compare_metric_row(
            c.value, a_rep.per_category.get(c), b_rep.per_category.get(c)
        )
        for c in cats
    ]


def _compare_layer_rows(a_rep, b_rep) -> list[dict]:
    layers = sorted(set(a_rep.per_layer) | set(b_rep.per_layer))
    return [
        _compare_metric_row(
            layer,
            a_rep.per_layer.get(layer),
            b_rep.per_layer.get(layer),
            suppress_rf=True,
        )
        for layer in layers
    ]


_DIMENSION_SPEC = [
    ("Identifiability", "NONE", "identifiability_none"),
    ("Identifiability", "INDIRECT", "identifiability_indirect"),
    ("Identifiability", "DIRECT", "identifiability_direct"),
    ("Data class", "NONE", "data_class_none"),
    ("Data class", "SPECIAL", "data_class_special"),
    ("Data class", "CRIMINAL", "data_class_criminal"),
]


def _dimension_is_empty(stats) -> bool:
    return all(getattr(stats, attr) == 0 for _, _, attr in _DIMENSION_SPEC)


def _compare_dimension_rows(a_rep, b_rep) -> list[dict]:
    a, b = a_rep.per_dimension, b_rep.per_dimension
    rows = []
    for dim, lvl, attr in _DIMENSION_SPEC:
        av, bv = getattr(a, attr), getattr(b, attr)
        rows.append(
            {
                "dimension": dim,
                "level": lvl,
                "a_count": av,
                "b_count": bv,
                "d_count": f"{bv - av:+d}",
            }
        )
    return rows


def _delta_conditional(col_ids: list[str]) -> list[dict]:
    """Green for improvements (+), red for regressions (-); neutral otherwise."""
    rules: list[dict] = []
    for cid in col_ids:
        rules.append(
            {
                "if": {"filter_query": f'{{{cid}}} contains "-"', "column_id": cid},
                "color": "#c0392b",
                "fontWeight": "bold",
            }
        )
        rules.append(
            {
                "if": {"filter_query": f'{{{cid}}} contains "+"', "column_id": cid},
                "color": "#1e8449",
                "fontWeight": "bold",
            }
        )
    return rules


def _side_by_side(left, right) -> html.Div:
    """Two equal-width columns that wrap to two stacked rows on narrow viewports.

    ``left``/``right`` may be a single component or a list of components.
    """
    col_style = {"flex": "1", "minWidth": "300px"}
    return html.Div(
        [
            html.Div(left, style=col_style),
            html.Div(right, style=col_style),
        ],
        style={"display": "flex", "gap": "16px", "flexWrap": "wrap"},
    )


# ---------------------------------------------------------------------------
# Freetext helpers
# ---------------------------------------------------------------------------

_SOURCE_COLORS: dict[str, str] = {
    "pattern": "orange",
    "entity": "#add8e6",
    "article9": "#ffb6c1",
    "context_signal": "#90ee90",
    "context_kombination": "#dda0dd",
}


def _resolve_overlaps(findings: list[Finding]) -> list[Finding]:
    """Return a non-overlapping subset of findings, preferring highest confidence."""
    if not findings:
        return []
    sorted_findings = sorted(findings, key=lambda f: (f.start, -f.confidence))
    clusters: list[list[Finding]] = []
    current_cluster: list[Finding] = [sorted_findings[0]]
    cluster_end = sorted_findings[0].end
    for f in sorted_findings[1:]:
        if f.start < cluster_end:
            current_cluster.append(f)
            cluster_end = max(cluster_end, f.end)
        else:
            clusters.append(current_cluster)
            current_cluster = [f]
            cluster_end = f.end
    clusters.append(current_cluster)
    return [max(cluster, key=lambda f: (f.confidence, -f.start)) for cluster in clusters]


def _get_layer_key(source: str) -> str:
    """Map a finding's source field to a _SOURCE_COLORS lookup key."""
    if source == "context.kombination":
        return "context_kombination"
    prefix = source.split(".")[0]
    return "context_signal" if prefix == "context" else prefix


def _build_finding_tooltip(f: Finding) -> str:
    """Build source-specific tooltip text for a finding."""
    if f.source == "context.kombination":
        meta = f.metadata or {}
        vp = meta.get("validation_path", "")
        reasoning = meta.get("reasoning", "")
        return (
            f"Aggregat-fynd. Konfidens: {f.confidence:.0%}. "
            f"Validation path: {vp}. Reasoning: {reasoning}"
        )
    if f.source.startswith("context."):
        return (
            f"Signal: {f.category.value}, "
            f"Källa: {f.source}, "
            f"Konfidens: {f.confidence:.0%}"
        )
    return (
        f"Kategori: {f.category.value}, "
        f"Källa: {f.source}, "
        f"Konfidens: {f.confidence:.0%}"
    )


def _render_findings_segment(
    text: str, start: int, end: int, findings: list[Finding]
) -> list:
    """Render text[start:end] with highlighted inner findings.

    findings must be non-overlapping and sorted by start, all within [start, end).
    """
    spans: list = []
    cursor = start
    for f in findings:
        if cursor < f.start:
            spans.append(html.Span(text[cursor : f.start]))
        bg = _SOURCE_COLORS.get(_get_layer_key(f.source), "#e0e0e0")
        spans.append(
            html.Span(
                text[f.start : f.end],
                title=_build_finding_tooltip(f),
                style={
                    "backgroundColor": bg,
                    "borderRadius": "3px",
                    "padding": "1px 2px",
                    "cursor": "help",
                },
            )
        )
        cursor = f.end
    if cursor < end:
        spans.append(html.Span(text[cursor:end]))
    return spans


def build_highlighted_text(text: str, findings: list[Finding]) -> list:
    """Build a list of html.Span components with colour-coded, annotated findings.

    Aggregate findings (context.kombination) render as outer wrapper spans containing
    inner highlighted findings. Non-aggregate findings outside any aggregate span
    render as flat highlighted spans. No findings are discarded.
    """
    aggregates = sorted(
        [f for f in findings if f.source == "context.kombination"],
        key=lambda f: f.start,
    )
    non_agg = [f for f in findings if f.source != "context.kombination"]
    resolved = sorted(_resolve_overlaps(non_agg), key=lambda f: f.start)

    if not aggregates:
        return _render_findings_segment(text, 0, len(text), resolved)

    spans: list = []
    cursor = 0

    for agg in aggregates:
        # Render text and non-aggregate findings between cursor and aggregate start
        between = [f for f in resolved if f.start >= cursor and f.end <= agg.start]
        spans.extend(_render_findings_segment(text, cursor, agg.start, between))

        # Non-aggregate findings fully contained within this aggregate span
        inner = [f for f in resolved if f.start >= agg.start and f.end <= agg.end]
        inner_content = _render_findings_segment(text, agg.start, agg.end, inner)

        spans.append(
            html.Span(
                inner_content,
                title=_build_finding_tooltip(agg),
                style={
                    "backgroundColor": _SOURCE_COLORS["context_kombination"],
                    "borderRadius": "3px",
                    "padding": "1px 2px",
                    "cursor": "help",
                },
            )
        )
        cursor = agg.end

    # Render remaining text and findings after the last aggregate
    post = [f for f in resolved if f.start >= cursor]
    spans.extend(_render_findings_segment(text, cursor, len(text), post))
    return spans


def build_summary(classification: Classification) -> html.Div:
    """Build a summary panel from a Classification result."""
    level = classification.sensitivity.value.upper()
    level_colors = {
        "NONE": "#27ae60",
        "LOW": "#f39c12",
        "MEDIUM": "#e67e22",
        "HIGH": "#e74c3c",
    }
    level_bg = level_colors.get(level, "#95a5a6")

    identifiability_level = classification.identifiability.value.upper()
    identifiability_colors = {
        "NONE": "#bdc3c7",      # ljusgrå
        "INDIRECT": "#3498db",  # mellanblå
        "DIRECT": "#1f618d",    # mörkblå
    }
    identifiability_bg = identifiability_colors.get(identifiability_level, "#95a5a6")

    data_class_level = classification.data_class.value.upper()
    data_class_colors = {
        "NONE": "#bdc3c7",      # ljusgrå
        "SPECIAL": "#8e44ad",   # mellanlila
        "CRIMINAL": "#5b2c6f",  # mörklila
    }
    data_class_bg = data_class_colors.get(data_class_level, "#95a5a6")

    per_category: dict[str, int] = defaultdict(int)
    per_layer: dict[str, int] = defaultdict(int)
    for f in classification.findings:
        per_category[f.category.value] += 1
        per_layer[f.source.split(".")[0]] += 1

    table_style = {"borderCollapse": "collapse", "marginTop": "8px", "width": "auto"}
    cell_style = {"border": "1px solid #ccc", "padding": "4px 12px"}

    category_rows = [
        html.Tr(
            [
                html.Td(cat, style=cell_style),
                html.Td(str(count), style=cell_style),
            ]
        )
        for cat, count in sorted(per_category.items())
    ]
    layer_rows = [
        html.Tr(
            [
                html.Td(layer, style=cell_style),
                html.Td(str(count), style=cell_style),
            ]
        )
        for layer, count in sorted(per_layer.items())
    ]

    sorted_findings = sorted(classification.findings, key=lambda f: f.start)
    all_finding_rows = [
        html.Tr(
            [
                html.Td(f.text_span, style=cell_style),
                html.Td(f.category.value, style=cell_style),
                html.Td(f.source.split(".")[0], style=cell_style),
                html.Td(f"{f.confidence:.0%}", style=cell_style),
                html.Td(f"{f.start}–{f.end}", style=cell_style),
            ]
        )
        for f in sorted_findings
    ]

    return html.Div(
        [
            html.Hr(),
            html.H3("Sammanfattning", style={"marginBottom": "8px"}),
            html.Div(
                f"Känslighetsnivå: {level}",
                style={
                    "display": "inline-block",
                    "backgroundColor": level_bg,
                    "color": "white",
                    "fontWeight": "bold",
                    "padding": "4px 14px",
                    "borderRadius": "4px",
                    "marginBottom": "16px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "Identifierbarhet",
                                style={
                                    "fontWeight": "bold",
                                    "fontSize": "13px",
                                    "marginBottom": "4px",
                                },
                            ),
                            html.Div(
                                identifiability_level,
                                style={
                                    "display": "inline-block",
                                    "backgroundColor": identifiability_bg,
                                    "color": "white",
                                    "fontWeight": "bold",
                                    "fontSize": "13px",
                                    "padding": "2px 10px",
                                    "borderRadius": "4px",
                                },
                            ),
                            html.Div(
                                "Direkt (artikel 4), indirekt via pusselbitseffekt (skäl 26) eller ingen identifiering.",
                                style={
                                    "fontSize": "12px",
                                    "color": "#555",
                                    "marginTop": "4px",
                                },
                            ),
                        ],
                        style={
                            "marginRight": "40px",
                            "display": "inline-block",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                "Dataskyddsklass",
                                style={
                                    "fontWeight": "bold",
                                    "fontSize": "13px",
                                    "marginBottom": "4px",
                                },
                            ),
                            html.Div(
                                data_class_level,
                                style={
                                    "display": "inline-block",
                                    "backgroundColor": data_class_bg,
                                    "color": "white",
                                    "fontWeight": "bold",
                                    "fontSize": "13px",
                                    "padding": "2px 10px",
                                    "borderRadius": "4px",
                                },
                            ),
                            html.Div(
                                "Särskilda kategorier (artikel 9), uppgifter om brott (artikel 10) eller ingen känslig data.",
                                style={
                                    "fontSize": "12px",
                                    "color": "#555",
                                    "marginTop": "4px",
                                },
                            ),
                        ],
                        style={"display": "inline-block", "verticalAlign": "top"},
                    ),
                ],
                style={"marginBottom": "16px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong("Fynd per GDPR-kategori"),
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Kategori", style=cell_style),
                                                html.Th("Antal", style=cell_style),
                                            ]
                                        )
                                    ),
                                    html.Tbody(category_rows),
                                ],
                                style=table_style,
                            )
                            if category_rows
                            else html.P("Inga fynd."),
                        ],
                        style={
                            "marginRight": "40px",
                            "display": "inline-block",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Div(
                        [
                            html.Strong("Fynd per lager"),
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Lager", style=cell_style),
                                                html.Th("Antal", style=cell_style),
                                            ]
                                        )
                                    ),
                                    html.Tbody(layer_rows),
                                ],
                                style=table_style,
                            )
                            if layer_rows
                            else html.P("Inga fynd."),
                        ],
                        style={
                            "marginRight": "40px",
                            "display": "inline-block",
                            "verticalAlign": "top",
                        },
                    ),
                    html.Div(
                        [
                            html.Strong("Alla fynd"),
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Text", style=cell_style),
                                                html.Th("Kategori", style=cell_style),
                                                html.Th("Lager", style=cell_style),
                                                html.Th("Konfidens", style=cell_style),
                                                html.Th("Position", style=cell_style),
                                            ]
                                        )
                                    ),
                                    html.Tbody(all_finding_rows),
                                ],
                                style=table_style,
                            )
                            if all_finding_rows
                            else html.P("Inga fynd."),
                        ],
                        style={"display": "inline-block", "verticalAlign": "top"},
                    ),
                ]
            ),
        ],
        style={"marginTop": "16px"},
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
)
def render_tab(tab: str) -> html.Div:
    """Switch between report, testdata and freetext views."""
    if tab == "tab-report":
        return html.Div(
            [
                html.H2("Utvärderingsrapport"),
                dcc.Checklist(
                    id="verbose-toggle",
                    options=[{"label": " Visa detaljerad data", "value": "verbose"}],
                    value=[],
                    style={"marginBottom": "16px"},
                ),
                html.Div(id="report-content"),
            ],
        )
    if tab == "tab-analysis":
        options = [
            {"label": _snapshot_option_label(info), "value": info.filename}
            for info in list_snapshots()
        ]
        return analysis_tab_layout(options)
    if tab == "tab-testdata":
        try:
            d1 = load_dataset(str(_DATASET_PATHS["iteration_1"]))
            d2 = load_dataset(str(_DATASET_PATHS["article9"]))
            d3 = load_dataset(str(_DATASET_PATHS["combination"]))
        except (OSError, json.JSONDecodeError, ValueError):
            _LOG.exception("Failed to load test datasets")
            return html.Div(
                [
                    html.H2("Testdata"),
                    html.P("Kunde inte läsa testdatafilerna. Kontrollera att filerna finns."),
                ]
            )
        dataset = d1 + d2 + d3
        rows = _testdata_rows(dataset)
        return html.Div(
            [
                html.H2("Testdata"),
                html.P(
                    f"Visar {len(rows)} testfall: {len(d1)} iteration-1, "
                    f"{len(d2)} artikel-9, {len(d3)} kombination."
                ),
                _make_table("testdata-table", _TESTDATA_COLUMNS, rows),
            ]
        )
    if tab == "tab-freetext":
        return freetext_tab_layout()
    return html.Div()


@callback(
    Output("report-content", "children"),
    Input("verbose-toggle", "value"),
)
def update_report(verbose_values: list[str]) -> list:
    """Render the evaluation report tables based on the verbose toggle."""
    snapshot = _get_snapshot()
    if snapshot is None:
        return [
            html.Div(
                [
                    html.H3("Snapshot saknas"),
                    html.P(
                        "Snapshot saknas. Kör `python scripts/build_demo_snapshot.py` "
                        "för att generera den."
                    ),
                ]
            )
        ]

    report = snapshot.report
    meta = snapshot.metadata
    verbose = "verbose" in (verbose_values or [])

    children: list = [
        _metadata_row(meta),
        html.H3("Totala mätvärden"),
        _make_table("total-table", _TOTAL_COLUMNS, _total_rows(report)),
        html.H3("Per kategori"),
        _make_table("category-table", _CATEGORY_COLUMNS, _category_rows(report)),
        html.H3("Per lager"),
        _make_table("layer-table", _LAYER_COLUMNS, _layer_rows(report)),
        html.H3("Per dimension"),
        _make_table("dimension-table", _DIMENSION_COLUMNS, _dimension_rows(report.per_dimension)),
    ]
    children.extend(
        _evidence_basis_section(
            snapshot.evidence_basis_breakdown,
            "Evidence basis (cross-validating-mekanismer)",
            id_prefix="report",
        )
    )

    if verbose:
        fp_data = _fp_rows(report)
        fn_data = _fn_rows(report)
        children.extend(
            [
                html.H3(f"False Positives ({len(fp_data)})"),
                (
                    _make_table("fp-table", _FP_COLUMNS, fp_data)
                    if fp_data
                    else html.P("Inga false positives.")
                ),
                html.H3(f"False Negatives ({len(fn_data)})"),
                (
                    _make_table("fn-table", _FN_COLUMNS, fn_data)
                    if fn_data
                    else html.P("Inga false negatives.")
                ),
            ],
        )

    return children


_DELTA_METRIC_COLS = ["d_p", "d_r", "d_f1"]


def _comparison_level(
    level: str, a_rep, b_rep
) -> list:
    """Render one comparison level, or a 'data saknas' notice if absent in both."""
    if level == "total":
        return [
            html.H3("Total"),
            _make_table(
                "cmp-total",
                _compare_columns("Metric"),
                _compare_total_rows(a_rep, b_rep),
                extra_conditional=_delta_conditional(_DELTA_METRIC_COLS),
            ),
        ]
    if level == "category":
        if not a_rep.per_category or not b_rep.per_category:
            return [html.H3("Per kategori"), html.P("Data saknas för denna nivå")]
        return [
            html.H3("Per kategori"),
            _make_table(
                "cmp-category",
                _compare_columns("Kategori"),
                _compare_category_rows(a_rep, b_rep),
                extra_conditional=_delta_conditional(_DELTA_METRIC_COLS),
            ),
        ]
    if level == "layer":
        if not a_rep.per_layer or not b_rep.per_layer:
            return [html.H3("Per lager"), html.P("Data saknas för denna nivå")]
        return [
            html.H3("Per lager"),
            _make_table(
                "cmp-layer",
                _compare_columns("Lager"),
                _compare_layer_rows(a_rep, b_rep),
                extra_conditional=_delta_conditional(["d_p"]),
            ),
        ]
    if level == "dimension":
        if _dimension_is_empty(a_rep.per_dimension) or _dimension_is_empty(
            b_rep.per_dimension
        ):
            return [html.H3("Per dimension"), html.P("Data saknas för denna nivå")]
        return [
            html.H3("Per dimension"),
            _make_table(
                "cmp-dimension",
                _COMPARE_DIMENSION_COLUMNS,
                _compare_dimension_rows(a_rep, b_rep),
                extra_conditional=_delta_conditional(["d_count"]),
            ),
        ]
    return []


@callback(
    Output("analysis-content", "children"),
    Input("snapshot-a", "value"),
    Input("snapshot-b", "value"),
    Input("analysis-levels", "value"),
)
def update_analysis(
    file_a: str | None, file_b: str | None, levels: list[str] | None
) -> list:
    """Render the A/B snapshot comparison for the selected levels."""
    if not file_a or not file_b:
        return [html.P("Välj snapshot A och B för att jämföra.")]

    infos = {info.filename: info for info in list_snapshots()}
    info_a, info_b = infos.get(file_a), infos.get(file_b)
    if info_a is None or info_b is None:
        return [html.P("En av de valda snapshotsen kunde inte hittas.")]

    data_a = load_snapshot_file(info_a.path)
    data_b = load_snapshot_file(info_b.path)
    if data_a is None or data_b is None:
        return [html.P("En av de valda snapshotsen kunde inte laddas.")]

    children: list = [
        _side_by_side(
            _metadata_row(data_a.metadata, prefix="A: "),
            _metadata_row(data_b.metadata, prefix="B: "),
        ),
    ]

    selected = levels or []
    for level in ("total", "category", "layer", "dimension"):
        if level in selected:
            children.extend(_comparison_level(level, data_a.report, data_b.report))

    ebb_a, ebb_b = data_a.evidence_basis_breakdown, data_b.evidence_basis_breakdown
    if ebb_a and ebb_b:
        children.append(
            _side_by_side(
                _evidence_basis_section(ebb_a, "A: Evidence basis", id_prefix="a"),
                _evidence_basis_section(ebb_b, "B: Evidence basis", id_prefix="b"),
            )
        )
    elif ebb_a:
        children.extend(
            _evidence_basis_section(ebb_a, "A: Evidence basis", id_prefix="a")
        )
        children.append(
            html.P(f"Snapshot B ({file_b}) saknar evidence_basis_breakdown")
        )
    elif ebb_b:
        children.extend(
            _evidence_basis_section(ebb_b, "B: Evidence basis", id_prefix="b")
        )
        children.append(
            html.P(f"Snapshot A ({file_a}) saknar evidence_basis_breakdown")
        )

    return children


@callback(
    Output("freetext-input", "value"),
    [Input(f"demo-text-btn-{i}", "n_clicks") for i in range(len(_DEMO_TEXTS))],
    prevent_initial_call=True,
)
def fill_demo_text(*_n_clicks) -> str:
    """Fill the freetext textarea with the clicked demo text."""
    triggered_id = ctx.triggered_id
    demo_keys = list(_DEMO_TEXTS.keys())
    for i, key in enumerate(demo_keys):
        if triggered_id == f"demo-text-btn-{i}":
            return _DEMO_TEXTS[key]
    return ""


@callback(
    Output("freetext-result", "children"),
    Output("freetext-summary", "children"),
    Input("analyze-button", "n_clicks"),
    State("freetext-input", "value"),
    prevent_initial_call=True,
)
def analyze_text(n_clicks: int, text: str | None) -> tuple:
    """Run the pipeline on free text and render highlighted results with summary."""
    if not text:
        return [], []
    try:
        classification = _get_freetext_pipeline().classify(text)
    except LLMProviderError:
        _provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
        _LOG.exception("LLM provider (%s) unavailable during freetext analysis", _provider)
        if _provider == "ollama":
            _err_text = (
                "Ollama är inte tillgänglig. Starta Ollama (`ollama serve`) och "
                "säkerställ att modellen `qwen3:14b` är pullad."
            )
        elif _provider == "anthropic":
            _err_text = (
                "Anthropic-providern är inte tillgänglig. Kontrollera att "
                "miljövariabeln `ANTHROPIC_API_KEY` är satt och giltig."
            )
        elif _provider == "gemini":
            _err_text = (
                "Gemini-providern är inte tillgänglig. Kontrollera att "
                "miljövariabeln `GEMINI_API_KEY` är satt och giltig."
            )
        else:
            _err_text = (
                f"Okänd LLM_PROVIDER: {_provider}. "
                "Förväntat: ollama, anthropic eller gemini."
            )
        error_msg = html.Div(_err_text, style={"color": "red"})
        return [error_msg], []
    except Exception:
        _LOG.exception("Pipeline failed during freetext analysis")
        error_msg = html.Div(
            "Analysen misslyckades - kontrollera serverloggen för detaljer.",
            style={"color": "red"},
        )
        return [error_msg], []
    return (
        build_highlighted_text(text, classification.findings),
        build_summary(classification),
    )
