import dash
import numpy as np
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from data.loadData import load_and_prepare_data

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)
sheet = client.open("DailyPnl").sheet1

def render_trading_trends(bobData_df):
    df = bobData_df.copy()
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date', 'Instrument', 'Pnl'])
    min_date = df['Date'].min()
    max_date = df['Date'].max()

    return dbc.Container([
        html.H4("Trading Performance Overview"),

        # --- Toggle for Add/Edit ---
        dbc.Row([
            dbc.Col([
                html.Label("Select Mode", style={"color": "white"}),
                dcc.Dropdown(
                    id="entry-mode-dropdown",
                    options=[
                        {"label": "Add Entry", "value": "add"},
                        {"label": "Edit Entry", "value": "edit"}
                    ],
                    value="add",
                    clearable=False,
                    style={"color": "black"}
                )
            ], width=4)
        ], className="mb-3"),

        # --- Add Entry Section ---
        html.Div(id="add-entry-section", children=[
            dbc.Row([
                dbc.Col(dbc.Input(id="input-date", type="date", placeholder="YYYY-MM-DD", debounce=True), width=4),
                dbc.Col(dbc.Input(id="input-instrument", type="text", placeholder="Instrument (e.g., NQ)"), width=4),
                dbc.Col(dbc.Input(id="input-pnl", type="number", placeholder="PnL Amount ($)"), width=4),
                dbc.Col(dbc.Input(id="input-goal", type="number", placeholder="Daily Goal ($)"), width=4),
            ], className="mb-2"),
            dbc.Button("Submit Entry", id="submit-btn", color="primary", className="mb-3"),
            html.Div(id="submit-msg", className="text-success mb-4"),
        ], style={"display": "block"}),

        # --- Edit Entry Section ---
        html.Div(id="edit-entry-section", children=[
            html.H4("Edit Existing Entry", className="mt-3"),
            dbc.Row([
                dbc.Col(dbc.Input(id="edit-date", type="date", placeholder="Date (YYYY-MM-DD)"), width=4),
                dbc.Col(dbc.Input(id="edit-instrument", type="text", placeholder="Instrument (e.g., NQ)"), width=4),
                dbc.Col(dbc.Button("Load Entry", id="load-entry-btn", color="info"), width=4),
            ], className="mb-3"),

            html.Div(id="edit-entry-form", children=[
                dbc.Row([
                    dbc.Col(dbc.Input(id="edit-date-new", type="date", placeholder="New Date (YYYY-MM-DD)"), width=4),
                    dbc.Col(dbc.Input(id="edit-instrument-new", type="text", placeholder="New Instrument (e.g., NQ)"), width=4),
                    dbc.Col(dbc.Input(id="edit-pnl-new", type="number", placeholder="New PnL Amount ($)"), width=4),
                    dbc.Col(dbc.Input(id="edit-goal-new", type="number", placeholder="New Daily Goal ($)"), width=4),
                ], className="mb-2"),

                dbc.Row([
                    dbc.Col(dbc.Button("Update Entry", id="update-entry-btn", color="success", className="w-100"), width=6),
                    dbc.Col(dbc.Button("Delete Entry", id="delete-entry-btn", color="danger", className="w-100"), width=6),
                ], className="mb-2"),

                html.Div(id="edit-entry-msg", className="text-success")
            ], style={"display": "none"})
        ], style={"display": "none"}),

        html.Hr(),

        html.H4("Date Range Filter"),
        dcc.DatePickerRange(
            id="date-range-picker",
            min_date_allowed=min_date,
            max_date_allowed=max_date,
            start_date=min_date,
            end_date=max_date,
            display_format='MM/DD/YYYY',
            className="mb-4"
        ),

        html.Hr(),
        html.H4("Percentage of Positive Trades by Instrument"),
        html.Div(id="positive-trade-stats"),

        html.Hr(),
        dcc.Graph(id="main-graph"),

        html.Hr(),
        html.H4("Individual Instrument Performance"),
        html.Div(id="individual-charts"),

        html.Hr(),
        html.H4("Daily Goal Hit Tracker"),
        html.Div(id="goal-hit-summary"),

        html.Hr(),
    ], className="mt-4")


# === Callbacks ===

