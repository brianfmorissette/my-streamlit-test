import streamlit as st
import pandas as pd
import plotly.express as px
from core.llm_client import get_visualization_code, GEMINI_API_KEY, OPENAI_API_KEY

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
    """Display KPIs in a card-like format with arrows and percentage changes."""
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
                    
                    # Create the KPI card
                    change = data['change']
                    if change is not None:
                        if change > 0:
                            arrow = "↗"
                            color = "green"
                            change_text = f"+{change:.1f}%"
                        elif change < 0:
                            arrow = "↘"
                            color = "red"
                            change_text = f"{change:.1f}%"
                        else:
                            arrow = "→"
                            color = "gray"
                            change_text = "0.0%"
                        
                        # Display the KPI with styling
                        st.markdown(f"""
                        <div style="
                            background-color: white;
                            padding: 20px;
                            border-radius: 10px;
                            border: 1px solid #e0e0e0;
                            text-align: left;
                        ">
                            <div style="color: #666; font-size: 14px; margin-bottom: 5px;">
                                {config['name']}
                            </div>
                            <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">
                                {formatted_value}
                            </div>
                            <div style="color: {color}; font-size: 14px;">
                                <span style="font-size: 16px;">{arrow}</span> {change_text}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Display KPI without percentage change
                        st.markdown(f"""
                        <div style="
                            background-color: white;
                            padding: 20px;
                            border-radius: 10px;
                            border: 1px solid #e0e0e0;
                            text-align: left;
                        ">
                            <div style="color: #666; font-size: 14px; margin-bottom: 5px;">
                                {config['name']}
                            </div>
                            <div style="font-size: 32px; font-weight: bold; margin-bottom: 5px;">
                                {formatted_value}
                            </div>
                            <div style="color: #999; font-size: 14px;">
                                n/a
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

def show_main_page(users_df_view, models_df_view, tools_df_view):
    """Renders the main page layout with dataframe exploration and AI plotting agent."""
    
    # Create two-column layout: left for data exploration, right for plotting agent
    left_col, right_col = st.columns(2)

    # Left column: Display dataframes in tabs
    with left_col:
        st.header("Explore the Dataframes")
        tab1, tab2, tab3 = st.tabs(["Users", "Models", "Tools"])
        
        # Display each dataframe in its respective tab
        with tab1:
            st.dataframe(users_df_view)
        with tab2:
            st.dataframe(models_df_view)
        with tab3:
            st.dataframe(tools_df_view)

    # Right column: AI plotting agent interface
    with right_col:
        st.header("Plot Agent")

        # Create sub-columns for dataframe selection and model selection
        col1, col2 = st.columns(2)

        # Store dataframes in a dictionary for easy access
        dataframes = {"Users": users_df_view, "Models": models_df_view, "Tools": tools_df_view}
        
        # Column 1: Dataframe selection
        with col1:
            selected_df_name = st.radio(
                "Choose a dataframe to query:",
                options=list(dataframes.keys()),
                horizontal=True,
            )
        # Get the selected dataframe
        df = dataframes[selected_df_name]

        # Column 2: Model selection
        with col2:
            model = st.radio(
                "Choose a model:",
                ("Gemini 1.5 Flash", "ChatGPT 4o"),
                horizontal=True,
                key="model"
            )
        
        # Define example prompts for each dataframe to guide users
        placeholder_prompts = {
            "Users": "e.g. 'Top 10 most active users', 'GPTs Messaged Usage', 'Users who have created a project",
            "Models": "e.g. 'Stacked bar chart of model usage by week', 'Pie chart of most popular models', 'Trend of o3 usage'", 
            "Tools": "e.g. 'Stacked bar chart of tool usage by week', 'Pie chart of most popular tools', 'Trend of Data Analysis usage'"
        }

        # Initialize user request in session state if not exists
        # Store user request in session state to persist it across interactions
        if 'user_request' not in st.session_state:
            st.session_state.user_request = ""

        # Text area for user's visualization request
        st.session_state.user_request = st.text_area(
            "Enter your visualization request:",
            placeholder=placeholder_prompts.get(selected_df_name),
            height=100,
            value=st.session_state.user_request
        )

        # Create buttons for generating visualization and clearing session
        col_gen, col_clear = st.columns([3, 1])

        # Generate Visualization button
        with col_gen:
            if st.button("Generate Visualization", use_container_width=True):
                # Validate user input
                if not st.session_state.user_request or st.session_state.user_request == placeholder_prompts.get(selected_df_name, ""):
                    st.warning("Please enter a request for the visualization.")
                
                # Check if required API keys are available
                elif model == "Gemini 1.5 Flash" and not GEMINI_API_KEY:
                    st.error("GEMINI_API_KEY not found. Please set it in your .env file.")
                elif model == "ChatGPT 4o" and not OPENAI_API_KEY:
                    st.error("OPENAI_API_KEY not found. Please set it in your .env file.")

                # Generate visualization if all checks pass
                else:
                    with st.spinner(f"Generating visualization with {model}..."):
                        try:
                            # Call LLM to generate visualization code
                            st.session_state.generated_code = get_visualization_code(
                                user_request=st.session_state.user_request,
                                df_for_prompt=df,
                                model=model,
                            )
                            st.session_state.feedback = "" # Clear previous feedback
                        except Exception as e:
                            st.error(str(e))
                            st.session_state.generated_code = None

        # Clear session button
        with col_clear:
            if st.button("Clear", use_container_width=True):
                # Clear all session state variables related to plotting agent
                keys_to_clear = ['generated_code', 'feedback', 'user_request', 'last_selected_df', 'show_code']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()  # Refresh the page to reflect changes

        # Display generated visualization and provide refinement options
        # This block runs if code has been generated successfully
        if 'generated_code' in st.session_state and st.session_state.generated_code:
            try:
                # Toggle button for showing/hiding the generated code
                if st.button("Show/Hide Generated Code"):
                    st.session_state.show_code = not st.session_state.get('show_code', False)
                
                # Display code if user has toggled it on
                if st.session_state.get('show_code', False):
                    st.code(st.session_state.generated_code, language='python')
                
                # Execute the generated code to create the visualization
                # Clean up any markdown formatting that might be present
                code_to_execute = st.session_state.generated_code.strip().replace("```python", "").replace("```", "")
                
                # Set up execution environment with required variables
                local_scope = {"df": df, "px": px, "pd": pd}
                
                # Execute the generated code
                exec(code_to_execute, {}, local_scope)
                
                # Extract the figure object from the executed code
                fig = local_scope.get("fig")
                
                if fig:
                    # Display the generated plot
                    st.plotly_chart(fig)

                    # Refinement section: Allow users to provide feedback
                    st.write("Provide feedback to refine the chart.")
                    feedback = st.text_area(
                        "Your feedback:", 
                        key="feedback_box",
                        placeholder="e.g., 'Change the chart to a bar chart', 'Use a different color scheme', 'Use names instead of emails'"
                    )

                    # Regenerate button with feedback
                    if st.button("Regenerate with Feedback"):
                        if not feedback:
                            st.warning("Please enter your feedback before regenerating.")
                        else:
                            # Generate refined visualization based on feedback
                            with st.spinner(f"Regenerating visualization with {model}..."):
                                try:
                                    st.session_state.generated_code = get_visualization_code(
                                        user_request=st.session_state.user_request,
                                        df_for_prompt=df,
                                        model=model,
                                        previous_code=st.session_state.generated_code,
                                        feedback=feedback
                                    )
                                    st.rerun() # Rerun to display the new chart
                                except Exception as e:
                                    st.error(str(e))

                else:
                    # Handle case where no figure was generated
                    st.warning("The AI did not generate a chart. Please try a different request.")
                    
            except Exception as e:
                # Handle any errors during code execution
                st.error(f"An error occurred while executing the generated code: {e}")
                st.session_state.generated_code = None # Clear broken code to prevent repeated errors 

    # Add separator and KPIs section below the two columns
    st.markdown("---")
    st.header("Key Metrics - Past Week")
    
    # Calculate and display KPIs
    kpis = calculate_weekly_kpis(users_df_view, models_df_view, tools_df_view)
    display_kpis(kpis) 