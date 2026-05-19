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
    "Text 4: HÖG": (
        "Internt HR-ärende 2026-0418, sammanställning inför uppföljningsmöte\n\n"
        "Medarbetare: Karin Lindqvist, anställd som logistiksamordnare sedan "
        "2019. Kontaktuppgifter enligt personalsystemet: "
        "karin.lindqvist@nordstromlogistik.se, mobil 070-413 88 21.\n\n"
        "Bakgrund: Karin har varit sjukskriven på heltid sedan den 3 mars efter "
        "att företagshälsovården ställt diagnosen utmattningssyndrom. Två "
        "rehabiliteringssamtal har hållits. Karin uppger att hon under perioden "
        "även genomgått utredning för en kronisk inflammatorisk tarmsjukdom och "
        "att hon medicinerar dagligen, samt att hon av hälsoskäl behöver slippa "
        "nattskift.\n\n"
        "Vid det senaste samtalet nämnde Karin att hon och hennes fru planerar "
        "att flytta närmare arbetsplatsen för att korta restiden. Hon bad också "
        "om att få gå ifrån en eftermiddag i månaden för möten i den lokala "
        "församling där hon är aktiv, och önskade ledigt för att fira en högtid "
        "med familjen i mitten av maj.\n\n"
        "Chefens bedömning och planerad åtgärd dokumenteras separat. Ärendet "
        "följs upp vid nästa möte."
    ),
    "Text 5: MEDEL": (
        "Visselblåsarrapport, inkommen 2026-05-09 via extern "
        "rapporteringskanal, anonym anmälare\n\n"
        "Anmälan rör påstådda missförhållanden i en offentlig verksamhet. "
        "Anmälaren har valt att inte uppge namn eller kontaktuppgifter.\n\n"
        "Personen som anmälan gäller namnges aldrig i underlaget, men beskrivs "
        "enligt följande: hen är regionens enda barnkardiolog, arbetar vid "
        "Region Bergslagens enhet i Degerfors och har enligt anmälaren suttit i "
        "den lokala fackklubbens styrelse de senaste fyra åren. Anmälaren uppger "
        "vidare att personen var sjukskriven under hösten och att flera kollegor "
        "kände till orsaken.\n\n"
        "Anmälaren beskriver ett upprepat agerande som anmälaren menar avviker "
        "från verksamhetens rutiner. Ingen brottsrubricering anges.\n\n"
        "Notering från mottagningsfunktionen: underlaget innehåller inga direkta "
        "identifikationsuppgifter, men kombinationen av yrkesroll, arbetsgivare "
        "och ort är ovanligt specifik."
    ),
    "Text 6: LÅG": (
        "Anonymiserad fallbeskrivning, internt utbildningsmaterial i "
        "bemötande\n\n"
        "En patient i 50-årsåldern söker vård för återkommande ledvärk och "
        "trötthet. Patienten har sedan tidigare en autoimmun diagnos och "
        "behandlas med immundämpande läkemedel. Av anteckningen framgår att "
        "patienten nyligen kommit till Sverige, att tolk anlitades och att "
        "patienten uppger att liknande besvär är vanliga i släkten.\n\n"
        "Vårdcentralen i Hjo remitterade patienten vidare till sjukhuset i "
        "Skövde för utredning. Uppföljning planeras i samband med en kommande "
        "patientutbildning på konferensen i höst.\n\n"
        "Fallet används enbart i utbildningssyfte. Inga namn, personnummer eller "
        "kontaktuppgifter förekommer, och beskrivningen är medvetet generell så "
        "att ingen enskild person kan identifieras."
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


_LEVEL_OPTIONS = [
    {"label": " Total", "value": "total"},
    {"label": " Per kategori", "value": "category"},
    {"label": " Per lager", "value": "layer"},
    {"label": " Per dimension", "value": "dimension"},
]


def analysis_tab_layout(snapshot_options: list[dict]) -> html.Div:
    """Return the layout for the Analys tab (snapshot comparison).

    ``snapshot_options`` is a list of ``{"label", "value"}`` dicts built by
    the caller from a fresh ``list_snapshots()`` scan so the dropdowns never
    go stale between tab visits.
    """
    _dd_style = {"marginBottom": "12px", "fontSize": "13px"}
    return html.Div(
        [
            html.H2("Analys"),
            html.Div(
                "Jämför två snapshots: välj A och B nedan. Δ-kolumnerna "
                "visar B − A i procentenheter (grönt = förbättring).",
                style={"marginBottom": "12px", "fontSize": "13px", "color": "#555"},
            ),
            html.Label("Snapshot A", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="snapshot-a",
                options=snapshot_options,
                placeholder="Välj snapshot A",
                style=_dd_style,
            ),
            html.Label("Snapshot B", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="snapshot-b",
                options=snapshot_options,
                placeholder="Välj snapshot B",
                style=_dd_style,
            ),
            html.Label("Nivåer", style={"fontWeight": "bold"}),
            dcc.Checklist(
                id="analysis-levels",
                options=_LEVEL_OPTIONS,
                value=["total", "category"],
                style={"marginBottom": "16px"},
            ),
            html.Div(id="analysis-content"),
        ],
    )


def get_layout() -> html.Div:
    """Return the top-level Dash layout: report, analysis, freetext, testdata."""
    return html.Div(
        children=[
            html.H1("GDPR-classifier - Demo", style={"textAlign": "center"}),
            dcc.Tabs(
                id="main-tabs",
                value="tab-report",
                children=[
                    dcc.Tab(label="Utvärderingsrapport", value="tab-report"),
                    dcc.Tab(label="Analys", value="tab-analysis"),
                    dcc.Tab(label="Fritext-analys", value="tab-freetext"),
                    dcc.Tab(label="Testdata", value="tab-testdata"),
                ],
            ),
            html.Div(id="tab-content", style={"padding": "24px"}),
        ],
    )
