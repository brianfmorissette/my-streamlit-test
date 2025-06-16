# PM ChatGPT Enterprise Analytics

This Streamlit application uses the Gemini and OpenAI APIs to create custom data visualizations on the fly based on user prompts.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd Prototype3
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    - Create a `.env` file in the root of the project.
    - Add your API keys to the `.env` file:
      ```
      GEMINI_API_KEY="your_gemini_api_key"
      OPENAI_API_KEY="your_openai_api_key"
      ```

## How to Run

To run the Streamlit application, execute the following command from the project's root directory:

```bash
streamlit run src/app.py
```
