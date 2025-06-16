import streamlit as st
import pandas as pd
from datetime import datetime
from core.data import save_master_dataframes, process_uploaded_file

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

def show_sidebar():
    """Renders the sidebar components and returns the state of the pm_only filter."""
    st.sidebar.header("Upload New Weekly Data")
    st.sidebar.file_uploader(
        "Upload CSV file", 
        type=['csv'], 
        key="file_uploader_widget",
        on_change=handle_file_upload
    )

    with st.sidebar.expander("Processed Report Dates", expanded=True):
        if not st.session_state.users_df.empty:
            processed_dates = pd.to_datetime(st.session_state.users_df['week_start']).dt.date.unique()
            processed_dates = sorted(processed_dates, reverse=True)
            
            for date in processed_dates:
                st.write(date.strftime('%Y-%m-%d'))
        else:
            st.write("No reports have been uploaded yet.")

    st.sidebar.header("Filters")
    pm_only = st.sidebar.checkbox("Show PM only")
    return pm_only 