import streamlit as st
import pandas as pd
import plotly.express as px
from core.llm_client import get_visualization_code, GEMINI_API_KEY, OPENAI_API_KEY

def show_plot_agent(users_df_view, models_df_view, tools_df_view):
    """Renders the AI plotting agent interface."""
    
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