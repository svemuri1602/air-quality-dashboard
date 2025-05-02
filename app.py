# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os
from datetime import datetime

# Initialize session state
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Indoor"

# Set page config
st.set_page_config(layout="wide", page_title="Air Quality Dashboard")

@st.cache_data
def load_data():
    indoor_id = "1YPNmFBB5xo2QJr05NR0elhLEceXA6XBZ"
    outdoor_id = "1nA15O8JQPNmg0ph2uXkV7E-R4tFQwEqQ"

    if not os.path.exists("indoor.csv"):
        gdown.download(f"https://drive.google.com/uc?id={indoor_id}", "indoor.csv", quiet=False)
    if not os.path.exists("outdoor.csv"):
        gdown.download(f"https://drive.google.com/uc?id={outdoor_id}", "outdoor.csv", quiet=False)

    indoor = pd.read_csv("indoor.csv")
    outdoor = pd.read_csv("outdoor.csv")

    # Data cleaning
    indoor.columns = indoor.columns.str.strip()
    outdoor.columns = outdoor.columns.str.strip()
    indoor['Datetime'] = pd.to_datetime(indoor['Datetime'], errors='coerce')
    outdoor['DateTime'] = pd.to_datetime(outdoor['DateTime'], errors='coerce')

    return indoor, outdoor

def create_sidebar_filters(df, prefix):
    st.sidebar.markdown(f"### {prefix} Filters")
    time_col = 'Datetime' if 'Datetime' in df.columns else 'DateTime'

    min_date = df[time_col].min().date()
    max_date = df[time_col].max().date()

    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        key=f"{prefix}_date_range"
    )

    hour_range = st.sidebar.slider(
        "Select Hour Range",
        0, 23, (0, 23),
        key=f"{prefix}_hour_range"
    )

    numeric_cols = [col for col in df.select_dtypes(include='number').columns 
                   if col.lower() != 'entry_id']
    column = st.sidebar.selectbox(
        "Select Parameter",
        numeric_cols,
        key=f"{prefix}_parameter"
    )

    cooking_filter = False
    if 'Cooking' in df.columns:
        cooking_filter = st.sidebar.checkbox(
            "Show only Cooking Time",
            value=False,
            key=f"{prefix}_cooking_filter"
        )

    return date_range, hour_range, column, cooking_filter, time_col

def filter_data(df, date_range, hour_range, cooking_filter, time_col):
    filtered = df[
        (df[time_col].dt.date >= date_range[0]) &
        (df[time_col].dt.date <= date_range[1]) &
        (df[time_col].dt.hour >= hour_range[0]) &
        (df[time_col].dt.hour <= hour_range[1])
    ]

    if cooking_filter:
        filtered = filtered[filtered['Cooking'] == 1]

    return filtered

def create_visualizations(df, column, time_col, prefix):
    if df.empty:
        st.warning("No data available for the selected filters.")
        return

    # CSV Download Button (Fixing duplicate key error)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{prefix}_filtered_data.csv",
        mime="text/csv",
        key=f"download_button_{prefix}"
    )

    # Summary statistics
    with st.expander("Summary Statistics"):
        st.dataframe(df[column].describe())

    # Alert for high PM2.5
    if column.lower() == 'pm2.5' and df[column].max() > 100:
        st.error("⚠️ High PM2.5 Alert: Levels exceeded 100")

    # Line chart
    st.subheader("Time Series")
    fig = px.line(
        df, 
        x=time_col, 
        y=column,
        title=f"{column} over Time"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Correlation heatmap (simplified)
    st.subheader("Correlation Matrix")
    numeric_df = df.select_dtypes(include='number')
    if len(numeric_df.columns) > 1:
        corr = numeric_df.corr()
        fig = px.imshow(
            corr,
            text_auto=True,
            title="Feature Correlations"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough numeric columns for correlation matrix")

def main():
    st.title("Air Quality Dashboard")

    # Load data
    indoor_df, outdoor_df = load_data()

    # Tab selection
    tab = st.radio(
        "Select Dashboard:",
        ["Indoor", "Outdoor"],
        horizontal=True,
        key="tab_selector"
    )

    st.session_state.current_tab = tab

    if tab == "Indoor":
        st.header("Indoor Air Quality")
        date_range, hour_range, column, cooking_filter, time_col = create_sidebar_filters(
            indoor_df, "indoor"
        )
        filtered = filter_data(
            indoor_df, date_range, hour_range, cooking_filter, time_col
        )
        create_visualizations(filtered, column, time_col, "indoor")
    else:
        st.header("Outdoor Air Quality")
        date_range, hour_range, column, cooking_filter, time_col = create_sidebar_filters(
            outdoor_df, "outdoor"
        )
        filtered = filter_data(
            outdoor_df, date_range, hour_range, cooking_filter, time_col
        )
        create_visualizations(filtered, column, time_col, "outdoor")

    st.markdown("---")
    st.markdown("Developed with Streamlit")

if __name__ == "__main__":
    main()

