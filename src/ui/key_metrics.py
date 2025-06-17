import streamlit as st
import pandas as pd

def calculate_weekly_kpis(users_df, models_df, tools_df):
    """Calculate key weekly metrics and their percentage changes from the previous week."""
    kpis = {}
    
    if users_df.empty:
        return kpis
    
    # Ensure week_start is datetime
    users_df = users_df.copy()
    models_df = models_df.copy() if not models_df.empty else pd.DataFrame()
    tools_df = tools_df.copy() if not tools_df.empty else pd.DataFrame()
    
    for df in [users_df, models_df, tools_df]:
        if not df.empty:
            df['week_start'] = pd.to_datetime(df['week_start'])
    
    # Get the two most recent weeks
    unique_weeks = sorted(users_df['week_start'].unique(), reverse=True)
    if len(unique_weeks) < 2:
        # If we don't have enough data for comparison, return current week metrics without percentage
        current_week = unique_weeks[0] if unique_weeks else None
        if current_week is None:
            return kpis
            
        current_users = users_df[users_df['week_start'] == current_week]
        current_models = models_df[models_df['week_start'] == current_week] if not models_df.empty else pd.DataFrame()
        current_tools = tools_df[tools_df['week_start'] == current_week] if not tools_df.empty else pd.DataFrame()
        
        # Calculate current week metrics (in desired order)
        kpis['total_users'] = {'value': len(current_users), 'change': None}
        kpis['active_users'] = {'value': current_users['is_active'].sum() if 'is_active' in current_users.columns else 0, 'change': None}
        kpis['total_messages'] = {'value': current_users['messages'].sum(), 'change': None}
        kpis['avg_messages_per_user'] = {'value': current_users['messages'].mean() if len(current_users) > 0 else 0, 'change': None}
        
        return kpis
    
    current_week = unique_weeks[0]
    previous_week = unique_weeks[1]
    
    # Filter data for current and previous weeks
    current_users = users_df[users_df['week_start'] == current_week]
    previous_users = users_df[users_df['week_start'] == previous_week]
    
    current_models = models_df[models_df['week_start'] == current_week] if not models_df.empty else pd.DataFrame()
    previous_models = models_df[models_df['week_start'] == previous_week] if not models_df.empty else pd.DataFrame()
    
    current_tools = tools_df[tools_df['week_start'] == current_week] if not tools_df.empty else pd.DataFrame()
    previous_tools = tools_df[tools_df['week_start'] == previous_week] if not tools_df.empty else pd.DataFrame()
    
    def calculate_percentage_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100
    
    # 1. Total Users
    current_total_users = len(current_users)
    previous_total_users = len(previous_users)
    kpis['total_users'] = {
        'value': current_total_users,
        'change': calculate_percentage_change(current_total_users, previous_total_users)
    }
    
    # 2. Active Users (users with is_active = True)
    current_active_users = current_users['is_active'].sum() if 'is_active' in current_users.columns else 0
    previous_active_users = previous_users['is_active'].sum() if 'is_active' in previous_users.columns else 0
    kpis['active_users'] = {
        'value': current_active_users,
        'change': calculate_percentage_change(current_active_users, previous_active_users)
    }
    
    # 3. Total Messages
    current_total_messages = current_users['messages'].sum()
    previous_total_messages = previous_users['messages'].sum()
    kpis['total_messages'] = {
        'value': current_total_messages,
        'change': calculate_percentage_change(current_total_messages, previous_total_messages)
    }
    
    # 4. Average Messages per User
    current_avg_messages = current_users['messages'].mean() if len(current_users) > 0 else 0
    previous_avg_messages = previous_users['messages'].mean() if len(previous_users) > 0 else 0
    kpis['avg_messages_per_user'] = {
        'value': current_avg_messages,
        'change': calculate_percentage_change(current_avg_messages, previous_avg_messages)
    }
    
    return kpis

def display_kpis(kpis):
    """Display KPIs in a clean format without boxes using Streamlit's native metric widget."""
    if not kpis:
        st.info("Not enough data to calculate weekly KPIs. Upload at least two weeks of data.")
        return
    
    # Define KPI display names and formatting (in desired order)
    kpi_config = {
        'total_users': {'name': 'Total Users', 'format': 'int'},
        'active_users': {'name': 'Active Users', 'format': 'int'},
        'total_messages': {'name': 'Total Messages', 'format': 'int'},
        'avg_messages_per_user': {'name': 'Avg Messages/User', 'format': 'float'}
    }
    
    # Create columns for KPIs (4 per row)
    cols_per_row = 4
    kpi_items = list(kpis.items())
    
    for i in range(0, len(kpi_items), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, (key, data) in enumerate(kpi_items[i:i + cols_per_row]):
            if j < len(cols):
                with cols[j]:
                    config = kpi_config.get(key, {'name': key.replace('_', ' ').title(), 'format': 'int'})
                    
                    # Format the value
                    value = data['value']
                    if config['format'] == 'float':
                        formatted_value = f"{value:.1f}"
                    elif value >= 1000000:
                        formatted_value = f"{value/1000000:.1f}M"
                    elif value >= 1000:
                        formatted_value = f"{value/1000:.1f}K"
                    else:
                        formatted_value = f"{int(value)}"
                    
                    # Display using Streamlit's metric widget
                    change = data['change']
                    if change is not None:
                        change_text = f"{change:+.1f}%"
                        st.metric(
                            label=config['name'],
                            value=formatted_value,
                            delta=change_text
                        )
                    else:
                        st.metric(
                            label=config['name'],
                            value=formatted_value
                        )

def show_key_metrics(users_df_view, models_df_view, tools_df_view):
    """Renders the key metrics section with weekly KPIs and percentage changes."""
    
    # Add separator and KPIs section
    st.header("Most Recent Week KPIs")
    
    # Calculate and display KPIs
    kpis = calculate_weekly_kpis(users_df_view, models_df_view, tools_df_view)
    display_kpis(kpis) 
    