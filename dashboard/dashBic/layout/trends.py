from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

def render_trends(complaints_df, violations_df):
    # --- Data Preparation ---
    yearly_counts = pd.DataFrame({
        'Complaints': complaints_df.groupby('Year').size(),
        'Violations': violations_df.groupby('Year').size()
    }).reset_index()

    avg_fine = (
        violations_df.dropna(subset=['FINE AMOUNT', 'Year'])
        .groupby('Year')
        .agg(TotalFines=('FINE AMOUNT', 'sum'), NumViolations=('FINE AMOUNT', 'count'))
        .assign(AverageFine=lambda df: df['TotalFines'] / df['NumViolations'])
        .reset_index()
    )

    first_seen_years = (
        violations_df.dropna(subset=['DESCRIPTION OF RULE', 'DATE VIOLATION ISSUED'])
        .groupby('DESCRIPTION OF RULE')['DATE VIOLATION ISSUED']
        .min().dt.year.value_counts().sort_index().reset_index()
    )
    first_seen_years.columns = ['Year', 'NewViolationTypes']
    first_seen_years = first_seen_years[first_seen_years['Year'].between(2015, 2025)]
    first_seen_years['CumulativeViolationTypes'] = first_seen_years['NewViolationTypes'].cumsum()

    merged = pd.merge(yearly_counts, avg_fine[['Year', 'AverageFine']], on='Year', how='left')
    merged = pd.merge(merged, first_seen_years[['Year', 'CumulativeViolationTypes']], on='Year', how='left')

    # --- Figure 1: Trends ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=merged['Year'], y=merged['Complaints'], mode='lines+markers', name='Complaints'))
    fig.add_trace(go.Scatter(x=merged['Year'], y=merged['Violations'], mode='lines+markers', name='Violations'))
    fig.add_trace(go.Scatter(x=merged['Year'], y=merged['AverageFine'], mode='lines+markers',
                             name='Average Fine ($)', yaxis='y2', line=dict(dash='dot')))
    fig.add_trace(go.Bar(x=merged['Year'], y=merged['CumulativeViolationTypes'],
                         name='Cumulative Violation Types', marker_color='lightgray', opacity=0.5))

    fig.update_layout(
        xaxis=dict(title='Year'),
        yaxis=dict(title='Complaints / Violations / Cumulative Types'),
        yaxis2=dict(title='Average Fine ($)', overlaying='y', side='right'),
        legend=dict(x=0.5, xanchor='center', y=1.15, orientation='h'),
        height=600,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )

    # --- Figure 2: New Violation Types ---
    new_violations_df = (
        violations_df.dropna(subset=['DESCRIPTION OF RULE', 'DATE VIOLATION ISSUED'])
        .groupby('DESCRIPTION OF RULE')['DATE VIOLATION ISSUED']
        .min()
        .dt.year
        .value_counts()
        .sort_index()
        .reset_index()
    )
    new_violations_df.columns = ['Year', 'NewViolationTypes']
    new_violations_df = new_violations_df[new_violations_df['Year'].between(2015, 2025)]
    new_violations_df['Cumulative'] = new_violations_df['NewViolationTypes'].cumsum()

    new_types_fig = go.Figure()
    new_types_fig.add_trace(go.Bar(
        x=new_violations_df['Year'],
        y=new_violations_df['NewViolationTypes'],
        name='New Violation Types',
        marker_color='indianred'
    ))
    new_types_fig.add_trace(go.Scatter(
        x=new_violations_df['Year'],
        y=new_violations_df['Cumulative'],
        name='Cumulative Total',
        mode='lines+markers',
        line=dict(color='steelblue', dash='dot')
    ))

    new_types_fig.update_layout(
        title='New Violation Types Introduced (2015–2025)',
        xaxis_title='Year',
        yaxis_title='Count',
        xaxis=dict(dtick=1),
        legend=dict(x=0.5, xanchor='center', y=1.15, orientation='h'),
        height=500,
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white'
    )

    # --- Combine Both Charts with Consistent Bootstrap Layout ---
    return dbc.Container([
        html.H4("Long Term Trends"),
        dcc.Graph(figure=fig, style={"marginBottom": "40px"}),
        html.H4("New Violation Types Introduced"),
        dcc.Graph(figure=new_types_fig)
    ], className="mt-4")