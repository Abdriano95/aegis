"""Dash callbacks and evaluation logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dash import Input, Output, callback, dash_table, dcc, html

from evaluation.dataset.loader import load_dataset
from evaluation.report import Report, _context_snippet
from evaluation.runner import run_evaluation
from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.layers.context import ContextLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.pattern import PatternLayer

_LOG = logging.getLogger(__name__)

# Project-root-relative fallback so the demo works regardless of CWD.
_DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "data"
    / "iteration_1"
    / "test_dataset.json"
)


def build_pipeline() -> Pipeline:
    """Construct the demo's default three-layer pipeline."""
    return Pipeline(
        layers=[PatternLayer(), EntityLayer(), ContextLayer()],
        aggregator=Aggregator(),
    )


@dataclass(frozen=True)
class EvaluationResult:
    """Container for demo evaluation output."""

    dataset: list
    report: Report
    data_path: Path


def evaluate_demo(data_path: Optional[str] = None) -> Optional[EvaluationResult]:
    """Load the dataset and run evaluation, returning None on failure."""
    path = Path(data_path) if data_path else _DEFAULT_DATA_PATH
    try:
        pipeline = build_pipeline()
        dataset = load_dataset(str(path))
        report = run_evaluation(pipeline, dataset)
    except Exception:
        _LOG.exception("Failed to run demo evaluation (data_path=%s)", path)
        return None
    return EvaluationResult(dataset=dataset, report=report, data_path=path)


_EVAL_CACHE: Optional[EvaluationResult] = None


def _get_evaluation() -> Optional[EvaluationResult]:
    """Return the cached evaluation result, running it once on first access."""
    global _EVAL_CACHE
    if _EVAL_CACHE is None:
        _EVAL_CACHE = evaluate_demo()
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
        return html.Div(
            [
                html.H2("Testdata"),
                html.P(
                    f"Visar {len(rows)} testfall från {result.data_path}.",
                ),
                _make_table("testdata-table", _TESTDATA_COLUMNS, rows),
            ],
        )
    # Stub for issue #43
    return html.Div(
        [
            html.H2("Fritext-analys"),
            html.P("Denna vy implementeras i Issue #43."),
        ],
    )


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

    fp_data = _fp_rows(report)
    fn_data = _fn_rows(report)

    children: list = [
        html.H3("Totala mätvärden"),
        _make_table("total-table", _TOTAL_COLUMNS, _total_rows(report)),
        html.H3("Per kategori"),
        _make_table("category-table", _CATEGORY_COLUMNS, _category_rows(report)),
        html.H3("Per lager"),
        _make_table("layer-table", _LAYER_COLUMNS, _layer_rows(report)),
    ]

    if verbose:
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
