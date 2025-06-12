#    pip install streamlit pandas plotly google-generativeai
# 2. Save this code as a Python file (e.g., `app.py`).
# 3. Run it from your terminal:
#    streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import io
import os
from dotenv import load_dotenv
load_dotenv()


# --- Page Configuration ---
st.set_page_config(
    page_title="PM ChatGPT Enterprise Analytics",
    page_icon="🤖",
    layout="centered"
)

# --- App Title and Description ---
st.title("🤖 PM ChatGPT Enterprise Analytics")
st.write(
    "This app (hello) (goodbye) uses the Gemini API to create visualizations on the fly. "
    "Enter a request in plain English, and the AI will generate a Plotly chart."
)
st.write("---")


# --- Hardcoded Dummy DataFrame ---
# In your final app, this will be replaced by your merged CSV data.
@st.cache_data
def get_dummy_data():
    """Creates a sample DataFrame for demonstration."""
    data = {
        'Date': pd.to_datetime([
            '2025-04-15', '2025-04-16', '2025-04-17', '2025-04-18', '2025-04-19',
            '2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04', '2025-05-05'
        ]),
        'UserName': [
            'Alice', 'Bob', 'Charlie', 'Alice', 'David',
            'Bob', 'Eve', 'Alice', 'Charlie', 'David'
        ],
        'TotalMessages': [25, 15, 30, 22, 18, 20, 35, 28, 12, 19],
        'GPT4_Messages': [15, 5, 20, 12, 8, 10, 25, 18, 2, 9],
        'GPT3.5_Messages': [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        'Department': [
            'Engineering', 'Sales', 'Engineering', 'Engineering', 'Marketing',
            'Sales', 'Marketing', 'Engineering', 'Engineering', 'Marketing'
        ]
    }
    df = pd.DataFrame(data)
    # Add a 'Month' column for easier time-based analysis
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    return df

df = get_dummy_data()


# --- Gemini API Configuration ---
gemini_api_key = os.getenv("GEMINI_API_KEY")



# --- AI Agent Logic ---
def get_visualization_code(user_request, df_for_prompt):
    """
    Calls the Gemini API to generate Python code for a visualization.
    """

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-001')
    except Exception as e:
        st.error(f"Error configuring the API. Please check your key. Details: {e}")
        return None

    # Capture DataFrame info and head for the prompt
    with io.StringIO() as buffer:
        df_for_prompt.info(buf=buffer)
        df_schema = buffer.getvalue()
    
    df_head = df_for_prompt.head().to_string()

    # Construct the detailed prompt
    prompt = f"""
    You are an expert Python data visualization assistant.
    You are working with a pandas DataFrame in memory named `df`.

    Here is the schema of the DataFrame:
    ```
    {df_schema}
    ```

    Here is the head of the DataFrame:
    ```
    {df_head}
    ```

    The user has requested the following visualization:
    "{user_request}"

    Your task is to generate ONLY the Python code (using Plotly Express) to create the requested visualization.
    Your response must be a raw string of Python code, without any markdown, code fences (```), or explanations.
    - The code should be a single block.
    - The DataFrame is already in memory as `df`. Do not load any data.
    - The final chart object should be named `fig`.
    - `plotly.express` is already imported as `px`. Do not import it again.
    - Do not include `st.plotly_chart(fig)`. The app will handle rendering.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while calling the Gemini API: {e}")
        return None


# --- Main Application UI ---
st.subheader("Explore the Data")
st.write("Here is the sample DataFrame we're working with:")
st.dataframe(df, use_container_width=True)
st.write("---")

st.subheader("Create a Custom Visualization")
user_prompt = st.text_input(
    "Enter your visualization request:",
    placeholder="e.g., 'Bar chart of total messages by user name'"
)

if st.button("Generate Visualization", type="primary"):
    if user_prompt:
        with st.spinner("🤖 The AI is thinking..."):
            # Step 1: Get the code from the LLM
            llm_response_code = get_visualization_code(user_prompt, df)

            if llm_response_code:
                st.write("✅ AI Generated the following code:")
                st.code(llm_response_code, language="python")

                # Step 2: Execute the code and display the chart
                try:
                    # Clean the generated code to remove markdown formatting
                    code_to_execute = llm_response_code.strip()
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
    else:
        st.warning("Please enter a request for the visualization.")

# --- Footer ---
st.sidebar.markdown("---")