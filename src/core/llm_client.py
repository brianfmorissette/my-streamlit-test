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
    model_provider
):
    """
    Calls the selected LLM API to generate Python code for a visualization.
    """
    # --- Prompt Definition (shared by both models) ---
    with io.StringIO() as buffer:
        df_for_prompt.info(buf=buffer)
        df_schema = buffer.getvalue()
    df_head = df_for_prompt.head().to_string()

    prompt = f"""
    You are an expert and meticulous Python data analyst specializing in Plotly Express.
    Your goal is to generate clean, readable, and accurate Python code for visualizations based on user requests.
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
    - The final chart object must be assigned to a variable named `fig`. For example: `fig = px.bar(...)`
    - `plotly.express` is already imported as `px`. Do not import it again.
    - Do not include `st.plotly_chart(fig)`. The app will handle rendering.
    """

    # --- API Call Logic ---
    if model_provider == "Gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"An error occurred while calling the Gemini API: {e}")

    elif model_provider == "OpenAI":
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