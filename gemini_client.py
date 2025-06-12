import google.generativeai as genai
import io


def get_visualization_code(user_request, df_for_prompt, api_key):
    """
    Calls the Gemini API to generate Python code for a visualization.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        # Let the caller handle UI feedback
        raise ValueError(f"Error configuring the API. Please check your key. Details: {e}")

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
        raise RuntimeError(f"An error occurred while calling the Gemini API: {e}") 