import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import gdown
import os

st.set_page_config(layout="wide")

# Load data from Google Drive using gdown with local caching
@st.cache_data
def load_data():
    # Google Drive file IDs
    indoor_id = "1YPNmFBB5xo2QJr05NR0elhLEceXA6XBZ"
    outdoor_id = "1nA15O8JQPNmg0ph2uXkV7E-R4tFQwEqQ"

    # Download only if files are not already present
    if not os.path.exists("indoor.csv"):
        gdown.download(f"https://drive.google.com/uc?id={indoor_id}", "indoor.csv", quiet=False, fuzzy=True)
    if not os.path.exists("outdoor.csv"):
        gdown.download(f"https://drive.google.com/uc?id={outdoor_id}", "outdoor.csv", quiet=False)

    # Load CSVs
    indoor = pd.read_csv("indoor.csv")
    outdoor = pd.read_csv("outdoor.csv")

    # Clean and convert datetime
    indoor.columns = indoor.columns.str.strip()
    outdoor.columns = outdoor.columns.str.strip()
    indoor['Datetime'] = pd.to_datetime(indoor['Datetime'], errors='coerce')
    outdoor['DateTime'] = pd.to_datetime(outdoor['DateTime'], errors='coerce')

    return indoor, outdoor

indoor_df, outdoor_df = load_data()

# Sidebar for filters

def sidebar_filters(df, key_prefix):
    st.sidebar.markdown("### Filters")
    time_col = 'Datetime' if 'Datetime' in df.columns else 'DateTime'
    date_range = st.sidebar.date_input(
        f"Select Date Range",  # Label must be unique across widgets
        [df[time_col].min().date(), df[time_col].max().date()],
        key=f"{key_prefix}_date"
    )
    hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23), key=f"{key_prefix}_hour")
    cols = df.select_dtypes(include='number').columns.tolist()
    cols = [c for c in cols if c.lower() != 'entry_id']
    column = st.sidebar.selectbox("Select Parameter", cols, key=f"{key_prefix}_col")
    cooking_filter = st.sidebar.checkbox("Show only Cooking Time", value=False, key=f"{key_prefix}_cook")
    return date_range, hour_range, column, cooking_filter, time_col

# Apply filters
def apply_filters(df, date_range, hour_range, cooking_filter, time_col):
    df_filtered = df[
        (df[time_col].dt.date >= date_range[0]) &
        (df[time_col].dt.date <= date_range[1]) &
        (df[time_col].dt.hour >= hour_range[0]) &
        (df[time_col].dt.hour <= hour_range[1])
    ]
    if cooking_filter and 'Cooking' in df.columns:
        df_filtered = df_filtered[df_filtered['Cooking'] == 1]
    return df_filtered

# Plotting
def plot_data(df, column, time_col):
    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    # Downsample large datasets
    max_points = 1000
    if len(df) > max_points:
        df = df.sample(n=max_points).sort_values(time_col)

    st.line_chart(df.set_index(time_col)[column])
    st.bar_chart(df.set_index(time_col)[column])
    st.write("Correlation Heatmap")
    corr = df.select_dtypes(include='number').corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, ax=ax)
    st.pyplot(fig)

# Main UI
tabs = st.tabs(["Indoor Air Quality", "Outdoor Air Quality"])

with tabs[0]:
    st.header("Indoor Air Quality Dashboard")
    with st.spinner("Loading indoor data and visualizations..."):
        date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(indoor_df, key_prefix="indoor")
        filtered = apply_filters(indoor_df, date_range, hour_range, cooking_filter, time_col)
        plot_data(filtered, column, time_col)

with tabs[1]:
    st.header("Outdoor Air Quality Dashboard")
    with st.spinner("Loading outdoor data and visualizations..."):
        date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(outdoor_df, key_prefix="outdoor")
        filtered = apply_filters(outdoor_df, date_range, hour_range, cooking_filter, time_col)
        plot_data(filtered, column, time_col)

st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit")
