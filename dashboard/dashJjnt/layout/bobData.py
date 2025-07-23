from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

def render_trading_trends(bobData_df):
    df = bobData_df.copy()
    
    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df = df.dropna(subset=['Date'])

    # Columns to plot
    pnl_cols = [
        'GC', 'NinzaRenko 8/4', 'GC 15 Min', 'CL', 'HG',
        'ES', 'NQ NinzaRenko 8/4', 'NQ 1 minute', 'RTY', 'YM', 'Total Pnl'
    ]

    for col in pnl_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- Main Combined Figure ---
    main_fig = go.Figure()

    for col in pnl_cols:
        main_fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df[col],
            mode='lines+markers',
            name=col
        ))

    main_fig.update_layout(
        title=dict(
            text="Daily PnL by Instrument",
            x=0.5,
            xanchor='center',
            yanchor='top',
            pad=dict(t=20, b=0)
        ),
        xaxis_title="Date",
        yaxis_title="PnL ($)",
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.3,
            x=0.5,
            xanchor='center',
            title_text='',
            font=dict(size=11)
        ),
        height=700,
        margin=dict(l=40, r=40, t=80, b=100),
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font_color='white',
        shapes=[{
            'type': 'line',
            'y0': 0, 'y1': 0,
            'x0': df['Date'].min(), 'x1': df['Date'].max(),
            'line': {'color': 'yellow', 'width': 3}
        }]
    )

    # --- Individual Figures for Each Instrument in 2 Columns Per Row ---
    rows = []
    for i in range(0, len(pnl_cols), 2):
        row_children = []
        for col in pnl_cols[i:i+2]:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df[col],
                mode='lines+markers',
                name=col,
                line=dict(color='steelblue', width=2)
            ))
            fig.add_shape(
                type='line',
                x0=df['Date'].min(), x1=df['Date'].max(),
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

    # --- Return Layout ---
    return dbc.Container([
        html.H4("Trading Performance Overview"),
        dcc.Graph(figure=main_fig),
        html.Hr(),
        html.H4("Individual Instrument Performance"),
        *rows  # Unpack the rows
    ], className="mt-4")