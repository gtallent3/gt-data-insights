from dash import html
import dash_bootstrap_components as dbc

def render_key_takeaways_tab():
    return dbc.Container([
        html.H3("Key Findings", className="mb-4"),
        html.Ul([
            html.Li([
                html.Strong("Increased Enforcement Appears Effective: "),
                "Violations tend to decline after years of expanded enforcement and higher fines — suggesting higher compliance."
            ], className="mb-2"),
            html.Li([
                html.Strong("A Few Violation Types and Accounts Drive Most Activity: "),
                "A small number of violation types and repeat violators account for a large share of total fines and violations."
            ], className="mb-2"),
            html.Li([
                html.Strong("Targeted Enforcement and Education Can Improve Compliance: "),
                "Combining penalties with proactive outreach or education may help reduce repeat offenses and improve long-term outcomes."
            ])
        ])
    ], fluid=True)