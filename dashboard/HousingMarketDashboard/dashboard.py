import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    zhvi = pd.read_csv("datasets/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv")
    zori = pd.read_csv("datasets/Metro_zori_uc_sfrcondomfr_sm_month.csv")
    return zhvi, zori

zhvi, zori = load_data()

# Preprocess
def preprocess_data(zhvi, zori):
    zhvi_long = zhvi.melt(
        id_vars=["RegionID", "SizeRank", "RegionName", "RegionType", "StateName"],
        var_name="Date", value_name="HomeValue"
    )
    zori_long = zori.melt(
        id_vars=["RegionID", "SizeRank", "RegionName", "RegionType", "StateName"],
        var_name="Date", value_name="Rent"
    )

    zhvi_long["Date"] = pd.to_datetime(zhvi_long["Date"])
    zori_long["Date"] = pd.to_datetime(zori_long["Date"])

    merged = pd.merge(
        zhvi_long,
        zori_long[["RegionName", "Date", "Rent"]],
        on=["RegionName", "Date"],
        how="inner"
    )

    merged["RentToPrice"] = (merged["Rent"] * 12) / merged["HomeValue"]
    merged["ZHVI_YoY"] = merged.groupby("RegionName")["HomeValue"].pct_change(periods=12) * 100

    return merged

merged = preprocess_data(zhvi, zori)

st.set_page_config(layout="wide")
st.title("🏘️ Housing Investment Dashboard")

# Sidebar filters
st.sidebar.title("Select Filters")

date_range = (merged["Date"].min().date(), merged["Date"].max().date())
selected_date = st.sidebar.slider(
    "Select Date",
    *date_range,
    value=merged["Date"].max().date(),
    format="YYYY-MM"
)

# --- State Filter ---
states = sorted(merged["StateName"].dropna().unique())
st.sidebar.markdown("### Filter by State")
selected_state = st.sidebar.selectbox("Select State", ["All"] + states)

# --- Region Lookup ---
region_lookup = merged[["RegionName", "StateName"]].dropna().drop_duplicates()
region_lookup["Label"] = region_lookup["StateName"] + " – " + region_lookup["RegionName"]
region_lookup = region_lookup.sort_values(by=["StateName", "RegionName"])
region_dict = dict(zip(region_lookup["Label"], region_lookup["RegionName"]))

# --- Filtered region options for current state ---
if selected_state == "All":
    filtered_region_lookup = region_lookup
else:
    filtered_region_lookup = region_lookup[region_lookup["StateName"] == selected_state]

# --- Session state for metro selections ---
if "selected_labels" not in st.session_state:
    st.session_state.selected_labels = []

# Only show previously selected metros that still exist
valid_labels = region_lookup["Label"].tolist()
st.session_state.selected_labels = [
    label for label in st.session_state.selected_labels if label in valid_labels
]

# Show filtered list (current state), but default to intersection of previous selection
new_selection = st.sidebar.multiselect(
    "Select Metro Areas",
    options=filtered_region_lookup["Label"].tolist(),
    default=[label for label in st.session_state.selected_labels if label in filtered_region_lookup["Label"].tolist()]
)

# Add any new selections to the session state
for label in new_selection:
    if label not in st.session_state.selected_labels:
        st.session_state.selected_labels.append(label)

# Optional: Remove deselected metros ONLY from the current state
for label in filtered_region_lookup["Label"]:
    if label not in new_selection and label in st.session_state.selected_labels:
        st.session_state.selected_labels.remove(label)

# Final region names
selected_regions = [region_dict[label] for label in st.session_state.selected_labels]

# Filter by date and region
selected_date_dt = pd.to_datetime(selected_date)
latest_df = merged[merged["Date"].dt.to_period("M") == pd.Period(selected_date, freq='M')]
region_df = merged[merged["RegionName"].isin(selected_regions)]

primary_region = selected_regions[0] if selected_regions else None
latest_row_df = latest_df[latest_df["RegionName"].isin(selected_regions)]

# Layout
col1, col2, col3 = st.columns([1, 2, 1])

