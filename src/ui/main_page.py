import streamlit as st
import pandas as pd
import plotly.express as px
from core.llm_client import get_visualization_code, GEMINI_API_KEY, OPENAI_API_KEY

def show_main_page(users_df_view, models_df_view, tools_df_view):
    """Renders the main page layout."""
    left_col, right_col = st.columns(2)

    with left_col:
        st.header("Explore the Dataframes")
        tab1, tab2, tab3 = st.tabs(["Users", "Models", "Tools"])
        with tab1:
            st.dataframe(users_df_view)
        with tab2:
            st.dataframe(models_df_view)
        with tab3:
            st.dataframe(tools_df_view)

    with right_col:
        st.header("Plot Agent")

        col1, col2 = st.columns(2)

        dataframes = {"Users": users_df_view, "Models": models_df_view, "Tools": tools_df_view}
        with col1:
            selected_df_name = st.radio(
                "Choose a dataframe to query:",
                options=list(dataframes.keys()),
                horizontal=True,
            )
        df = dataframes[selected_df_name]


        with col2:
            model = st.radio(
                "Choose a model:",
                ("Gemini 1.5 Flash", "ChatGPT 4o"),
                horizontal=True,
                key="model"
            )
            
        placeholder_prompts = {
            "Users": "e.g. 'Average messages per user'",
            "Models": "e.g. 'Stacked bar chart of model usage by week', 'Pie chart of most popular models', 'Trend of o3 usage'", 
            "Tools": "e.g. 'Stacked bar chart of tool usage by week', 'Pie chart of most popular tools', 'Trend of Data Analysis usage'"
        }

        # Store user request in session state to persist it
        if 'user_request' not in st.session_state:
            st.session_state.user_request = ""

        st.session_state.user_request = st.text_area(
            "Enter your visualization request:",
            placeholder=placeholder_prompts.get(selected_df_name),
            height=68,
            value=st.session_state.user_request
        )

        if st.button("Generate Visualization"):
            if not st.session_state.user_request:
                st.warning("Please enter a request for the visualization.")
            
            elif model == "Gemini 1.5 Flash" and not GEMINI_API_KEY:
                st.error("GEMINI_API_KEY not found. Please set it in your .env file.")
            elif model == "ChatGPT 4o" and not OPENAI_API_KEY:
                st.error("OPENAI_API_KEY not found. Please set it in your .env file.")

            else:
                with st.spinner(f"Generating visualization with {model}..."):
                    try:
                        st.session_state.generated_code = get_visualization_code(
                            user_request=st.session_state.user_request,
                            df_for_prompt=df,
                            model=model,
                        )
                        st.session_state.feedback = "" # Clear previous feedback
                    except Exception as e:
                        st.error(str(e))
                        st.session_state.generated_code = None
        
        # This block runs if code has been generated
        if 'generated_code' in st.session_state and st.session_state.generated_code:
            try:
                st.code(st.session_state.generated_code)
                code_to_execute = st.session_state.generated_code.strip().replace("```python", "").replace("```", "")
                local_scope = {"df": df, "px": px, "pd": pd}
                exec(code_to_execute, {}, local_scope)
                fig = local_scope.get("fig")
                if fig:
                    st.plotly_chart(fig)

                    # --- Refinement Section ---
                    st.write("Does this look right? Provide feedback to refine the chart.")
                    feedback = st.text_area(
                        "Your feedback:", 
                        key="feedback_box",
                        placeholder="e.g., 'Change the chart to a bar chart', 'Use a different color scheme'"
                    )

                    if st.button("Regenerate with Feedback"):
                        if not feedback:
                            st.warning("Please enter your feedback before regenerating.")
                        else:
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
                    st.warning("The AI did not generate a chart. Please try a different request.")
            except Exception as e:
                st.error(f"An error occurred while executing the generated code: {e}")
                st.session_state.generated_code = None # Clear broken code 