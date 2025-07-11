import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.markdown("""
    <style>
    body {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', sans-serif;
    }
    .css-1v0mbdj {background-color: white;}
    </style>
""", unsafe_allow_html=True)

colors = {
    'fines': 'indianred',
    'violations': 'steelblue'
}

labels = {
    'TotalFines': 'Total Fines ($)',
    'ViolationCount': 'Violation Count',
    'AverageFines': 'Average Fine ($)'
}

st.set_page_config(page_title="NYC BIC Compliance Dashboard", layout="wide")

def load_data():
    complaints = pd.read_csv("datasets/BIC_Complaints_Inquiries_20250612.csv")
    violations = pd.read_csv("https://drive.google.com/uc?export=download&id=1SOaADySZRl_mHg--NA4M0ZiORSecljwI")
    return complaints, violations

complaints_df, violations_df = load_data()

# Short labels for violations
short_descriptions = {
    "failed to timely notify commission of a material information": "Late update to Commission",
    "a licensee must maintain copies of all inspection and certification of repair forms": "Missing inspection and or repair forms",
    "(e)   a trade waste vehicle must not be operated unless such vehicle is in safe operating": "Uncertified or unsafe trade waste vehicle",
    "a registrant must maintain copies of all daily inspection reports required by 17 rcny ? 7-03(f) for at least five (5) years": "Missing daily inspection logs",
    "an applicant for registration and a registrant": "No notice to the Commission of business changes",
    "each vehicle having a gross vehicle weight rating of": "Missing front mirror on truck",
    "a registrant must maintain copies of all inspection and certification of repair forms required by 17": "Missing 6-month repair records in vehicle",
    "a trade waste vehicle must not be operated unless": "Inspection proof not in truck",
    "it shall be unlawful for any person to operate a business for the purpose of": "No trade waste license",
    "removed collected or disposed of trade waste or without the proper commission issued license": "Unauthorized waste disposal",
    "failed to provide off-street parking":"Failed to provide off-street parking",
    "unreported change of ownership": "Ownership not filed",
}

def normalize_rule(text):
    if pd.isna(text):
        return ""
    return str(text).lower().strip().replace('\n', ' ').replace('\r', ' ')

def get_short_label(description):
    norm = normalize_rule(description)
    for key, short in short_descriptions.items():
        if norm.startswith(key):
            return short
    return description[:40] + '...' if isinstance(description, str) else "Unknown"

# Convert and filter dates
complaints_df['DATE COMPLAINT/INQUIRY REPORTED ON'] = pd.to_datetime(complaints_df['DATE COMPLAINT/INQUIRY REPORTED ON'], errors='coerce')
violations_df['DATE VIOLATION ISSUED'] = pd.to_datetime(violations_df['DATE VIOLATION ISSUED'], errors='coerce')
complaints_df = complaints_df[complaints_df['DATE COMPLAINT/INQUIRY REPORTED ON'].dt.year >= 2015]
violations_df = violations_df[violations_df['DATE VIOLATION ISSUED'].dt.year >= 2015]

violations_df['ShortLabel'] = violations_df['DESCRIPTION OF RULE'].apply(get_short_label)

# Interface layout
st.title("NYC BIC Compliance Dashboard")
tabs = st.tabs(["Overview & Summary", "Long Term Trends", "Violation Categories", "Fine-Violation Relationships", "Frequent Violators", "Key Takeaways"])