# --- COLUMN 1: Filters + KPIs ---
with col1:
    st.markdown("### 🔧 Filters")
    st.markdown(f"**Date:** {selected_date_dt}")
    st.markdown(f"**Regions:** {selected_regions}")
    st.divider()

    st.markdown("### 📊 KPIs")
    if not latest_row_df.empty:
        for _, row in latest_row_df.iterrows():
            st.markdown(f"#### {row['RegionName']}")
            st.metric("Median Home Value", f"${row['HomeValue']:,.0f}" if pd.notna(row['HomeValue']) else "N/A")
            st.metric("Median Rent", f"${row['Rent']:,.0f}" if pd.notna(row['Rent']) else "N/A")
            st.metric("Rent-to-Price Ratio", f"{row['RentToPrice']:.2%}" if pd.notna(row['RentToPrice']) else "N/A")
            st.metric("YoY Appreciation", f"{row['ZHVI_YoY']:.2f}%" if pd.notna(row['ZHVI_YoY']) else "N/A")
    else:
        st.warning("No data for these regions and date.")

# --- COLUMN 2: Trends + Bar Charts ---
with col2:
    with st.container():
        st.markdown(f"### 📈 Trends for {selected_regions}")
        fig = go.Figure()

        for region in selected_regions:
            region_data = region_df[region_df["RegionName"] == region]
            fig.add_trace(go.Scatter(
                x=region_data["Date"], y=region_data["HomeValue"],
                name=f"{region} – Home Value", mode="lines"
            ))
            fig.add_trace(go.Scatter(
                x=region_data["Date"], y=region_data["Rent"] * 12,
                name=f"{region} – Annual Rent", mode="lines", line=dict(dash='dot')
            ))

        fig.update_layout(
            title="Home Value vs. Annual Rent Over Time",
            xaxis_title="Date", yaxis_title="USD",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("### 🏆 Top 10 Metros by Rent-to-Price")
        top10 = latest_df.dropna(subset=["RentToPrice"]).sort_values(by="RentToPrice", ascending=False).head(10)
        fig2 = px.bar(top10, x="RentToPrice", y="RegionName", orientation="h",
                      labels={"RentToPrice": "Rent-to-Price Ratio"}, title="Top 10 Rent Yields")
        fig2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.markdown("### 🚀 Top 10 Metros by YoY Appreciation")
        top_growth = latest_df.dropna(subset=["ZHVI_YoY"]).sort_values(by="ZHVI_YoY", ascending=False).head(10)
        fig3 = px.bar(top_growth, x="ZHVI_YoY", y="RegionName", orientation="h",
                      labels={"ZHVI_YoY": "YoY Appreciation (%)"}, title="Top 10 Growth Markets")
        fig3.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig3, use_container_width=True)

# --- COLUMN 3: Rankings + About ---
with col3:
  with st.container():
        st.markdown("### 📋 Rankings")

        # Top 5 overall from the full dataset
        ranked_all = latest_df.dropna(subset=["RentToPrice", "ZHVI_YoY"]).copy()
        ranked_all["Score"] = ranked_all["RentToPrice"] * ranked_all["ZHVI_YoY"]
        top5 = ranked_all.sort_values(by="Score", ascending=False).head(5)

        st.markdown("#### Top 5 Investment Metros (Overall)")
        st.dataframe(top5[["RegionName", "StateName", "RentToPrice", "ZHVI_YoY", "Score"]].round(3), height=200)

        # Ranking of selected metros only
        ranked_selected = latest_row_df.dropna(subset=["RentToPrice", "ZHVI_YoY"]).copy()
        ranked_selected["Score"] = ranked_selected["RentToPrice"] * ranked_selected["ZHVI_YoY"]
        ranked_selected = ranked_selected.sort_values(by="Score", ascending=False)

        st.markdown("#### Selected Metros Ranked by Score")
        st.dataframe(ranked_selected[["RegionName", "StateName", "RentToPrice", "ZHVI_YoY", "Score"]].round(3), height=250)

        st.divider()
        st.markdown("### ℹ️ About")
        st.info("""
        This dashboard analyzes Zillow housing and rent data to identify investment opportunities.
        It scores metros based on rental yield (Rent-to-Price) and price appreciation (YoY %).
        Built with Python, Streamlit, and Zillow Research data.
        """)

