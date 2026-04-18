"""Dash application entry point."""

from __future__ import annotations

from dash import Dash

from demo.layout import get_layout

app = Dash(__name__)
app.config.suppress_callback_exceptions = True
app.layout = get_layout()

# Importing callbacks registers them as a side-effect.
import demo.callbacks  # noqa: E402, F401

if __name__ == "__main__":
    app.run(debug=True)
