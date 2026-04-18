"""Dash layout definition for the demo interface."""

from __future__ import annotations

from dash import dash_table, dcc, html


def freetext_tab_layout() -> html.Div:
    """Return the layout for the Fritext-analys tab (Issue #43/#44)."""
    return html.Div(
        [
            html.H2("Fritext-analys"),
            dcc.Textarea(
                id="freetext-input",
                placeholder="Skriv eller klistra in text här...",
                style={
                    "width": "100%",
                    "height": "160px",
                    "fontFamily": "monospace",
                    "fontSize": "14px",
                    "marginBottom": "12px",
                    "boxSizing": "border-box",
                },
            ),
            html.Button(
                "Analysera",
                id="analyze-button",
                n_clicks=0,
                style={
                    "padding": "8px 20px",
                    "fontSize": "14px",
                    "cursor": "pointer",
                    "marginBottom": "24px",
                },
            ),
            html.Div(
                id="freetext-result",
                style={
                    "fontFamily": "monospace",
                    "fontSize": "15px",
                    "lineHeight": "1.8",
                    "whiteSpace": "pre-wrap",
                    "marginBottom": "24px",
                },
            ),
            html.Div(id="freetext-summary"),
        ],
    )


def get_layout() -> html.Div:
    """Return the top-level Dash layout with three tabs: report, freetext, and testdata."""
    return html.Div(
        children=[
            html.H1("GDPR-classifier - Demo", style={"textAlign": "center"}),
            dcc.Tabs(
                id="main-tabs",
                value="tab-report",
                children=[
                    dcc.Tab(label="Utvärderingsrapport", value="tab-report"),
                    dcc.Tab(label="Fritext-analys", value="tab-freetext"),
                    dcc.Tab(label="Testdata", value="tab-testdata"),
                ],
            ),
            html.Div(id="tab-content", style={"padding": "24px"}),
        ],
    )
