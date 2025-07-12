import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html, dcc

def render_violation_categories(violations_df):
    # Top 10 ShortLabel types
    top_labels = (
        violations_df['ShortLabel'].value_counts()
        .head(10)
        .index.tolist()
    )

    filtered = violations_df[violations_df['ShortLabel'].isin(top_labels)].dropna(subset=['ShortLabel'])

    # Aggregated stats
    stats = (
        filtered.groupby('ShortLabel')['FINE AMOUNT']
        .agg(['mean', 'median', 'min', 'max'])
        .reset_index()
        .rename(columns={'mean': 'AvgFine', 'median': 'MedianFine', 'min': 'MinFine', 'max': 'MaxFine'})
    )

    counts = (
        filtered['ShortLabel']
        .value_counts()
        .rename_axis('ShortLabel')
        .reset_index(name='Count')
    )

    descriptions = (
        filtered.drop_duplicates(subset='ShortLabel')[['ShortLabel', 'DESCRIPTION OF RULE']]
    )

    top_types = (
        counts.merge(stats, on='ShortLabel')
              .merge(descriptions, on='ShortLabel')
              .sort_values(by="Count", ascending=False)
    )

    # Percent metrics
    all_violations = violations_df.shape[0]
    all_fines = violations_df['FINE AMOUNT'].sum()

    top10_data = violations_df[violations_df['ShortLabel'].isin(top_types['ShortLabel'])]
    top10_violations = top10_data.shape[0]
    top10_fines = top10_data['FINE AMOUNT'].sum()

    pct_violations = (top10_violations / all_violations) * 100
    pct_fines = (top10_fines / all_fines) * 100

    # Bar Chart
    fig_vio = px.bar(
        top_types,
        x='Count',
        y='ShortLabel',
        orientation='h',
        title="Top 10 Violation Types",
        hover_data={'AvgFine': ':.2f'},
        labels={'Count': 'Violation Count', 'AvgFine': 'Avg Fine ($)'},
        color_discrete_sequence=['steelblue']
    )
    fig_vio.update_layout(
        yaxis_title="Violation Type",
        xaxis_title="Number of Violations",
        height=500,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )

    # Box Plot for Fine Distribution
    summary_stats = (
        filtered.groupby('ShortLabel')['FINE AMOUNT']
        .agg(Min='min', Median='median', Max='max')
        .reset_index()
    )

    fig_box = go.Figure()
    for _, row in summary_stats.iterrows():
        fines = filtered[filtered['ShortLabel'] == row['ShortLabel']]['FINE AMOUNT']
        fines = fines[fines > 0]
        fig_box.add_trace(go.Box(
            y=fines,
            name=row['ShortLabel'],
            boxpoints=False,
            marker_color='indianred',
            customdata=[[row['Min'], row['Median'], row['Max']]] * len(fines),
            hovertemplate=(
                "Min: $%{customdata[0]:,.0f}<br>"
                "Median: $%{customdata[1]:,.0f}<br>"
                "Max: $%{customdata[2]:,.0f}<extra></extra>"
            )
        ))
    fig_box.update_layout(
        title="Fine Distribution by Violation Type",
        yaxis_title="Fine ($)",
        xaxis_title="Violation Type",
        xaxis_tickangle=-30,
        showlegend=False,
        height=550,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )

    # Render full layout
    return dbc.Container([
        html.H4("Top 10 Violation Types Summary", className="mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Violations from Top 10"),
                    dbc.CardBody(html.H5(f"{top10_violations:,}"))
                ])
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Percent of All Violations"),
                    dbc.CardBody(html.H5(f"{pct_violations:.2f}%"))
                ])
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Fines from Top 10"),
                    dbc.CardBody(html.H5(f"${top10_fines:,.2f}"))
                ])
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Percent of All Fines"),
                    dbc.CardBody(html.H5(f"{pct_fines:.2f}%"))
                ])
            ])
        ], className="mb-4"),
        dcc.Graph(figure=fig_vio),
        dcc.Graph(figure=fig_box)
    ])