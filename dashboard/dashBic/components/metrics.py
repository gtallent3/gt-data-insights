import dash_bootstrap_components as dbc
from dash import html

def generate_metric_cards(df):
    total_violations = len(df)
    total_fines = df["FINE AMOUNT"].sum()
    avg_fine = df["FINE AMOUNT"].mean()
    median_fine = df["FINE AMOUNT"].median()
    max_fine = df["FINE AMOUNT"].max()
    min_fine = df[df["FINE AMOUNT"] > 0]["FINE AMOUNT"].min()
    total_accounts = df["ACCOUNT NAME"].nunique()
    avg_violations_per_account = total_violations / total_accounts if total_accounts else 0
    avg_fines_per_account = total_fines / total_accounts if total_accounts else 0

    def card(label, value):
        return dbc.Col(dbc.Card([
            dbc.CardHeader(label),
            dbc.CardBody(html.H5(value, className="card-title"))
        ], className="mb-3"))

    return dbc.Container([
        dbc.Row([
            card("Total Violations", f"{total_violations:,}"),
            card("Total Fines Issued", f"${total_fines:,.2f}"),
            card("Avg Fine per Violation", f"${avg_fine:,.2f}")
        ]),
        dbc.Row([
            card("Median Fine per Violation", f"${median_fine:,.2f}"),
            card("Max Fine Issued", f"${max_fine:,.2f}"),
            card("Min Fine Issued", f"${min_fine:,.2f}")
        ]),
        dbc.Row([
            card("Total Accounts Fined", f"{total_accounts:,}"),
            card("Avg Violations per Account", f"{avg_violations_per_account:.2f}"),
            card("Avg Fines per Account", f"${avg_fines_per_account:,.2f}")
        ])
    ])