@callback(
    Output("main-graph", "figure"),
    Output("individual-charts", "children"),
    Output("positive-trade-stats", "children"),
    Output("goal-hit-summary", "children"),
    Input("date-range-picker", "start_date"),
    Input("date-range-picker", "end_date")
)
def update_graphs(start_date, end_date):
    df = load_and_prepare_data()
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date', 'Instrument', 'Pnl'])

    if "Daily Goal" in df.columns:
        df['Daily Goal'] = pd.to_numeric(df['Daily Goal'], errors='coerce')
    else:
        df['Daily Goal'] = None

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    df_pivot = df.pivot_table(index='Date', columns='Instrument', values='Pnl', aggfunc='sum').reset_index()
    pnl_cols = [col for col in df_pivot.columns if col != 'Date']
    for col in pnl_cols:
        df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce')
    df_pivot["Total PnL"] = df_pivot[pnl_cols].sum(axis=1)

    # Main Graph
    main_fig = go.Figure()
    for col in pnl_cols:
        main_fig.add_trace(go.Scatter(x=df_pivot['Date'], y=df_pivot[col], mode='lines+markers', name=col))
    main_fig.add_trace(go.Scatter(x=df_pivot['Date'], y=df_pivot["Total PnL"],
                                  mode='lines+markers', name="Total PnL",
                                  line=dict(color='white', width=3, dash='dot')))
    main_fig.update_layout(
        title=dict(text="Daily PnL by Instrument", x=0.5),
        xaxis_title="Date", yaxis_title="PnL ($)",
        plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white',
        height=700,
        legend=dict(orientation='h', y=-0.3, x=0.5, xanchor='center'),
        shapes=[{'type': 'line', 'y0': 0, 'y1': 0,
                 'x0': df_pivot['Date'].min(), 'x1': df_pivot['Date'].max(),
                 'line': {'color': 'yellow', 'width': 3}}]
    )

    # Individual Charts
    rows = []
    for i in range(0, len(pnl_cols), 2):
        row_children = []
        for col in pnl_cols[i:i+2]:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_pivot['Date'], y=df_pivot[col], mode='lines+markers', name=col))
            fig.add_shape(type='line', x0=df_pivot['Date'].min(), x1=df_pivot['Date'].max(), y0=0, y1=0,
                          line=dict(color='yellow', width=3))
            fig.update_layout(
                title=f"{col} Daily PnL", xaxis_title="Date", yaxis_title="PnL ($)",
                height=400, plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font_color='white'
            )
            row_children.append(dbc.Col(dcc.Graph(figure=fig), width=6))
        rows.append(dbc.Row(row_children, className="mb-4"))

    # Positive Trade Stats
    positive_pct = {}
    for col in pnl_cols:
        total_days = df_pivot[col].count()
        positive_days = (df_pivot[col] > 0).sum()
        pct = round(100 * positive_days / total_days, 1) if total_days > 0 else 0
        positive_pct[col] = pct
    positive_stats = dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.H6(instr, className="card-title text-center"),
                html.H4(f"{pct}%", className=f"text-center {'text-success' if pct >= 50 else 'text-warning'}"),
                html.P("Positive Days", className="text-center mb-0", style={"fontSize": "14px"})
            ]), color="dark", inverse=True), width=3
        )
        for instr, pct in sorted(positive_pct.items(), key=lambda x: x[1], reverse=True)
    ])

    # Daily Goal Hits (using np.isclose)
    goal_summary = []
    if "Daily Goal" in df.columns and df['Daily Goal'].notna().any():
        goal_df = df[df['Daily Goal'].notna()]
        grouped = goal_df.groupby(['Date', 'Instrument'])
        hit_results = []

        for (date, instr), group in grouped:
            total_pnl = group['Pnl'].sum()
            goal = group['Daily Goal'].iloc[0]
            hit = "Yes" if np.isclose(total_pnl, goal, atol=0.01) or total_pnl > goal else "No"
            hit_results.append((date.strftime('%m/%d/%Y'), instr, goal, total_pnl, hit))

        hit_df = pd.DataFrame(hit_results, columns=['Date', 'Instrument', 'Goal', 'PnL', 'Hit'])

        goal_summary = dbc.Table.from_dataframe(
            hit_df[['Date', 'Instrument', 'Goal', 'PnL', 'Hit']],
            striped=True, bordered=True, hover=True,
            style={"color": "white"}
        )

    return main_fig, rows, positive_stats, goal_summary

# Toggle Add vs Edit sections
@callback(
    Output("add-entry-section", "style"),
    Output("edit-entry-section", "style"),
    Input("entry-mode-dropdown", "value")
)
def toggle_entry_mode(mode):
    return (
        {"display": "block"} if mode == "add" else {"display": "none"},
        {"display": "block"} if mode == "edit" else {"display": "none"}
    )

