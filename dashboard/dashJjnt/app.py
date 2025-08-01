import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from data.loadData import load_and_prepare_data, append_new_entry
from layout.bobData import render_trading_trends

# --- Dash App Setup ---
app = dash.Dash(
    __name__,
    external_stylesheets=["https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css"],
    suppress_callback_exceptions=True
)
app.title = "JJNT Data Dashboard"
server = app.server

# --- App Layout ---
app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="JJNT Data Dashboard", color="primary", dark=True, fluid=True, className="mb-4"
    ),
    dbc.Tabs([
        dbc.Tab(label="Overview & Summary", tab_id="overview"),
        dbc.Tab(label="Bob Trading", tab_id="BB"),
        dbc.Tab(label="Computer 1", tab_id="c1"),
        dbc.Tab(label="Computer 2", tab_id="c2"),
        dbc.Tab(label="Computer 3", tab_id="c3"),
    ], id="tabs", active_tab="overview", className="mb-4"),
    html.Div(id="tab-content"),
], fluid=True)

# --- Unified Callback for Tabs ---
@app.callback(Output("tab-content", "children"), Input("tabs", "active_tab"))
def render_tab_content(tab):
    if tab == "BB":
        df = load_and_prepare_data()
        return render_trading_trends(df)
    elif tab == "c1":
        return html.Div("Computer 1 content coming soon.")
    elif tab == "c2":
        return html.Div("Computer 2 content coming soon.")
    elif tab == "c3":
        return html.Div("Computer 3 content coming soon.")
    else:
        return html.Div("Welcome to the JJNT Data Dashboard.")

# --- Google Sheets Setup (only for dev print logging) ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)

print("✅ Connected to Google successfully.")
print("📄 Sheets accessible by service account:")
for s in client.openall():
    print("   -", s.title)

# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)