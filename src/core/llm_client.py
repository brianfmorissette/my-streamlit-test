import google.generativeai as genai
import openai
import io
import os
from dotenv import load_dotenv

load_dotenv()

# Load API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_visualization_code(
    user_request, 
    df_for_prompt, 
    model,
    previous_code=None,
    feedback=None
):
    """
    Calls the selected LLM API to generate Python code for a visualization.
    If previous_code and feedback are provided, it asks the model to refine the code.
    """
    # --- Prompt Definition (shared by both models) ---
    with io.StringIO() as buffer:
        df_for_prompt.info(buf=buffer)
        df_schema = buffer.getvalue()
    df_head = df_for_prompt.head().to_string()
    df_tail = df_for_prompt.tail().to_string()
    df_columns = df_for_prompt.columns.tolist()

    if previous_code and feedback:
        # This is a refinement request
        prompt = f"""
        You are an expert and meticulous Python data analyst specializing in Plotly Express.
        A user wants to refine a visualization you previously created.

        The DataFrame `df` has this schema and head:
        Schema:
        ```
        {df_schema}
        ```
        Head:
        ```
        {df_head}
        ```
        Tail:
        ```
        {df_tail}
        ```

        Here is the original user request:
        "{user_request}"

        Here is the Python code you previously generated:
        ```python
        {previous_code}
        ```

        The user has provided the following feedback for how to change the chart:
        "{feedback}"

        Your task is to generate ONLY the updated Python code that incorporates the user's feedback.
        Your response must be a raw string of Python code, without any markdown, code fences (```), or explanations.
        
        CRITICAL REQUIREMENTS TO PREVENT ERRORS:
        - The DataFrame is already in memory as `df`. Do not load any data.
        - `pandas` is imported as `pd`.
        - The final chart object must be assigned to a variable named `fig`.
        - `plotly.express` is already imported as `px`. Do not import it again.
        - Do not include `st.plotly_chart(fig)`. The app will handle rendering.
        - **ONLY use columns that exist in the DataFrame schema above. Available columns are: {df_columns}**
        - **Handle missing data: Use df.dropna() or df.fillna() as appropriate**
        - **For aggregations, use pandas groupby/agg methods before plotting**
        - **Only use valid Plotly Express function parameters. Common valid parameters include: x, y, color, size, hover_data, title, labels**
        - **For date columns, ensure proper datetime conversion: pd.to_datetime(df['col'], errors='coerce')**
        - **Always include error handling for data operations**
        - **If the request cannot be fulfilled with available data, create a simple fallback visualization**
        """
    else:
        # This is an initial request
        prompt = f"""
        You are an expert and meticulous Python data analyst specializing in Plotly Express.
        Your goal is to generate clean, readable, and ERROR-FREE Python code for visualizations based on user requests.
        You are working with a pandas DataFrame in memory named `df`.

        Here is the schema of the DataFrame:
        ```
        {df_schema}
        ```

        Here is the head of the DataFrame:
        ```
        {df_head}
        ```

        Here is the tail of the DataFrame:
        ```
        {df_tail}
        ```

        The user has requested the following visualization:
        "{user_request}"

        Your task is to generate ONLY the Python code (using Plotly Express) to create the requested visualization.
        Your response must be a raw string of Python code, without any markdown, code fences (```), or explanations.
        
        CRITICAL REQUIREMENTS TO PREVENT ERRORS:
        - The code should be a single block.
        - The DataFrame is already in memory as `df`. Do not load any data.
        - `pandas` is imported as `pd`.
        - The final chart object must be assigned to a variable named `fig`. For example: `fig = px.bar(...)`
        - `plotly.express` is already imported as `px`. Do not import it again.
        - Do not include `st.plotly_chart(fig)`. The app will handle rendering.
        - **ONLY use columns that exist in the DataFrame schema above. Available columns are: {df_columns}**
        - **Handle missing data: Use df.dropna() or df.fillna() as appropriate**
        - **For aggregations, use pandas groupby/agg methods before plotting**
        - **Only use valid Plotly Express function parameters. Common valid parameters include: x, y, color, size, hover_data, title, labels**
        - **If a column has mixed data types, convert appropriately: pd.to_numeric(df['col'], errors='coerce')**
        - **For date columns, ensure proper datetime conversion: pd.to_datetime(df['col'], errors='coerce')**
        - **Always include error handling for data operations**
        - **If the request cannot be fulfilled with available data, create a simple fallback visualization**
        - **Wrap the main plotting logic in a try-except block and provide a fallback chart if errors occur**
        """

    # --- API Call Logic ---
    if model == "Gemini 1.5 Flash":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"An error occurred while calling the Gemini API: {e}")

    elif model == "ChatGPT 4o":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o", # Or another suitable model
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_request}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"An error occurred while calling the OpenAI API: {e}")
            
    else:
        raise ValueError("Invalid model provider specified. Choose 'Gemini' or 'OpenAI'.") 