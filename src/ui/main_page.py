import streamlit as st
import pandas as pd
import plotly.express as px
from core.llm_client import get_visualization_code, GEMINI_API_KEY, OPENAI_API_KEY

def show_main_page(users_df_view, models_df_view, tools_df_view):
    """Renders the main page layout."""
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

        model_provider = st.radio(
            "Choose a model provider:",
            ("Gemini", "OpenAI"),
            horizontal=True,
            key="model_provider"
        )

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
            
            elif model_provider == "Gemini" and not GEMINI_API_KEY:
                st.error("GEMINI_API_KEY not found. Please set it in your .env file.")
            elif model_provider == "OpenAI" and not OPENAI_API_KEY:
                st.error("OPENAI_API_KEY not found. Please set it in your .env file.")

            else:
                with st.spinner(f"Generating visualization with {model_provider}..."):
                    try:
                        generated_code = get_visualization_code(
                            user_request=user_request,
                            df_for_prompt=df,
                            model_provider=model_provider,
                        )

                        if generated_code:
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