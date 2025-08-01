import dash
from dash import dcc, html, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import dash.exceptions
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from data.loadData import load_and_prepare_data, append_new_entry

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)
sheet = client.open("DailyPnl").sheet1

def edit_table_section():
    df = load_and_prepare_data().sort_values("Date", ascending=False).head(20)
    return html.Div([
        html.H4("Edit Recent Entries"),
        dash_table.DataTable(
            id="edit-table",
            columns=[{"name": col, "id": col, "editable": True} for col in df.columns],
            data=df.to_dict("records"),
            style_table={"overflowX": "auto"},
            style_cell={"backgroundColor": "#1e1e1e", "color": "white"},
            style_header={"backgroundColor": "black", "color": "white"},
            editable=True
        ),
        html.Div(id="edit-msg", className="mt-2 text-success")
    ])

def render_trading_trends(bobData_df):
    df = bobData_df.copy()

    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date', 'Instrument', 'Pnl'])
    df_pivot = df.pivot_table(index='Date', columns='Instrument', values='Pnl', aggfunc='sum').reset_index()
    df_pivot = df_pivot.dropna(how='all', subset=df_pivot.columns[1:])
    pnl_cols = [col for col in df_pivot.columns if col != 'Date']

    for col in pnl_cols:
        df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce')

    main_fig = go.Figure()
    for col in pnl_cols:
        main_fig.add_trace(go.Scatter(
            x=df_pivot['Date'],
            y=df_pivot[col],
            mode='lines+markers',
            name=col
        ))
    main_fig.update_layout(
        title=dict(text="Daily PnL by Instrument", x=0.5),
        xaxis_title="Date",
        yaxis_title="PnL ($)",
        legend=dict(orientation='h', y=-0.3, x=0.5, xanchor='center'),
        height=700,
        margin=dict(l=40, r=40, t=80, b=100),
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white',
        shapes=[{
            'type': 'line',
            'y0': 0, 'y1': 0,
            'x0': df_pivot['Date'].min(), 'x1': df_pivot['Date'].max(),
            'line': {'color': 'yellow', 'width': 3}
        }]
    )

    rows = []
    for i in range(0, len(pnl_cols), 2):
        row_children = []
        for col in pnl_cols[i:i+2]:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_pivot['Date'],
                y=df_pivot[col],
                mode='lines+markers',
                name=col,
                line=dict(color='steelblue', width=2)
            ))
            fig.add_shape(
                type='line',
                x0=df_pivot['Date'].min(), x1=df_pivot['Date'].max(),
                y0=0, y1=0,
                line=dict(color='yellow', width=3)
            )
            fig.update_layout(
                title=f"{col} Daily PnL",
                xaxis_title="Date",
                yaxis_title="PnL ($)",
                height=400,
                margin=dict(l=20, r=20, t=60, b=40),
                plot_bgcolor='#1e1e1e',
                paper_bgcolor='#1e1e1e',
                font_color='white'
            )
            row_children.append(dbc.Col(dcc.Graph(figure=fig), width=6))
        rows.append(dbc.Row(row_children, className="mb-4"))

    return dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Button("Edit Entries", id="toggle-edit-btn", color="warning"), width="auto")
        ], className="mb-3"),
        html.Div(id="edit-section", children=edit_table_section(), style={"display": "none"}),

        html.H4("Trading Performance Overview"),

        dbc.Row([
            dbc.Col(dbc.Input(id="input-date", type="text", placeholder="YYYY-MM-DD", debounce=True), width=4),
            dbc.Col(dbc.Input(id="input-instrument", type="text", placeholder="Instrument (e.g., NQ)"), width=4),
            dbc.Col(dbc.Input(id="input-pnl", type="number", placeholder="PnL Amount ($)"), width=4),
        ], className="mb-2"),

        dbc.Button("Submit Entry", id="submit-btn", color="primary", className="mb-3"),
        html.Div(id="submit-msg", className="text-success mb-4"),

        dcc.Graph(id="main-graph", figure=main_fig),

        html.Hr(),
        html.H4("Individual Instrument Performance"),
        *rows,
        html.Hr(),
    ], className="mt-4")

# --- Callbacks ---

@callback(
    Output("edit-section", "style"),
    Input("toggle-edit-btn", "n_clicks"),
    State("edit-section", "style"),
    prevent_initial_call=True
)
def toggle_edit_section(n, current_style):
    if current_style and current_style.get("display") == "block":
        return {"display": "none"}
    else:
        return {"display": "block"}

@callback(
    Output("edit-msg", "children"),
    Input("edit-table", "data_previous"),
    State("edit-table", "data"),
    prevent_initial_call=True
)
def update_gsheet(data_previous, data):
    if data_previous is None:
        raise dash.exceptions.PreventUpdate

    changed_rows = []
    for i, row in enumerate(data):
        for col in row:
            if data_previous[i][col] != row[col]:
                row_num = i + 2  # Assumes match to sheet order
                col_letter = chr(65 + list(row.keys()).index(col))
                sheet.update_acell(f"{col_letter}{row_num}", row[col])
                changed_rows.append(i)

    if changed_rows:
        return f"✅ Edited rows: {', '.join(str(i+1) for i in changed_rows)}"
    else:
        return "No changes made."

@callback(
    Output("submit-msg", "children"),
    Output("main-graph", "figure"),
    Input("submit-btn", "n_clicks"),
    State("input-date", "value"),
    State("input-instrument", "value"),
    State("input-pnl", "value"),
    prevent_initial_call=True
)
def handle_submit(n_clicks, date, instrument, pnl):
    if not (date and instrument and pnl is not None):
        return "❌ Please fill in all fields.", no_update

    append_new_entry(date, instrument, pnl)
    df = load_and_prepare_data()

    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date', 'Instrument', 'Pnl'])
    df_pivot = df.pivot_table(index='Date', columns='Instrument', values='Pnl', aggfunc='sum').reset_index()

    fig = go.Figure()
    for col in df_pivot.columns[1:]:
        fig.add_trace(go.Scatter(x=df_pivot['Date'], y=df_pivot[col], mode='lines+markers', name=col))

    fig.update_layout(
        title="Daily PnL by Instrument",
        xaxis_title="Date",
        yaxis_title="PnL ($)",
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white',
        shapes=[{
            'type': 'line',
            'y0': 0, 'y1': 0,
            'x0': df_pivot['Date'].min(), 'x1': df_pivot['Date'].max(),
            'line': {'color': 'yellow', 'width': 3}
        }]
    )

    return "✅ Entry submitted!", fig