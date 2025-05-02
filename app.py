
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")

# Load data from Google Drive
@st.cache_data
def load_data():
    indoor_url = "https://drive.google.com/uc?export=download&id=1YPNmFBB5xo2QJr05NR0elhLEceXA6XBZ"
    outdoor_url = "https://drive.google.com/uc?export=download&id=1nA15O8JQPNmg0ph2uXkV7E-R4tFQwEqQ"

    indoor = pd.read_csv(indoor_url)
    outdoor = pd.read_csv(outdoor_url)

    # Clean column names and convert datetime
    indoor.columns = indoor.columns.str.strip()
    outdoor.columns = outdoor.columns.str.strip()

    indoor['Datetime'] = pd.to_datetime(indoor['Datetime'], errors='coerce')
    outdoor['DateTime'] = pd.to_datetime(outdoor['DateTime'], errors='coerce')

    return indoor, outdoor

indoor_df, outdoor_df = load_data()

# Sidebar for filters
def sidebar_filters(df):
    st.sidebar.markdown("### Filters")
    time_col = 'Datetime' if 'Datetime' in df.columns else 'DateTime'
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [df[time_col].min().date(), df[time_col].max().date()]
    )
    hour_range = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
    column = st.sidebar.selectbox("Select Parameter", df.select_dtypes(include='number').columns)
    cooking_filter = st.sidebar.checkbox("Show only Cooking Time", value=False)
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
    date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(indoor_df)
    filtered = apply_filters(indoor_df, date_range, hour_range, cooking_filter, time_col)
    plot_data(filtered, column, time_col)

with tabs[1]:
    st.header("Outdoor Air Quality Dashboard")
    date_range, hour_range, column, cooking_filter, time_col = sidebar_filters(outdoor_df)
    filtered = apply_filters(outdoor_df, date_range, hour_range, cooking_filter, time_col)
    plot_data(filtered, column, time_col)

st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit")

