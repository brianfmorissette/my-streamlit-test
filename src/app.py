import streamlit as st
import pandas as pd
from core.data import load_master_dataframes
from ui.sidebar import show_sidebar
from ui.main_page import show_main_page

# --- Page Configuration ---
st.set_page_config(
    page_title="PM ChatGPT Enterprise Analytics",
    page_icon="assets/company_logo.png",
    layout="wide"
)

# --- App Title and Description ---
st.title("PM ChatGPT Enterprise Analytics")
st.write(
    "This app creates custom visualizations on the fly. "
    "Enter a request in plain English, and the AI will generate a Plotly chart."
)
st.write("---")

# --- Initialize Session State ---
if 'initialized' not in st.session_state:
    st.toast("Loading master data...")
    users_df, models_df, tools_df = load_master_dataframes()
    
    st.session_state.users_df = users_df
    st.session_state.models_df = models_df
    st.session_state.tools_df = tools_df
    
    st.session_state.initialized = True
    st.toast("Data loaded successfully!", icon="✅")

# --- Load PM Emails ---
try:
    pm_emails_df = pd.read_csv("pm_emails.csv")
    pm_emails = pm_emails_df["email"].tolist()
except FileNotFoundError:
    st.error("pm_emails.csv not found. Please create it in the root directory.")
    pm_emails = []

# --- Render UI and Apply Filters ---
pm_only = show_sidebar()

# Create filtered views of the dataframes based on the sidebar filter.
if pm_only:
    users_df_view = st.session_state.users_df[st.session_state.users_df["email"].isin(pm_emails)]
    models_df_view = st.session_state.models_df[st.session_state.models_df["email"].isin(pm_emails)]
    tools_df_view = st.session_state.tools_df[st.session_state.tools_df["email"].isin(pm_emails)]
else:
    users_df_view = st.session_state.users_df
    models_df_view = st.session_state.models_df
    tools_df_view = st.session_state.tools_df

# Render the main page content
show_main_page(users_df_view, models_df_view, tools_df_view)