# Submit Entry
@callback(
    Output("submit-msg", "children"),
    Input("submit-btn", "n_clicks"),
    State("input-date", "value"),
    State("input-instrument", "value"),
    State("input-pnl", "value"),
    State("input-goal", "value"),  # <- NEW
    prevent_initial_call=True
)
def submit_entry(n_clicks, date, instrument, pnl, goal):
    if not (date and instrument and pnl is not None):
        return "All fields are required."
    try:
        new_row = [
            pd.to_datetime(date).strftime("%m/%d/%Y"),
            instrument.upper(),
            float(pnl),
            float(goal) if goal is not None else ""  # <- append goal
        ]
        sheet.append_row(new_row)
        return f"✅ Entry added: {new_row}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
    
@callback(
    Output("edit-entry-form", "style"),
    Output("edit-date-new", "value"),
    Output("edit-instrument-new", "value"),
    Output("edit-pnl-new", "value"),
    Output("edit-goal-new", "value"),  # <- NEW
    Output("edit-entry-msg", "children"),
    Input("load-entry-btn", "n_clicks"),
    State("edit-date", "value"),
    State("edit-instrument", "value"),
    prevent_initial_call=True
)
def load_existing_entry(n_clicks, date, instrument):
    if not (date and instrument):
        return {"display": "none"}, None, None, None, None, "❌ Please enter both date and instrument."

    df = sheet.get_all_records()
    target_date = pd.to_datetime(date).strftime("%m/%d/%Y")
    instrument = instrument.upper()

    for i, row in enumerate(df):
        if row["Date"] == target_date and row["Instrument"].upper() == instrument:
            return (
                {"display": "block"},
                pd.to_datetime(row["Date"]).strftime("%Y-%m-%d"),
                row["Instrument"],
                float(row["Pnl"]),
                float(row["Daily Goal"]) if "Daily Goal" in row and str(row["Daily Goal"]).strip() != '' else None,
                f"✅ Entry loaded for {row['Date']} {row['Instrument']}"
            )

    return (
    {"display": "block"},
    pd.to_datetime(row["Date"]).strftime("%Y-%m-%d"),
    row["Instrument"],
    float(row["Pnl"]),
    float(row["Daily Goal"]) if "Daily Goal" in row and str(row["Daily Goal"]).strip() != '' else None,
    f"✅ Entry loaded for {row['Date']} {row['Instrument']}"
)
    
@callback(
    Output("edit-entry-msg", "children", allow_duplicate=True),
    Input("update-entry-btn", "n_clicks"),
    State("edit-date", "value"),
    State("edit-instrument", "value"),
    State("edit-date-new", "value"),
    State("edit-instrument-new", "value"),
    State("edit-pnl-new", "value"),
    State("edit-goal-new", "value"),  # <- NEW
    prevent_initial_call=True
)
def update_entry(n_clicks, old_date, old_instr, new_date, new_instr, new_pnl, new_goal):
    try:
        if not (old_date and old_instr and new_date and new_instr):
            return "❌ Missing values."

        old_date_fmt = pd.to_datetime(old_date).strftime("%m/%d/%Y")
        new_date_fmt = pd.to_datetime(new_date).strftime("%m/%d/%Y")

        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if row["Date"] == old_date_fmt and row["Instrument"].upper() == old_instr.upper():
                sheet.update_cell(i+2, 1, new_date_fmt)  # Date
                sheet.update_cell(i+2, 2, new_instr.upper())  # Instrument
                sheet.update_cell(i+2, 3, float(new_pnl))  # PnL
                if "Daily Goal" in sheet.row_values(1):  # Only update goal if the column exists
                    sheet.update_cell(i+2, 4, float(new_goal) if new_goal is not None else "")
                return f"✅ Updated entry to {new_date_fmt} {new_instr.upper()} ${new_pnl}"
        return "❌ Entry to update not found."
    except Exception as e:
        return f"❌ Error: {str(e)}"
    
@callback(
    Output("edit-entry-msg", "children", allow_duplicate=True),
    Input("delete-entry-btn", "n_clicks"),
    State("edit-date", "value"),
    State("edit-instrument", "value"),
    prevent_initial_call=True
)
def delete_entry(n_clicks, date, instrument):
    try:
        if not (date and instrument):
            return "❌ Date and Instrument required."

        date_fmt = pd.to_datetime(date).strftime("%m/%d/%Y")
        instrument = instrument.upper()

        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if row["Date"] == date_fmt and row["Instrument"].upper() == instrument:
                sheet.delete_rows(i+2)
                return f"🗑️ Deleted entry for {date_fmt} {instrument}"

        return "❌ Entry not found."

    except Exception as e:
        return f"❌ Error: {str(e)}"