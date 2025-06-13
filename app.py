import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from dotenv import load_dotenv

from data import load_master_dataframes, save_master_dataframes, process_uploaded_file
from gemini_client import get_visualization_code

load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="PM ChatGPT Enterprise Analytics",
    page_icon="company_logo.png", # Make sure you have this image or remove this line
    layout="wide"
)

# --- Callback Function for File Upload ---
def handle_file_upload():
    """
    This function is called when a new file is uploaded.
    It handles processing, duplicate checking, and updating the master data.
    """
    uploaded_file = st.session_state.get("file_uploader_widget")
    if uploaded_file is None:
        return

    try:
        # --- PERMANENT DUPLICATE CHECK ---
        # Extract the date from the filename to check against existing master data.
        report_date_str = uploaded_file.name.split(' ')[-1].replace('.csv', '')
        report_date = pd.to_datetime(datetime.strptime(report_date_str, '%Y-%m-%d'))

        # Check if this date already exists in our master users dataframe
        if not st.session_state.users_df.empty and report_date in pd.to_datetime(st.session_state.users_df['week_start']).values:
            st.sidebar.warning(f"A report for the date {report_date.date()} has already been uploaded.")
        else:
            # If it's a new date, process the file
            st.sidebar.info(f"Processing '{uploaded_file.name}'...")
            df = pd.read_csv(uploaded_file)
            new_users, new_models, new_tools = process_uploaded_file(df, uploaded_file.name)
            
            # Append new data TO THE DATAFRAMES IN SESSION STATE
            st.session_state.users_df = pd.concat([st.session_state.users_df, new_users], ignore_index=True)
            st.session_state.models_df = pd.concat([st.session_state.models_df, new_models], ignore_index=True)
            st.session_state.tools_df = pd.concat([st.session_state.tools_df, new_tools], ignore_index=True)
            
            # Save the UPDATED master dataframes for persistence
            save_master_dataframes(
                st.session_state.users_df, 
                st.session_state.models_df, 
                st.session_state.tools_df
            )
            st.sidebar.success("File processed and master data updated!")

    except Exception as e:
        st.sidebar.error(f"Error processing file: {e}")


# --- App Title and Description ---
st.title("PM ChatGPT Enterprise Analytics")
st.write(
    "This app uses the Gemini API to create custom visualizations on the fly. "
    "Enter a request in plain English, and the AI will generate a Plotly chart."
)
st.write("---")

# --- Initialize Session State ---
# This block runs ONLY ONCE per user session.
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


# --- Sidebar ---
st.sidebar.header("Upload New Weekly Data")
st.sidebar.file_uploader(
    "Upload CSV file", 
    type=['csv'], 
    key="file_uploader_widget", # Use a key to access the widget's value in the callback
    on_change=handle_file_upload # Set the callback function
)

# --- NEW: Show Processed Dates in Sidebar ---
with st.sidebar.expander("Processed Report Dates", expanded=True):
    if not st.session_state.users_df.empty:
        # Get unique dates, sort them with the newest first
        processed_dates = pd.to_datetime(st.session_state.users_df['week_start']).dt.date.unique()
        processed_dates = sorted(processed_dates, reverse=True)
        
        for date in processed_dates:
            st.write(date.strftime('%Y-%m-%d'))
    else:
        st.write("No reports have been uploaded yet.")


st.sidebar.header("Filters")
pm_only = st.sidebar.checkbox("Show PM only")


# --- Main Logic ---

# Create filtered views of the dataframes. This now runs after the callback has updated the state.
if pm_only:
    users_df_view = st.session_state.users_df[st.session_state.users_df["email"].isin(pm_emails)]
    models_df_view = st.session_state.models_df[st.session_state.models_df["email"].isin(pm_emails)]
    tools_df_view = st.session_state.tools_df[st.session_state.tools_df["email"].isin(pm_emails)]
else:
    users_df_view = st.session_state.users_df
    models_df_view = st.session_state.models_df
    tools_df_view = st.session_state.tools_df

# Gemini API Configuration
gemini_api_key = os.getenv("GEMINI_API_KEY")



# Main App Layout
left_col, right_col = st.columns(2)

with left_col:
    st.header("Explore the dataframes")
    tab1, tab2, tab3 = st.tabs(["Users", "Models", "Tools"])
    with tab1:
        st.dataframe(users_df_view)
    with tab2:
        st.dataframe(models_df_view)
    with tab3:
        st.dataframe(tools_df_view)
    st.write("---")

with right_col:
    st.header("Create a Custom Visualization")
    dataframes = {"Users": users_df_view, "Models": models_df_view, "Tools": tools_df_view}
    selected_df_name = st.radio(
        "Choose a dataframe to query:",
        options=list(dataframes.keys()),
        horizontal=True,
    )
    df = dataframes[selected_df_name]

    user_request = st.text_area(
        "Enter your visualization request:",
        "Bar chart of total messages per user"
    )

    if st.button("Generate Visualization"):
        if not user_request:
            st.warning("Please enter a request for the visualization.")
        elif not gemini_api_key:
            st.error("GEMINI_API_KEY not found. Please set it in your .env file.")
        else:
            with st.spinner("Generating visualization..."):
                try:
                    generated_code = get_visualization_code(
                        user_request=user_request,
                        df_for_prompt=df,
                        api_key=gemini_api_key
                    )

                    if generated_code:
                        st.success("✅ AI Generated the following code:")
                        st.code(generated_code, language="python")
                        try:
                            code_to_execute = generated_code.strip().replace("```python", "").replace("```", "")
                            local_scope = {"df": df, "px": px, "pd": pd}
                            exec(code_to_execute, {}, local_scope)
                            fig = local_scope.get("fig")
                            if fig:
                                st.plotly_chart(fig)
                            else:
                                st.warning("The AI did not generate a chart. Please try a different request.")
                        except Exception as e:
                            st.error(f"An error occurred while executing the generated code: {e}")
                except Exception as e:
                    st.error(str(e))
