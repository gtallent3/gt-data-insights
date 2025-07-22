import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc

from data.loadData import load_and_prepare_data
from layout.overview import render_overview, register_overview_callbacks
from layout.trends import render_trends
from layout.violationCategories import render_violation_categories
from layout.fineViolationRelationships import render_fine_violation_tab
from layout.frequentViolators import render_frequent_violators_tab
from layout.takeaways import render_key_takeaways_tab


# Prepare data
complaints_df, violations_df = load_and_prepare_data()

# App setup
app = dash.Dash(
    __name__,
    external_stylesheets=["https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css"],
    suppress_callback_exceptions=True
)
app.title = "NYC BIC Compliance Dashboard"
server = app.server  # for deployment

# App layout
app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="NYC BIC Compliance Dashboard", color="primary", dark=True, fluid=True, className="mb-4"
    ),
    dbc.Tabs([
        dbc.Tab(label="Overview & Summary", tab_id="overview"),
        dbc.Tab(label="Long Term Trends", tab_id="trends"),
        dbc.Tab(label="Violation Categories", tab_id="violations"),
        dbc.Tab(label="Fine-Violation Relationships", tab_id="fine-violation relationships"),
        dbc.Tab(label="Frequent Violators", tab_id="frequent violators"),
        dbc.Tab(label="Key Takeaways", tab_id="takeaways"),
    ], id="tabs", active_tab="overview", className="mb-4"),
    html.Div(id="tab-content")
], fluid=True)

@app.callback(Output("tab-content", "children"), Input("tabs", "active_tab"))
def render_tab_content(tab):
    if tab == "overview":
        return render_overview(violations_df)
    elif tab == "trends":
        return render_trends(complaints_df, violations_df)
    elif tab == "violations":
        return render_violation_categories(violations_df)
    elif tab == "fine-violation relationships":
        return render_fine_violation_tab(violations_df)
    elif tab == "frequent violators":
        return render_frequent_violators_tab(violations_df)
    elif tab == "takeaways":
        return render_key_takeaways_tab()

# Register modular callbacks
register_overview_callbacks(app, violations_df)

if __name__ == "__main__":
   #app.run(debug=True)
   app.run_server(host="0.0.0.0", port=8080)