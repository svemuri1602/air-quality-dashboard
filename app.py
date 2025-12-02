import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import gdown
import os

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    indoor_id = "1Kr96yny-8P5GN3SybOdQYSZ11O-_7Vfe"
    outdoor_id = "1Cvy83xiTqzRnmiSiUCRhMMkAWwpKKA22"

    if not os.path.exists("indoor.csv"):
        gdown.download(f"https://drive.google.com/uc?id={indoor_id}", "indoor.csv", quiet=False, fuzzy=True)
    if not os.path.exists("outdoor.csv"):
        gdown.download(f"https://drive.google.com/uc?id={outdoor_id}", "outdoor.csv", quiet=False)

    indoor = pd.read_csv("indoor.csv")
    outdoor = pd.read_csv("outdoor.csv")

    indoor.columns = indoor.columns.str.strip()
    outdoor.columns = outdoor.columns.str.strip()
    indoor['Datetime'] = pd.to_datetime(indoor['Datetime'], errors='coerce')
    outdoor['DateTime'] = pd.to_datetime(outdoor['DateTime'], errors='coerce')

    return indoor, outdoor

indoor_df, outdoor_df = load_data()

def sidebar_filters(df, prefix):
    st.sidebar.markdown("### Filters")
    time_col = 'Datetime' if 'Datetime' in df.columns else 'DateTime'
    date_range = st.sidebar.date_input(
        f"Select Date Range ({prefix})",
        [df[time_col].min().date(), df[time_col].max().date()],
        key=f"{prefix}_date"
    )
    hour_range = st.sidebar.slider(f"Select Hour Range ({prefix})", 0, 23, (0, 23), key=f"{prefix}_hour")
    cols = df.select_dtypes(include='number').columns.tolist()
    cols = [c for c in cols if c.lower() != 'entry_id']
    column = st.sidebar.selectbox(f"Select Parameter ({prefix})", cols, key=f"{prefix}_col")
    cooking_filter = st.sidebar.checkbox(f"Show only Cooking Time ({prefix})", value=False, key=f"{prefix}_cook")
    return date_range, hour_range, column, cooking_filter, time_col

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

def plot_data(df, column, time_col, prefix):
    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    st.subheader("Summary Statistics")
    st.write(df[[column]].describe())

    if column.lower() == 'pm2.5' and df[column].max() > 100:
        st.error("⚠️ Alert: PM2.5 has exceeded 100 at some points in the selected data.")

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

tabs = st.tabs(["Indoor Air Quality", "Outdoor Air Quality"])

with tabs[0]:
    st.header("Indoor Air Quality Dashboard")
    with st.spinner("Loading indoor data and visualizations..."):
        date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(indoor_df, prefix="indoor")
        filtered = apply_filters(indoor_df, date_range, hour_range, cooking_filter, time_col)
        plot_data(filtered, column, time_col, prefix="indoor")

with tabs[1]:
    st.header("Outdoor Air Quality Dashboard")
    with st.spinner("Loading outdoor data and visualizations..."):
        date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(outdoor_df, prefix="outdoor")
        filtered = apply_filters(outdoor_df, date_range, hour_range, cooking_filter, time_col)
        plot_data(filtered, column, time_col, prefix="outdoor")

st.markdown("---")