# --- Overview Tab ---
with tabs[0]:

    st.markdown("### Summary Statistics (Since 2015)")

    min_year, max_year = int(violations_df['DATE VIOLATION ISSUED'].dt.year.min()), int(violations_df['DATE VIOLATION ISSUED'].dt.year.max())
    selected_years = st.slider("Select year range", min_value=min_year, max_value=max_year, value=(2015, max_year))

    filtered_df = violations_df[
    violations_df['DATE VIOLATION ISSUED'].dt.year.between(selected_years[0], selected_years[1])
    ]

      # Calculate additional metrics
    total_accounts = filtered_df['ACCOUNT NAME'].nunique()
    avg_violations_per_account = filtered_df.shape[0] / total_accounts if total_accounts else 0
    avg_fines_per_account = filtered_df['FINE AMOUNT'].sum() / total_accounts if total_accounts else 0



    # Row 1: Violation-level stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Violations", f"{filtered_df.shape[0]:,}")
    col2.metric("Total Fines Issued", f"${filtered_df['FINE AMOUNT'].sum():,.2f}")
    col3.metric("Avg Fine per Violation", f"${filtered_df['FINE AMOUNT'].mean():,.2f}")

    # Row 2: Distribution stats
    col4, col5, col6 = st.columns(3)
    col4.metric("Median Fine per Violation", f"${filtered_df['FINE AMOUNT'].median():,.2f}")
    col5.metric("Max Fine Issued", f"${filtered_df['FINE AMOUNT'].max():,.2f}")
    col6.metric("Min Fine Issued", f"${filtered_df['FINE AMOUNT'][filtered_df['FINE AMOUNT'] > 0].min():,.2f}")

    col7, col8, col9 = st.columns(3)
    col7.metric("Total Accounts Fined", f"{total_accounts:,}")
    col8.metric("Avg Violations per Account", f"{avg_violations_per_account:.2f}")
    col9.metric("Avg Fines per Account", f"${avg_fines_per_account:,.2f}")

    st.markdown("---")  # Visual separator

    st.markdown("### Overview & Key Questions")
    st.markdown(
        """
        This dashboard explores trends in enforcement, fine issuance, and business behavior using NYC BIC data.

        **Key Questions:**
        - Does increasing fine severity lead to improved compliance behavior?
        - Which violation types are the most common?
        - Which accounts are the most frequent violators?
        """
    )

