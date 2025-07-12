import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import html, dcc

def render_fine_violation_tab(violations_df):
    violations_df['Year'] = pd.to_datetime(violations_df['DATE VIOLATION ISSUED'], errors='coerce').dt.year
    violations_df = violations_df[violations_df['Year'] >= 2015]

    top10_labels = violations_df['ShortLabel'].value_counts().head(10).index

    # --- Correlation Chart: Avg Fine vs Count ---
    corr_df = (
        violations_df[violations_df['ShortLabel'].isin(top10_labels)]
        .dropna(subset=['FINE AMOUNT', 'Year'])
        .groupby(['ShortLabel', 'Year'])
        .agg(
            TotalFines=('FINE AMOUNT', 'sum'),
            ViolationCount=('FINE AMOUNT', 'count'),
            AvgFine=('FINE AMOUNT', 'mean')
        )
        .reset_index()
    )

    corr_result = (
        corr_df
        .groupby('ShortLabel')[['AvgFine', 'ViolationCount']]
        .corr()
        .iloc[0::2, -1]
        .reset_index()
        .rename(columns={'ShortLabel': 'ShortLabel', 'ViolationCount': 'Correlation'})
        .drop(columns=['level_1'])
    )

    fig_corr = px.bar(
        corr_result.sort_values(by='Correlation'),
        x='Correlation',
        y='ShortLabel',
        orientation='h',
        color='Correlation',
        color_continuous_scale='RdBu',
        title="Top 10 Violation Types: Correlation Between Avg Fine & Count"
    )
    fig_corr.update_layout(
        yaxis_title="Violation Type",
        xaxis_title="Correlation",
        height=500,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )

    # --- Time Series Comparison Plots ---
    sorted_labels = (
        corr_result
        .set_index('ShortLabel')
        .loc[top10_labels]
        .sort_values('Correlation')
        .reset_index()
    )

    plot_df = (
        violations_df[violations_df['ShortLabel'].isin(sorted_labels['ShortLabel'])]
        .groupby(['ShortLabel', 'Year'])
        .agg(
            AvgFine=('FINE AMOUNT', 'mean'),
            ViolationCount=('FINE AMOUNT', 'count')
        )
        .reset_index()
    )

    time_series_graphs = []
    for label in sorted_labels['ShortLabel']:
        subset = plot_df[plot_df['ShortLabel'] == label]
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
            y=subset['AvgFine'],
            name='Avg Fine ($)',
            mode='lines+markers',
            line=dict(color='indianred', dash='dot'),
            yaxis='y2'
        ))

        fig.update_layout(
            title=label,
            height=300,
            margin=dict(t=40, b=30, l=30, r=10),
            xaxis=dict(title='Year', dtick=1),
            yaxis=dict(title='Violation Count', side='left'),
            yaxis2=dict(
                overlaying='y',
                side='right',
                title='Avg Fine ($)',
                showgrid=False
            ),
            showlegend=False,
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font_color='white'
        )

        time_series_graphs.append(dcc.Graph(figure=fig))

    # Build layout
    return dbc.Container([
        html.H4("Fine-Violation Relationships", className="mb-4"),
        dcc.Graph(figure=fig_corr, className="mb-4"),
        html.Hr(),
        html.H5("Yearly Trends for Top Violation Types", className="mb-3"),
        dbc.Row([
            dbc.Col(time_series_graphs[i], md=6)
            for i in range(len(time_series_graphs))
        ])
    ], fluid=True)