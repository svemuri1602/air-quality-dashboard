# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import gdown
import os
import hashlib

# Set page config with a unique key
st.set_page_config(layout="wide", key="main_page_config")

@st.cache_data
def load_data():
    indoor_id = "1YPNmFBB5xo2QJr05NR0elhLEceXA6XBZ"
    outdoor_id = "1nA15O8JQPNmg0ph2uXkV7E-R4tFQwEqQ"

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

# Generate unique keys based on content
def generate_key(*args):
    return hashlib.md5(str(args).encode()).hexdigest()

indoor_df, outdoor_df = load_data()

def sidebar_filters(df, prefix):
    st.sidebar.markdown("### Filters", key=f"filters_header_{prefix}")
    time_col = 'Datetime' if 'Datetime' in df.columns else 'DateTime'
    date_range = st.sidebar.date_input(
        f"Select Date Range ({prefix})",
        [df[time_col].min().date(), df[time_col].max().date()],
        key=f"date_range_{prefix}"
    )
    hour_range = st.sidebar.slider(
        f"Select Hour Range ({prefix})", 
        0, 23, (0, 23), 
        key=f"hour_range_{prefix}"
    )
    cols = df.select_dtypes(include='number').columns.tolist()
    cols = [c for c in cols if c.lower() != 'entry_id']
    column = st.sidebar.selectbox(
        f"Select Parameter ({prefix})", 
        cols, 
        key=f"parameter_{prefix}"
    )
    cooking_filter = st.sidebar.checkbox(
        f"Show only Cooking Time ({prefix})", 
        value=False, 
        key=f"cooking_{prefix}"
    )
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
        st.warning("No data available for the selected filters.", key=generate_key("warning", prefix))
        return

    # Create unique container for this plot
    with st.container():
        st.subheader("Summary Statistics", key=generate_key("stats_header", prefix))
        st.write(df[[column]].describe(), key=generate_key("stats", prefix))

        if column.lower() == 'pm2.5' and df[column].max() > 100:
            st.error("⚠️ Alert: PM2.5 has exceeded 100 at some points in the selected data.", 
                    key=generate_key("alert", prefix))

        max_points = 1000
        if len(df) > max_points:
            df = df.sample(n=max_points).sort_values(time_col)

        # Use different chart methods with explicit keys
        st.markdown("### Line Chart", key=generate_key("line_header", prefix))
        st.line_chart(
            df.set_index(time_col)[column], 
            use_container_width=True,
            key=generate_key("line_chart", prefix, column)
        )

        st.markdown("### Bar Chart", key=generate_key("bar_header", prefix))
        st.bar_chart(
            df.set_index(time_col)[column],
            use_container_width=True,
            key=generate_key("bar_chart", prefix, column)
        )

        st.markdown("### Correlation Heatmap", key=generate_key("heatmap_header", prefix))
        corr = df.select_dtypes(include='number').corr()
        fig, ax = plt.subplots(num=generate_key("heatmap_fig", prefix))
        sns.heatmap(corr, annot=True, ax=ax)
        st.pyplot(fig, key=generate_key("heatmap", prefix))
        plt.close(fig)

# Main app layout
def main():
    tabs = st.tabs(["Indoor Air Quality", "Outdoor Air Quality"], key="main_tabs")

    with tabs[0]:
        st.header("Indoor Air Quality Dashboard", key="indoor_header")
        with st.spinner("Loading indoor data and visualizations..."):
            date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(
                indoor_df, prefix="indoor"
            )
            filtered = apply_filters(
                indoor_df, date_range, hour_range, cooking_filter, time_col
            )
            plot_data(filtered, column, time_col, prefix="indoor")

    with tabs[1]:
        st.header("Outdoor Air Quality Dashboard", key="outdoor_header")
        with st.spinner("Loading outdoor data and visualizations..."):
            date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(
                outdoor_df, prefix="outdoor"
            )
            filtered = apply_filters(
                outdoor_df, date_range, hour_range, cooking_filter, time_col
            )
            plot_data(filtered, column, time_col, prefix="outdoor")

    st.markdown("---", key="footer_divider")
    st.markdown("Developed with ❤️ using Streamlit", key="footer_text")

if __name__ == "__main__":
    main()
