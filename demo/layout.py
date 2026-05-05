"""Dash layout definition for the demo interface."""

from __future__ import annotations

from dash import dash_table, dcc, html

_DEMO_TEXTS = {
    "Text 1 (Lager 1+2)": (
        "Hej Supporten, Jag har problem med min inloggning. Mitt personnummer "
        "är 850101-1236. Kan ni återkomma till anna.svensson@mail.se eller "
        "ringa på 070-123 45 67? Mvh Anna"
    ),
    "Text 2 (Lager 3, artikel 9)": (
        "Patienten har diagnostiserats med diabetes typ 2 och behandlas med "
        "metformin sedan 2024. Uppföljning sker på Sahlgrenska "
        "Universitetssjukhuset."
    ),
    "Text 3 (Lager 4, pusselbitseffekt)": (
        "Den nya rektorn på Hvitfeldtska gymnasiets fick utmärkelsen "
        "i fjol efter sitt arbete med ensembleundervisning."
    ),
}


def freetext_tab_layout() -> html.Div:
    """Return the layout for the Fritext-analys tab."""
    return html.Div(
        [
            html.H2("Fritext-analys"),
            html.Div("Exempeltexter:", style={"marginBottom": "6px", "fontWeight": "bold"}),
            html.Div(
                [
                    html.Button(
                        label,
                        id=f"demo-text-btn-{i}",
                        n_clicks=0,
                        style={
                            "marginRight": "8px",
                            "padding": "4px 10px",
                            "fontSize": "13px",
                            "cursor": "pointer",
                        },
                    )
                    for i, label in enumerate(_DEMO_TEXTS.keys())
                ],
                style={"marginBottom": "12px"},
            ),
            html.Label(
                "Text att analysera",
                htmlFor="freetext-input",
                style={"display": "block", "marginBottom": "6px"},
            ),
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
