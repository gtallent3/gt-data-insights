import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc

from .data.loadData import load_and_prepare_data
from .layout.bobData import render_trading_trends


# Prepare data
bobData_df = load_and_prepare_data()

# --- Dash App Setup ---
app = dash.Dash(
    __name__,
    #requests_pathname_prefix='/dashboard/',  # 👈 This allows subpath routing!
    external_stylesheets=["https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css"],
    suppress_callback_exceptions=True
)
app.title = "JJNT Data Dashboard"
server = app.server  # 👈 Render uses this for deployment

# App layout
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
    html.Div(id="tab-content")
], fluid=True)

@app.callback(Output("tab-content", "children"), Input("tabs", "active_tab"))
def render_tab_content(tab):
    #if tab == "overview":
     #   return render_overview(violations_df)
    #elif tab == "trends":
     #   return render_trends(complaints_df, violations_df)
    if tab == "BB":
        return render_trading_trends(bobData_df)
    elif tab == "c1":
        return None
    elif tab == "c2":
        return None
    elif tab == "c3":
        return None

# Register modular callbacks
#register_overview_callbacks(app, violations_df)

if __name__ == "__main__":
   app.run(debug=True)
   #app.run_server(host="0.0.0.0", port=8080)