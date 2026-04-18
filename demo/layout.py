"""Dash layout definition for the demo interface."""

from __future__ import annotations

from dash import dash_table, dcc, html


def get_layout() -> html.Div:
    """Return the top-level Dash layout with two tabs."""
    return html.Div(
        children=[
            html.H1("GDPR-classifier – Demo", style={"textAlign": "center"}),
            dcc.Tabs(
                id="main-tabs",
                value="tab-report",
                children=[
                    dcc.Tab(label="Utvärderingsrapport", value="tab-report"),
                    dcc.Tab(label="Fritext-analys", value="tab-freetext"),
                ],
            ),
            html.Div(id="tab-content", style={"padding": "24px"}),
        ],
    )
