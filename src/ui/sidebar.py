import streamlit as st
import pandas as pd
from datetime import datetime
from core.data import save_master_dataframes, process_uploaded_file

def handle_date_deletion(date_to_delete):
    """
    Deletes all data entries for a specific date from the master dataframes.
    """
    try:
        # Convert the date to a datetime object to ensure correct filtering
        date_to_delete = pd.to_datetime(date_to_delete)

        # Filter out the data for the given date
        st.session_state.users_df = st.session_state.users_df[pd.to_datetime(st.session_state.users_df['week_start']) != date_to_delete]
        st.session_state.models_df = st.session_state.models_df[pd.to_datetime(st.session_state.models_df['week_start']) != date_to_delete]
        st.session_state.tools_df = st.session_state.tools_df[pd.to_datetime(st.session_state.tools_df['week_start']) != date_to_delete]

        # Save the updated dataframes
        save_master_dataframes(
            st.session_state.users_df,
            st.session_state.models_df,
            st.session_state.tools_df
        )
        st.toast(f"Successfully deleted all data for {date_to_delete.date()}.", icon="✅")
        st.rerun()  # Rerun the app to reflect the changes immediately
        
    except Exception as e:
        st.sidebar.error(f"Error deleting data: {e}")

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
    """Renders the sidebar components and returns the filter states."""
    st.sidebar.header("Filters")

    # --- PM Filter ---
    st.sidebar.subheader("User Type")
    pm_only = st.sidebar.checkbox("Show PM only")
    
    # --- Time Filter ---
    start_date, end_date = None, None
    if not st.session_state.users_df.empty:
        st.sidebar.subheader("Date Range")
        min_date = pd.to_datetime(st.session_state.users_df['week_start']).dt.date.min()
        max_date = pd.to_datetime(st.session_state.users_df['week_start']).dt.date.max()

        start_date = st.sidebar.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

    st.sidebar.divider()

    st.sidebar.header("Upload Weekly Data")
    st.sidebar.file_uploader(
        "Upload CSV file", 
        type=['csv'], 
        key="file_uploader_widget",
        on_change=handle_file_upload
    )

    with st.sidebar.expander("Processed Report Dates", expanded=False):
        if not st.session_state.users_df.empty:
            processed_dates = pd.to_datetime(st.session_state.users_df['week_start']).dt.date.unique()
            processed_dates = sorted(processed_dates, reverse=True)
            
            for date in processed_dates:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(date.strftime('%Y-%m-%d'))
                with col2:
                    if st.button("🗑️", key=f"delete_{date}"):
                        handle_date_deletion(date)
        else:
            st.write("No reports have been uploaded yet.")

    
    

    
    
    return pm_only, start_date, end_date 