# --- Trends Over Time ---
with tabs[1]:
    st.header("Long Term Trends")

    # Ensure date columns are datetime
    complaints_df['DATE COMPLAINT/INQUIRY REPORTED ON'] = pd.to_datetime(
        complaints_df['DATE COMPLAINT/INQUIRY REPORTED ON'], errors='coerce'
    )
    violations_df['DATE VIOLATION ISSUED'] = pd.to_datetime(
        violations_df['DATE VIOLATION ISSUED'], errors='coerce'
    )

    # Extract year
    complaints_df['Year'] = complaints_df['DATE COMPLAINT/INQUIRY REPORTED ON'].dt.year
    violations_df['Year'] = violations_df['DATE VIOLATION ISSUED'].dt.year

    # Filter from 2015 onward
    complaints_df = complaints_df[complaints_df['Year'] >= 2015]
    violations_df = violations_df[violations_df['Year'] >= 2015]

    # Complaints & Violations count
    yearly_counts = pd.DataFrame({
        'Complaints': complaints_df.groupby('Year').size(),
        'Violations': violations_df.groupby('Year').size()
    }).reset_index()

    # Average Fine
    valid_violations = violations_df.dropna(subset=['FINE AMOUNT', 'Year'])
    avg_fine = (
        valid_violations
        .groupby('Year')
        .agg(TotalFines=('FINE AMOUNT', 'sum'), NumViolations=('FINE AMOUNT', 'count'))
        .assign(AverageFine=lambda df: df['TotalFines'] / df['NumViolations'])
        .reset_index()
    )

    # Cumulative new violation types
    first_seen_years = (
        violations_df.dropna(subset=['DESCRIPTION OF RULE', 'DATE VIOLATION ISSUED'])
        .groupby('DESCRIPTION OF RULE')['DATE VIOLATION ISSUED']
        .min()
        .dt.year
        .value_counts()
        .sort_index()
        .reset_index()
    )
    first_seen_years.columns = ['Year', 'NewViolationTypes']
    first_seen_years = first_seen_years[first_seen_years['Year'].between(2015, 2025)]
    first_seen_years['CumulativeViolationTypes'] = first_seen_years['NewViolationTypes'].cumsum()

    # Merge all data by year
    merged = pd.merge(yearly_counts, avg_fine[['Year', 'AverageFine']], on='Year', how='left')
    merged = pd.merge(merged, first_seen_years[['Year', 'CumulativeViolationTypes']], on='Year', how='left')

    # Plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=merged['Year'], y=merged['Complaints'],
        mode='lines+markers', name='Complaints', yaxis='y1'
    ))
    fig.add_trace(go.Scatter(
        x=merged['Year'], y=merged['Violations'],
        mode='lines+markers', name='Violations', yaxis='y1'
    ))
    fig.add_trace(go.Scatter(
        x=merged['Year'], y=merged['AverageFine'],
        mode='lines+markers', name='Average Fine ($)', yaxis='y2', line=dict(dash='dot')
    ))
    fig.add_trace(go.Bar(
        x=merged['Year'], y=merged['CumulativeViolationTypes'],
        name='Cumulative Violation Types',
        marker_color='lightgray',
        opacity=0.5,
        yaxis='y1'
    ))

    fig.update_layout(
        xaxis=dict(title='Year'),
        yaxis=dict(title='Complaints / Violations / Cumulative Types', side='left'),
        yaxis2=dict(title=labels['AverageFines'], overlaying='y', side='right'),
        legend=dict(x=0.5, xanchor='center', y=1.15, orientation='h'),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    #with st.expander("Why this matters"):
     #   st.markdown("""
      #  This chart shows how complaint and violation volumes have shifted over time, alongside average fines. 
       # The gray bars show how new violation types have accumulated, helping contextualize enforcement complexity and policy evolution.
        #""")
    
    
    # Ensure datetime format
    # Ensure datetime format
    violations_df['DATE VIOLATION ISSUED'] = pd.to_datetime(violations_df['DATE VIOLATION ISSUED'], errors='coerce')

    # Add year column
    violations_df['Year'] = violations_df['DATE VIOLATION ISSUED'].dt.year

    # Identify when each unique violation type (by description) was first seen
    first_seen_years = (
        violations_df.dropna(subset=['DESCRIPTION OF RULE', 'DATE VIOLATION ISSUED'])
        .groupby('DESCRIPTION OF RULE')['DATE VIOLATION ISSUED']
        .min()
        .dt.year
        .value_counts()
        .sort_index()
        .reset_index()
    )

    # Rename columns properly
    first_seen_years.columns = ['Year', 'NewViolationTypes']

    # Filter to 2020–2025 and calculate cumulative sum
    new_violations_per_year = first_seen_years[first_seen_years['Year'].between(2015, 2025)].copy()
    new_violations_per_year['Cumulative'] = new_violations_per_year['NewViolationTypes'].cumsum()

    # Build combined bar and line plot
    fig = go.Figure()

    # Bar for new violation types per year
    fig.add_trace(go.Bar(
        x=new_violations_per_year['Year'],
        y=new_violations_per_year['NewViolationTypes'],
        name='New Violation Types',
        marker_color='indianred'
    ))


    # Line for cumulative total
    fig.add_trace(go.Scatter(
        x=new_violations_per_year['Year'],
        y=new_violations_per_year['Cumulative'],
        name='Cumulative Total',
        mode='lines+markers',
        line=dict(color='steelblue', dash='dot')
    ))

    # Layout
    fig.update_layout(
        title='New Violation Types Introduced (2020–2025)',
        xaxis_title='Year',
        yaxis_title='Count',
        xaxis=dict(dtick=1),
        legend=dict(x=0.5, xanchor='center', y=1.15, orientation='h'),
        height=500
    )

    st.plotly_chart(fig)


with tabs[2]:
    st.subheader("Violation Categories")

    # Get top 10 violation types by frequency
    top_labels = (
        violations_df['ShortLabel'].value_counts()
        .head(10)
        .index.tolist()
    )

    filtered = violations_df[violations_df['ShortLabel'].isin(top_labels)].dropna(subset=['ShortLabel'])

    # Compute statistics
    stats = (
        filtered.groupby('ShortLabel')['FINE AMOUNT']
        .agg(['mean', 'median', 'min', 'max'])
        .reset_index()
        .rename(columns={
            'mean': 'AvgFine',
            'median': 'MedianFine',
            'min': 'MinFine',
            'max': 'MaxFine'
        })
    )

    # Violation counts
    counts = (
        filtered['ShortLabel']
        .value_counts()
        .rename_axis('ShortLabel')
        .reset_index(name='Count')
    )

    # Rule descriptions
    descriptions = (
        filtered.drop_duplicates(subset='ShortLabel')[['ShortLabel', 'DESCRIPTION OF RULE']]
    )

    # Merge into single DataFrame
    top_types = (
        counts.merge(stats, on='ShortLabel')
              .merge(descriptions, on='ShortLabel')
              .sort_values(by="Count", ascending=False)  # sort by frequency
    )

       # Calculate share of top 10 violation types
    all_violations = violations_df.shape[0]
    all_fines = violations_df['FINE AMOUNT'].sum()

    top10_data = violations_df[violations_df['ShortLabel'].isin(top_types['ShortLabel'])]
    top10_violations = top10_data.shape[0]
    top10_fines = top10_data['FINE AMOUNT'].sum()

    pct_violations = (top10_violations / all_violations) * 100
    pct_fines = (top10_fines / all_fines) * 100

    # Display metrics
    st.markdown("### Top 10 Violation Types Summary")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Violations from Top 10", f"{top10_violations:,}", help="Number of violations from the 10 most common types")
        st.metric("Percent of All Violations", f"{pct_violations:.2f}%", help="Share of total violations")
    with col2:
        st.metric("Fines from Top 10", f"${top10_fines:,.2f}", help="Total fines from top 10 violation types")
        st.metric("Percent of All Fines", f"{pct_fines:.2f}%", help="Share of total fines")

    # Bar chart (with limited hover info)
    fig_vio = px.bar(
        top_types,
        x='Count',
        y='ShortLabel',
        orientation='h',
        title="Top 10 Violation Types",
        hover_data={
            'DESCRIPTION OF RULE': False,
            'ShortLabel': False,
            'Count': True,
            'AvgFine': ':.2f',
        },
        labels={'Count': 'Violation Count', 'AvgFine': 'Avg Fine ($)'},
        color_discrete_sequence=['steelblue']
    )

    fig_vio.update_layout(
        yaxis_title="Violation Type",
        xaxis_title="Number of Violations"
    )

    st.plotly_chart(fig_vio)

    #with st.expander("Why this matters"):
     #   st.markdown("""
      #  This chart shows the most frequent violation types and how costly they are on average.
       # Understanding which violations are both common and expensive can guide enforcement and policy focus.
        #""")

    # Box Plot for Fine Distribution (Min / Median / Max)
    summary_stats = (
        filtered.groupby('ShortLabel')['FINE AMOUNT']
        .agg(Min='min', Median='median', Max='max')
        .reset_index()
    )

    fig_box = go.Figure()

    for _, row in summary_stats.iterrows():
        label = row['ShortLabel']
        fines = filtered[filtered['ShortLabel'] == label]['FINE AMOUNT']
        fines = fines[fines > 0]  # Exclude zero fines

        fig_box.add_trace(go.Box(
            y=fines,
            name=label,
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
        height=550
    )

    st.plotly_chart(fig_box)

    #with st.expander("Why this matters"):
     #   st.markdown("""
      #  These box plots show the distribution of fines for the top 10 most common violation types.
       # By looking at the minimum, median, and maximum fines, we can identify which violations tend to carry
        #higher penalties, which ones have more variability, and where enforcement may be most impactful.
        #""")

with tabs[3]:
    st.subheader("Fine-Violation Relationships")

    # Calculate year again (if not already)
    violations_df['Year'] = pd.to_datetime(violations_df['DATE VIOLATION ISSUED'], errors='coerce').dt.year
    violations_df = violations_df[violations_df['Year'] >= 2015]

    # Top 10 frequent violation types
    st.subheader("Top 10 Most Common Violation Types: Correlation Between Avg Fine and Count")

    top10_labels = violations_df['ShortLabel'].value_counts().head(10).index

    corr_top10_df = (
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

    corr_top10_result = (
        corr_top10_df
        .groupby('ShortLabel')[['AvgFine', 'ViolationCount']]
        .corr()
        .iloc[0::2, -1]
        .reset_index()
        .rename(columns={'ShortLabel': 'Violation Type', 'ViolationCount': 'Correlation'})
        .drop(columns=['level_1'])
    )

    fig_corr_top10 = px.bar(
        corr_top10_result.sort_values(by='Correlation'),
        x='Correlation',
        y='Violation Type',
        orientation='h',
        color='Correlation',
        color_continuous_scale='RdBu'
    )
    fig_corr_top10.update_layout(
        yaxis_title="Violation Type",
        xaxis_title="Correlation (Avg Fine vs Count)"
    )
    st.plotly_chart(fig_corr_top10)

    #with st.expander("Why this matters"):
     #   st.markdown("""
      #  This correlation plot explores whether increasing fines are associated with changes in violation frequency 
       # across top categories. It can suggest whether fines are acting as a deterrent.
        #""")


    st.subheader("Average Price & Violation Counts per Violation Type")

    # Prepare data
    top10_labels = violations_df['ShortLabel'].value_counts().head(10).index

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

    sorted_labels = (
        corr_result.set_index('ShortLabel')
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

    st.markdown("### Legend")
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 10px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 30px; height: 3px; background-color: indianred; margin-right: 5px;"></div>
                <span style="color: white;">Avg Fine ($)</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 15px; height: 15px; background-color: steelblue; margin-right: 5px;"></div>
                <span style="color: white;">Violation Count</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    top_violation_plots = []
    for short_label in sorted_labels['ShortLabel']:
        subset = plot_df[plot_df['ShortLabel'] == short_label]
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=subset['Year'],
            y=subset['ViolationCount'],
            name='Violation Count',
            marker_color=colors['violations'],
            yaxis='y1'
        ))

        fig.add_trace(go.Scatter(
            x=subset['Year'],
            y=subset['AvgFine'],
            mode='lines+markers',
            name='Avg Fine ($)',
            line=dict(color='indianred'),
            yaxis='y2'
        ))

        fig.update_layout(
            title=short_label,
            height=300,
            margin=dict(t=40, b=30, l=30, r=10),
            xaxis=dict(title='Year', dtick=1),
            yaxis=dict(title=labels['ViolationCount'], side='left'),
            yaxis2=dict(
                overlaying='y',
                side='right',
                title='Avg Fine ($)',
                showgrid=False
            ),
            showlegend=False
        )

        top_violation_plots.append(fig)

    row_col_counts = [3, 3, 2, 2]
    rows = [st.columns(n) for n in row_col_counts]

    plot_idx = 0
    for row_idx, col_count in enumerate(row_col_counts):
        for col_idx in range(col_count):
            if plot_idx < len(top_violation_plots):
                with rows[row_idx][col_idx]:
                    st.plotly_chart(top_violation_plots[plot_idx], use_container_width=True)
                plot_idx += 1
    
    #with st.expander("Why this matters"):
     #   st.markdown("""
      #  These charts compare how the average fine and number of violations have evolved for specific violation types.
       # Observing these trends help assess if financial penalties are effectively influencing behavior.
        #""")

# --- Frequent Violators Tab ---
with tabs[4]:
    st.subheader("Frequent Violators")

    rank_by = st.radio(
        "Show Top 10 Accounts by:",
        ["Total Fines", "Violation Count"],
        horizontal=True,
        help="Choose whether to rank businesses by the amount they’ve been fined or by how many violations they’ve committed."
    )

    violations_df = violations_df.dropna(subset=['ACCOUNT NAME', 'FINE AMOUNT'])

    account_summary = (
        violations_df
        .groupby('ACCOUNT NAME')
        .agg(
            TotalFines=('FINE AMOUNT', 'sum'),
            ViolationCount=('FINE AMOUNT', 'count')
        )
        .reset_index()
    )

    sort_column = 'TotalFines' if rank_by == 'Total Fines' else 'ViolationCount'
    account_summary = account_summary.sort_values(by=sort_column, ascending=False).head(10)
    top_accounts = account_summary['ACCOUNT NAME']

    total_violations = violations_df.shape[0]
    total_fines = violations_df['FINE AMOUNT'].sum()

    # Calculate total across all data
    total_violations = violations_df.shape[0]
    total_fines = violations_df['FINE AMOUNT'].sum()

    # Calculate totals for top 10 accounts
    top10_data = violations_df[violations_df['ACCOUNT NAME'].isin(top_accounts)]
    top10_violations = top10_data.shape[0]
    top10_fines = top10_data['FINE AMOUNT'].sum()

    # Calculate percentages
    pct_violations = (top10_violations / total_violations) * 100
    pct_fines = (top10_fines / total_fines) * 100

    # Display totals and percentages
    st.markdown("### Top 10 Account Summary")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Violations by Top 10", f"{top10_violations:,}", help="Number of violations associated with the top 10 accounts")
        st.metric("Percent of All Violations", f"{pct_violations:.2f}%", help="Share of total violations caused by top 10")
    with col2:
        st.metric("Fines from Top 10", f"${top10_fines:,.2f}", help="Dollar amount of fines from top 10 accounts")
        st.metric("Percent of All Fines", f"{pct_fines:.2f}%", help="Share of total fines attributable to top 10")


    fig = go.Figure()

    primary_y, secondary_y = ('ViolationCount', 'TotalFines') if rank_by == 'Violation Count' else ('TotalFines', 'ViolationCount')
    primary_color, secondary_color = ('steelblue', 'indianred') if rank_by == 'Violation Count' else ('indianred', 'steelblue')

    fig.add_trace(go.Bar(
        x=account_summary['ACCOUNT NAME'],
        y=account_summary[primary_y],
        name=primary_y.replace("Count", " Count").replace("Fines", " Fines ($)"),
        marker_color=primary_color,
        yaxis='y1',
        offsetgroup=0
    ))

    fig.add_trace(go.Bar(
        x=account_summary['ACCOUNT NAME'],
        y=account_summary[secondary_y],
        name=secondary_y.replace("Count", " Count").replace("Fines", " Fines ($)"),
        marker_color=secondary_color,
        yaxis='y2',
        offsetgroup=1
    ))

    fig.update_layout(
        barmode='group',
        title=f"Top 10 Accounts by {rank_by}: Fines vs Violations",
        xaxis=dict(title='Account Name', tickangle=-45),
        yaxis=dict(title=primary_y.replace("Count", " Count").replace("Fines", " Fines ($)"), side='left'),
        yaxis2=dict(
            title=secondary_y.replace("Count", " Count").replace("Fines", " Fines ($)"),
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(x=0.5, y=1.15, orientation='h', xanchor='center'),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    #with st.expander("Why this matters"):
     #   st.markdown("""
      #  Identifying the top violators pin points high-risk businesses
       # allowing for investigating recurring issues in more depth.
        #""")

    # Time Series Section
    st.subheader(f"Violations and Fines Over Time: Top 10 by {rank_by}")

    fine_metric = st.radio(
        "Choose fine metric to display:",
        ["Total Fines", "Average Fines"],
        horizontal=True,
        help="Total Fines = sum of all fines issued in a year. Average Fines = average fine amount per violation."
    )

    st.markdown("### Legend")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 10px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 30px; height: 3px; background-color: indianred; margin-right: 5px;"></div>
                <span style="color: white;">{fine_metric}</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 15px; height: 15px; background-color: steelblue; margin-right: 5px;"></div>
                <span style="color: white;">Violation Count</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    top_violations_df = violations_df[violations_df['ACCOUNT NAME'].isin(top_accounts)].copy()
    top_violations_df['DATE VIOLATION ISSUED'] = pd.to_datetime(top_violations_df['DATE VIOLATION ISSUED'], errors='coerce')
    top_violations_df['Year'] = top_violations_df['DATE VIOLATION ISSUED'].dt.year
    top_violations_df = top_violations_df[top_violations_df['Year'] >= 2015]

    plot_df = (
        top_violations_df
        .groupby(['ACCOUNT NAME', 'Year'])
        .agg(
            TotalFines=('FINE AMOUNT', 'sum'),
            ViolationCount=('FINE AMOUNT', 'count'),
            AverageFines=('FINE AMOUNT', 'mean')
        )
        .reset_index()
    )

    top_offender_plots = []
    for account in top_accounts:
        subset = plot_df[plot_df['ACCOUNT NAME'] == account]
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=subset['Year'],
            y=subset['ViolationCount'],
            name='Violation Count',
            marker_color=colors['violations'],
            yaxis='y1'
        ))

        fig.add_trace(go.Scatter(
            x=subset['Year'],
            y=subset['AverageFines'] if fine_metric == "Average Fines" else subset['TotalFines'],
            name=fine_metric,
            mode='lines+markers',
            line=dict(color='indianred'),
            yaxis='y2'
        ))

        fig.update_layout(
            title=account,
            xaxis=dict(title='Year', dtick=1),
            yaxis=dict(title=labels['ViolationCount'], side='left'),
            yaxis2=dict(
                title=fine_metric,
                overlaying='y',
                side='right',
                showgrid=False
            ),
            height=300,
            margin=dict(t=40, b=30, l=30, r=30),
            showlegend=False
        )

        top_offender_plots.append(fig)

    row_col_counts = [3, 3, 2, 2]
    rows = [st.columns(n) for n in row_col_counts]

    plot_idx = 0
    for row_idx, col_count in enumerate(row_col_counts):
        for col_idx in range(col_count):
            if plot_idx < len(top_offender_plots):
                with rows[row_idx][col_idx]:
                    st.plotly_chart(top_offender_plots[plot_idx], use_container_width=True)
                plot_idx += 1

    #with st.expander("Why this matters"):
     #   st.markdown("""
      #  Tracking violations and fines over time for specific businesses provides insight into whether 
       # enforcement actions (increasing fines) lead to changes in behavior.
        #""")
with tabs[5]:
    st.markdown("### Key Findings")
    st.markdown(
        """
        - **Increased Enforcement Appears Effective:** Violations tend to decline after years of expanded 
        enforcement and higher fines — suggesting higher compliance.
        - **A Few Violation Types and Accounts Drive Most Activity:** A small number of violation types and repeat violators account for a 
        large share of total fines and violations..
        - **Targeted Enforcement and Education Can Improve Compliance:** Combining penalties with proactive outreach 
        or education may help reduce repeat offenses and improve long-term outcomes.
        """
    )