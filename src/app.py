import streamlit as st
import pandas as pd
from core.data import load_master_dataframes
from ui.sidebar import show_sidebar
from ui.main_page import show_main_page

# --- Page Configuration ---
st.set_page_config(
    page_title="Flagship Pioneering ChatGPT Usage Analytics",
    page_icon="assets/company_logo.png",
    layout="wide"
)

# --- App Title and Description ---
st.title("Flagship Pioneering ChatGPT Usage Analytics")
st.write(
    "This app creates custom visualizations on the fly. "
    "Enter a request in plain English, and the AI will generate a Plotly chart."
)
st.write("---")

# --- Initialize Session State ---
if 'initialized' not in st.session_state:
    users_df, models_df, tools_df = load_master_dataframes()
    
    st.session_state.users_df = users_df
    st.session_state.models_df = models_df
    st.session_state.tools_df = tools_df
    
    st.session_state.initialized = True

# --- Load PM Emails ---
pm_emails_df = pd.read_csv("pm_emails.csv")
pm_emails = pm_emails_df["email"].tolist()


# --- Render UI and Apply Filters ---
pm_only, start_date, end_date = show_sidebar()

# Create initial filtered views based on the pm_only filter.
if pm_only:
    users_df_view = st.session_state.users_df[st.session_state.users_df["email"].isin(pm_emails)].copy()
    models_df_view = st.session_state.models_df[st.session_state.models_df["email"].isin(pm_emails)].copy()
    tools_df_view = st.session_state.tools_df[st.session_state.tools_df["email"].isin(pm_emails)].copy()
else:
    users_df_view = st.session_state.users_df.copy()
    models_df_view = st.session_state.models_df.copy()
    tools_df_view = st.session_state.tools_df.copy()

# Apply the date range filter if it's available
if start_date and end_date:
    for df_view in [users_df_view, models_df_view, tools_df_view]:
        if not df_view.empty:
            df_view['week_start'] = pd.to_datetime(df_view['week_start']).dt.date
            df_view.query("@start_date <= week_start <= @end_date", inplace=True)

# Sort all dataframes by date in descending order before displaying
users_df_view = users_df_view.sort_values(by='week_start', ascending=False).reset_index(drop=True)
models_df_view = models_df_view.sort_values(by='week_start', ascending=False).reset_index(drop=True)
tools_df_view = tools_df_view.sort_values(by='week_start', ascending=False).reset_index(drop=True)
# Render the main page content
show_main_page(users_df_view, models_df_view, tools_df_view)
