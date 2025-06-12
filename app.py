#    pip install streamlit pandas plotly google-generativeai
# 2. Save this code as a Python file (e.g., `app.py`).
# 3. Run it from your terminal:
#    streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

from data import get_dummy_data
from gemini_client import get_visualization_code

load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Visualization Assistant",
    page_icon="🤖",
    layout="centered"
)

# --- App Title and Description ---
st.title("🤖 PM ChatGPT Enterprise Analytics")
st.write(
    "This app uses the Gemini API to create visualizations on the fly. "
    "Enter a request in plain English, and the AI will generate a Plotly chart."
)
st.write("---")

# --- Load Data ---
df = get_dummy_data()

# --- Gemini API Configuration ---
gemini_api_key = os.getenv("GEMINI_API_KEY")

# --- Main App ---
st.markdown("### Here is the sample DataFrame we're working with:")
st.dataframe(df)
st.write("---")

st.header("Create a Custom Visualization")
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
        with st.spinner("🤖 AI is thinking..."):
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
                        # Clean the generated code to remove markdown formatting
                        code_to_execute = generated_code.strip()
                        if code_to_execute.startswith("```python"):
                            code_to_execute = code_to_execute[len("```python"):].strip()
                        if code_to_execute.endswith("```"):
                            code_to_execute = code_to_execute[:-len("```")].strip()

                        # Execute the generated code in a controlled scope
                        local_scope = {"df": df, "px": px, "pd": pd}
                        exec(code_to_execute, {}, local_scope)
                        fig = local_scope.get("fig")

                        # Display the chart if one was created
                        if fig:
                            st.plotly_chart(fig)
                        else:
                            st.warning("The AI did not generate a chart. Please try a different request.")

                    except Exception as e:
                        st.error(f"An error occurred while executing the generated code: {e}")

            except (ValueError, RuntimeError) as e:
                st.error(str(e))

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.info(
    "This is a demo application. The data is randomly generated and not real."
)