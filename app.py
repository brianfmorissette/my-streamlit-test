#    pip install streamlit pandas plotly google-generativeai
# 2. Save this code as a Python file (e.g., `app.py`).
# 3. Run it from your terminal:
#    streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

from data import load_master_dataframes, save_master_dataframes, process_uploaded_file
from gemini_client import get_visualization_code

load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="PM ChatGPT Enterprise Analytics",
    page_icon="company_logo.png",
    layout="centered"
)

# --- App Title and Description ---
st.title("PM ChatGPT Enterprise Analytics")
st.write(
    "This app uses the Gemini API to create custom visualizations on the fly. "
    "Enter a request in plain English, and the AI will generate a Plotly chart."
)
st.write("---")

# --- Load Data ---

# Load existing master dataframes
users_df, models_df, tools_df = load_master_dataframes()

# Load PM emails from CSV
try:
    pm_emails_df = pd.read_csv("pm_emails.csv")
    pm_emails = pm_emails_df["email"].tolist()
except FileNotFoundError:
    st.error("pm_emails.csv not found. Please create it in the root directory.")
    pm_emails = []

# Sidebar for file upload
st.sidebar.header("Upload New Weekly Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        new_users, new_models, new_tools = process_uploaded_file(df, uploaded_file.name)
        # Append new data to master dataframes``
        users_df = pd.concat([users_df, new_users], ignore_index=True)
        models_df = pd.concat([models_df, new_models], ignore_index=True)
        tools_df = pd.concat([tools_df, new_tools], ignore_index=True)
        # Save updated masters
        save_master_dataframes(users_df, models_df, tools_df)
        st.success("File processed and data added to master dataframes!")
    except Exception as e:
        st.error(f"Error processing file: {e}")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
pm_only = st.sidebar.checkbox("Show PM only")

# Create views of the dataframes based on the filter
if pm_only:
    users_df_view = users_df[users_df["email"].isin(pm_emails)]
    models_df_view = models_df[models_df["email"].isin(pm_emails)]
    tools_df_view = tools_df[tools_df["email"].isin(pm_emails)]
else:
    users_df_view = users_df
    models_df_view = models_df
    tools_df_view = tools_df

# --- Gemini API Configuration ---
gemini_api_key = os.getenv("GEMINI_API_KEY")

# --- Main App ---
st.markdown("### Explore the dataframes")
tab1, tab2, tab3 = st.tabs(["Users", "Models", "Tools"])
with tab1:
    st.dataframe(users_df_view)
with tab2:
    st.dataframe(models_df_view)
with tab3:
    st.dataframe(tools_df_view)
st.write("---")


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

