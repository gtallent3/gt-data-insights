import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback

def render_frequent_violators_tab(violations_df):
    return dbc.Container([
        html.H4("Frequent Violators", className="mb-4"),

        dbc.Row([
            dbc.Col([
                html.Label("Show Top 10 Accounts by:"),
                dcc.RadioItems(
                    id="rank-toggle",
                    options=[
                        {"label": "Total Fines", "value": "TotalFines"},
                        {"label": "Violation Count", "value": "ViolationCount"},
                    ],
                    value="TotalFines",
                    inline=True,
                    labelStyle={'margin-right': '20px'}
                )
            ])
        ], className="mb-3"),

        # Just an empty toggle placeholder to satisfy Dash's callback registry
        html.Div(dcc.RadioItems(id="fine-metric-toggle", value="TotalFines"), style={"display": "none"}),

        html.Div(id="frequent-violators-content")
    ], fluid=True)

@callback(
    Output("frequent-violators-content", "children"),
    Input("rank-toggle", "value"),
    Input("fine-metric-toggle", "value"),
    prevent_initial_call=False
)
def update_frequent_violators(rank_by, fine_metric):
    # Load and clean data
    violations_df = pd.read_csv("https://drive.google.com/uc?export=download&id=1SOaADySZRl_mHg--NA4M0ZiORSecljwI")
    violations_df = violations_df.dropna(subset=['ACCOUNT NAME', 'FINE AMOUNT'])
    violations_df['DATE VIOLATION ISSUED'] = pd.to_datetime(violations_df['DATE VIOLATION ISSUED'], errors='coerce')
    violations_df['Year'] = violations_df['DATE VIOLATION ISSUED'].dt.year
    violations_df = violations_df[violations_df['Year'] >= 2015]

    # Rankings
    account_summary = (
        violations_df
        .groupby('ACCOUNT NAME')
        .agg(TotalFines=('FINE AMOUNT', 'sum'), ViolationCount=('FINE AMOUNT', 'count'))
        .reset_index()
    )
    top_accounts = account_summary.sort_values(by=rank_by, ascending=False).head(10)['ACCOUNT NAME']
    top10_data = violations_df[violations_df['ACCOUNT NAME'].isin(top_accounts)]
    top10_summary = (
        top10_data
        .groupby('ACCOUNT NAME')
        .agg(TotalFines=('FINE AMOUNT', 'sum'), ViolationCount=('FINE AMOUNT', 'count'))
        .reset_index()
        .sort_values(by=rank_by, ascending=False)
    )

    # Totals and %s
    total_violations = violations_df.shape[0]
    total_fines = violations_df['FINE AMOUNT'].sum()
    top10_violations = top10_data.shape[0]
    top10_fines = top10_data['FINE AMOUNT'].sum()
    pct_violations = (top10_violations / total_violations) * 100
    pct_fines = (top10_fines / total_fines) * 100

    summary = dbc.Row([
        dbc.Col([
            html.H6("Violations by Top 10"),
            html.H5(f"{top10_violations:,}"),
            html.P(f"{pct_violations:.2f}% of all violations", className="text-muted")
        ]),
        dbc.Col([
            html.H6("Fines from Top 10"),
            html.H5(f"${top10_fines:,.2f}"),
            html.P(f"{pct_fines:.2f}% of all fines", className="text-muted")
        ])
    ], className="mb-4")

    # Main bar chart
    fig_main = go.Figure()
    fig_main.add_trace(go.Bar(
        x=top10_summary['ACCOUNT NAME'],
        y=top10_summary[rank_by],
        name=rank_by,
        marker_color='indianred' if rank_by == 'TotalFines' else 'steelblue',
        yaxis='y1',
        offsetgroup=0
    ))

    secondary_metric = 'ViolationCount' if rank_by == 'TotalFines' else 'TotalFines'
    fig_main.add_trace(go.Bar(
        x=top10_summary['ACCOUNT NAME'],
        y=top10_summary[secondary_metric],
        name=secondary_metric,
        marker_color='steelblue' if rank_by == 'TotalFines' else 'indianred',
        yaxis='y2',
        offsetgroup=1
    ))

    fig_main.update_layout(
        title=f"Top 10 Accounts by {'Total Fines' if rank_by == 'TotalFines' else 'Violation Count'}",
        xaxis=dict(title='Account Name', tickangle=-45),
        yaxis=dict(title=rank_by, side='left', showgrid=True),
        yaxis2=dict(title=secondary_metric, overlaying='y', side='right', showgrid=False),
        barmode='group',
        height=600,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white',
        legend=dict(x=0.5, y=1.15, orientation='h', xanchor='center')
    )

    # Fine metric toggle to control the 10 time series charts (placed BELOW main chart)
    fine_toggle = dbc.Row([
        dbc.Col([
            html.Label("Choose Fine Metric for Time Series:"),
            dcc.RadioItems(
                id="fine-metric-toggle",
                options=[
                    {"label": "Total Fines", "value": "TotalFines"},
                    {"label": "Average Fines", "value": "AverageFines"},
                ],
                value=fine_metric,
                inline=True,
                labelStyle={'margin-right': '20px'}
            )
        ])
    ], className="my-4")

    # Time Series
    plot_df = (
        top10_data
        .groupby(['ACCOUNT NAME', 'Year'])
        .agg(
            TotalFines=('FINE AMOUNT', 'sum'),
            ViolationCount=('FINE AMOUNT', 'count'),
            AverageFines=('FINE AMOUNT', 'mean')
        )
        .reset_index()
    )

    time_series_charts = []
    for account in top_accounts:
        subset = plot_df[plot_df['ACCOUNT NAME'] == account]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=subset['Year'],
            y=subset['ViolationCount'],
            name='Violation Count',
            marker_color='steelblue',
            yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=subset['Year'],
            y=subset[fine_metric],
            name=fine_metric,
            mode='lines+markers',
            line=dict(color='indianred'),
            yaxis='y2'
        ))
        fig.update_layout(
            title=account,
            xaxis=dict(title='Year', dtick=1),
            yaxis=dict(title='Violation Count', side='left'),
            yaxis2=dict(
                title='Total Fines ($)' if fine_metric == 'TotalFines' else 'Average Fine ($)',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            height=300,
            margin=dict(t=40, b=30, l=30, r=30),
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font_color='white',
            showlegend=False
        )
        time_series_charts.append(dbc.Col(dcc.Graph(figure=fig), md=6))

    return html.Div([
        summary,
        dcc.Graph(figure=fig_main),
        fine_toggle,
        html.Hr(),
        html.H5("Violations and Fines Over Time"),
        dbc.Row(time_series_charts[:2]),
        dbc.Row(time_series_charts[2:4]),
        dbc.Row(time_series_charts[4:6]),
        dbc.Row(time_series_charts[6:8]),
        dbc.Row(time_series_charts[8:10]),
    ])