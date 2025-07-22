from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
from ..components.metrics import generate_metric_cards

def render_overview(df):
    return dbc.Container([
        html.H3("Overview & Key Questions"),
        html.Ul([
            html.Li("Does increasing fine severity lead to improved compliance behavior?"),
            html.Li("Which violation types are the most common?"),
            html.Li("Which accounts are the most frequent violators?")
        ]),
        html.Hr(),
        html.H4("Summary Statistics (Since 2015)"),
        dcc.RangeSlider(
            id="year-slider",
            min=2015,
            max=2025,
            value=[2015, 2025],
            marks={year: str(year) for year in range(2015, 2026)},
            step=1
        ),
        html.Div(id="summary-stats", className="mt-4")
    ])

def register_overview_callbacks(app, violations_df):
    @app.callback(
        Output("summary-stats", "children"),
        Input("year-slider", "value")
    )
    def update_summary(selected_years):
        df = violations_df[violations_df['Year'].between(selected_years[0], selected_years[1])]
        return generate_metric_cards(df)