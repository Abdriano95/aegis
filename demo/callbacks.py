"""Dash callbacks and evaluation logic."""

from __future__ import annotations

from pathlib import Path

from dash import Input, Output, callback, dash_table, dcc, html

from evaluation.dataset.loader import load_dataset
from evaluation.runner import run_evaluation
from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.layers.context import ContextLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.pattern import PatternLayer

# ---------------------------------------------------------------------------
# Run the evaluation once at module load so the UI stays responsive.
# ---------------------------------------------------------------------------

_DATA_PATH = Path("tests/data/iteration_1/test_dataset.json")

_pipeline = Pipeline(
    layers=[PatternLayer(), EntityLayer(), ContextLayer()],
    aggregator=Aggregator(),
)

_dataset = load_dataset(str(_DATA_PATH))
_report = run_evaluation(_pipeline, _dataset)


# ---------------------------------------------------------------------------
# Helper: build Dash DataTable from a list of dicts
# ---------------------------------------------------------------------------


def _make_table(table_id: str, columns: list[dict], data: list[dict]) -> dash_table.DataTable:
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
# Prepare table data from the report
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

_total_data = [
    {
        "metric": "Totalt",
        "tp": _report.total.tp,
        "fp": _report.total.fp,
        "fn": _report.total.fn,
        "precision": f"{_report.total.precision:.2%}",
        "recall": f"{_report.total.recall:.2%}",
        "f1": f"{_report.total.f1:.2%}",
    },
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

_category_data = [
    {
        "category": cat.value,
        "tp": m.tp,
        "fp": m.fp,
        "fn": m.fn,
        "precision": f"{m.precision:.2%}",
        "recall": f"{m.recall:.2%}",
        "f1": f"{m.f1:.2%}",
    }
    for cat, m in sorted(_report.per_category.items(), key=lambda x: x[0].value)
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

_layer_data = [
    {
        "layer": layer,
        "tp": m.tp,
        "fp": m.fp,
        "fn": m.fn,
        "precision": f"{m.precision:.2%}",
        "recall": "N/A",
        "f1": "N/A",
    }
    for layer, m in sorted(_report.per_layer.items())
]


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
)
def render_tab(tab: str) -> html.Div:
    """Switch between the two main tabs."""
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
    verbose = "verbose" in (verbose_values or [])

    children: list = [
        html.H3("Totala mätvärden"),
        _make_table("total-table", _TOTAL_COLUMNS, _total_data),
    ]

    if verbose:
        children.extend(
            [
                html.H3("Per kategori"),
                _make_table("category-table", _CATEGORY_COLUMNS, _category_data),
                html.H3("Per lager"),
                _make_table("layer-table", _LAYER_COLUMNS, _layer_data),
            ],
        )

    return children
