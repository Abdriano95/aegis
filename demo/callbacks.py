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
from evaluation.report import MechanismStats, Report
from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.config import get_llm_provider
from gdpr_classifier.core.classification import Classification
from gdpr_classifier.core.finding import Finding
from gdpr_classifier.layers.article9 import Article9Layer
from gdpr_classifier.layers.combination import CombinationLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.llm.provider import LLMProviderError
from gdpr_classifier.layers.pattern import PatternLayer
from demo.layout import _DEMO_TEXTS, freetext_tab_layout
from demo.snapshot_loader import SnapshotData, load_snapshot

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
    provider = get_llm_provider("qwen2.5:7b-instruct")
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
    table_id: str, columns: list[dict], data: list[dict]
) -> dash_table.DataTable:
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
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9",
            },
        ],
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

_MECHANISM_COLUMNS = [
    {"name": "Mekanism", "id": "mechanism"},
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

_MECHANISM_DESCRIPTIONS = {
    "article9": "Artikel 9-fynd hittat (känsliga uppgifter)",
    "bypass": "Hög konfidens (>= 0.85), Mekanism 3 kringgicks",
    "mechanism3": "Pusselbitseffekt med tillräckligt evidens",
    "low": "Endast Artikel 4-fynd",
    "none": "Inga fynd över sensitivity-tröskeln",
}


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


def _mechanism_rows(stats: MechanismStats) -> list[dict]:
    labels = [
        ("article9", stats.high_via_article9),
        ("bypass", stats.medium_via_bypass),
        ("mechanism3", stats.medium_via_mechanism3),
        ("low", stats.low_count),
        ("none", stats.none_count),
    ]
    return [{"mechanism": key, "count": count} for key, count in labels]


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

    mechanism = classification.mechanism_used or "none"
    mech_explanation = _MECHANISM_DESCRIPTIONS.get(mechanism, mechanism)

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
                    "marginBottom": "8px",
                },
            ),
            html.Div(
                f"Mekanism: {mechanism} ({mech_explanation})",
                style={"marginBottom": "16px", "fontSize": "14px"},
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

    ds = meta.get("dataset", {})
    meta_div = html.Div(
        f"Snapshot genererad: {meta.get('generated_at', '?')[:10]}, "
        f"modell: {meta.get('model', '?')}, "
        f"dataset: {ds.get('total_texts', '?')} texter, "
        f"commit: {meta.get('git_commit', '?')[:8]}",
        style={"marginBottom": "16px", "fontSize": "13px", "color": "#555"},
    )

    children: list = [
        meta_div,
        html.H3("Totala mätvärden"),
        _make_table("total-table", _TOTAL_COLUMNS, _total_rows(report)),
        html.H3("Per kategori"),
        _make_table("category-table", _CATEGORY_COLUMNS, _category_rows(report)),
        html.H3("Per lager"),
        _make_table("layer-table", _LAYER_COLUMNS, _layer_rows(report)),
        html.H3("Per mekanism"),
        _make_table("mechanism-table", _MECHANISM_COLUMNS, _mechanism_rows(report.per_mechanism)),
    ]

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
                "säkerställ att modellen `qwen2.5:7b-instruct` är pullad."
            )
        else:
            _err_text = (
                f"LLM-providern ({_provider}) är inte tillgänglig. "
                "Kontrollera att modellen `qwen2.5:7b-instruct` är tillgänglig."
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
