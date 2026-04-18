"""Dash callbacks and evaluation logic."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from collections import defaultdict

from dash import Input, Output, State, callback, dash_table, dcc, html

from evaluation.dataset.loader import load_dataset
from evaluation.report import Report
from evaluation.runner import run_evaluation
from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.core.classification import Classification
from gdpr_classifier.core.finding import Finding
from gdpr_classifier.layers.context import ContextLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.pattern import PatternLayer
from demo.layout import freetext_tab_layout

_LOG = logging.getLogger(__name__)

# Project-root-relative fallback so the demo works regardless of CWD.
_DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "data"
    / "iteration_1"
    / "test_dataset.json"
)


def _context_snippet(text: str, start: int, end: int, window: int = 20) -> str:
    """Return a short snippet of ``text`` around ``[start, end)`` with ellipses."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    prefix = "..." if ctx_start > 0 else ""
    suffix = "..." if ctx_end < len(text) else ""
    return f"{prefix}{text[ctx_start:ctx_end]}{suffix}"


def build_pipeline() -> Pipeline:
    """Construct the demo's default three-layer pipeline."""
    return Pipeline(
        layers=[PatternLayer(), EntityLayer(), ContextLayer()],
        aggregator=Aggregator(),
    )


_FREETEXT_PIPELINE: Pipeline | None = None


def _get_freetext_pipeline() -> Pipeline:
    global _FREETEXT_PIPELINE
    if _FREETEXT_PIPELINE is None:
        _FREETEXT_PIPELINE = build_pipeline()
    return _FREETEXT_PIPELINE


@dataclass(frozen=True)
class EvaluationResult:
    """Container for demo evaluation output."""

    dataset: list
    report: Report
    data_path: Path


def evaluate_demo(data_path: Optional[str] = None) -> Optional[EvaluationResult]:
    """Load the dataset and run evaluation, returning None on dataset-load failure."""
    path = Path(data_path) if data_path else _DEFAULT_DATA_PATH
    try:
        dataset = load_dataset(str(path))
    except (OSError, json.JSONDecodeError, ValueError):
        _LOG.exception("Failed to load dataset (data_path=%s)", path)
        return None
    pipeline = build_pipeline()
    report = run_evaluation(pipeline, dataset)
    return EvaluationResult(dataset=dataset, report=report, data_path=path)


_EVAL_CACHE: Optional[EvaluationResult] = None
_EVAL_INITIALIZED: bool = False
_EVAL_LOCK = threading.Lock()


def _get_evaluation() -> Optional[EvaluationResult]:
    """Return the cached evaluation result, running it exactly once (thread-safe)."""
    global _EVAL_CACHE, _EVAL_INITIALIZED
    if not _EVAL_INITIALIZED:
        with _EVAL_LOCK:
            if not _EVAL_INITIALIZED:
                _EVAL_CACHE = evaluate_demo()
                _EVAL_INITIALIZED = True
    return _EVAL_CACHE


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


def _evaluation_unavailable() -> html.Div:
    return html.Div(
        [
            html.H2("Utvärdering misslyckades"),
            html.P(
                "Kunde inte köra utvärderingen. Kontrollera serverloggen för "
                "detaljer och att testdatafilen finns.",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Freetext helpers (Issue #43 / #44)
# ---------------------------------------------------------------------------

_SOURCE_COLORS: dict[str, str] = {
    "pattern": "orange",
    "entity": "#add8e6",
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


def build_highlighted_text(text: str, findings: list[Finding]) -> list:
    """Build a list of html.Span components with colour-coded, annotated findings."""
    winners = _resolve_overlaps(findings)
    winners.sort(key=lambda f: f.start)
    spans: list = []
    cursor = 0
    for f in winners:
        if cursor < f.start:
            spans.append(html.Span(text[cursor : f.start]))
        layer = f.source.split(".")[0]
        bg = _SOURCE_COLORS.get(layer, "#e0e0e0")
        tooltip = (
            f"Kategori: {f.category.value}, "
            f"Källa: {f.source}, "
            f"Konfidens: {f.confidence:.0%}"
        )
        spans.append(
            html.Span(
                text[f.start : f.end],
                title=tooltip,
                style={
                    "backgroundColor": bg,
                    "borderRadius": "3px",
                    "padding": "1px 2px",
                    "cursor": "help",
                },
            )
        )
        cursor = f.end
    if cursor < len(text):
        spans.append(html.Span(text[cursor:]))
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

    per_category: dict[str, int] = defaultdict(int)
    per_layer: dict[str, int] = defaultdict(int)
    for f in classification.findings:
        per_category[f.category.value] += 1
        per_layer[f.source.split(".")[0]] += 1

    category_rows = [
        html.Tr([html.Td(cat), html.Td(str(count))])
        for cat, count in sorted(per_category.items())
    ]
    layer_rows = [
        html.Tr([html.Td(layer), html.Td(str(count))])
        for layer, count in sorted(per_layer.items())
    ]
    table_style = {"borderCollapse": "collapse", "marginTop": "8px", "width": "auto"}
    cell_style = {"border": "1px solid #ccc", "padding": "4px 12px"}

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
                                    html.Tbody(
                                        [
                                            html.Tr(
                                                [
                                                    html.Td(cat, style=cell_style),
                                                    html.Td(str(cnt), style=cell_style),
                                                ]
                                            )
                                            for cat, cnt in sorted(per_category.items())
                                        ]
                                    ),
                                ],
                                style=table_style,
                            )
                            if category_rows
                            else html.P("Inga fynd."),
                        ],
                        style={"marginRight": "40px", "display": "inline-block", "verticalAlign": "top"},
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
                                    html.Tbody(
                                        [
                                            html.Tr(
                                                [
                                                    html.Td(layer, style=cell_style),
                                                    html.Td(str(cnt), style=cell_style),
                                                ]
                                            )
                                            for layer, cnt in sorted(per_layer.items())
                                        ]
                                    ),
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
    """Switch between report, testdata and freetext stub views."""
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
        result = _get_evaluation()
        if result is None:
            return _evaluation_unavailable()
        rows = _testdata_rows(result.dataset)
        display_name = result.data_path.name
        return html.Div(
            [
                html.H2("Testdata"),
                html.P(
                    f"Visar {len(rows)} testfall från {display_name}.",
                ),
                _make_table("testdata-table", _TESTDATA_COLUMNS, rows),
            ],
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
    result = _get_evaluation()
    if result is None:
        return [_evaluation_unavailable()]

    report = result.report
    verbose = "verbose" in (verbose_values or [])

    children: list = [
        html.H3("Totala mätvärden"),
        _make_table("total-table", _TOTAL_COLUMNS, _total_rows(report)),
        html.H3("Per kategori"),
        _make_table("category-table", _CATEGORY_COLUMNS, _category_rows(report)),
        html.H3("Per lager"),
        _make_table("layer-table", _LAYER_COLUMNS, _layer_rows(report)),
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
    except Exception:
        _LOG.exception("Pipeline failed during freetext analysis")
        error_msg = html.Div(
            "Analysen misslyckades – kontrollera serverloggen för detaljer.",
            style={"color": "red"},
        )
        return [], error_msg
    return (
        build_highlighted_text(text, classification.findings),
        build_summary(classification),
    )
