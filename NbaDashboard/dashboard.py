import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def load_data():
    df = pd.read_csv("datasets/nba_team_combined_2010_2024.csv")
    return df

px.scatter(df, x="3PA", y="W", color="Season", hover_name="Team", trendline="ols")