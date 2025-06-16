import pandas as pd
import os
import ast
from datetime import datetime

# Define the columns for each of the three master DataFrames
# This ensures consistency across the application.
USER_COLS = [
    'week_start', 'email', 'name', 'user_status', 'is_active', 'messages', 'gpts_messaged', 'tools_messaged', 
    'projects_created', 'last_day_active'
]
MODEL_COLS = ['week_start', 'email', 'name', 'model', 'messages']
TOOL_COLS = ['week_start', 'email', 'name', 'tool', 'messages']


def initialize_master_dataframes():
    """
    Creates three empty master DataFrames with the correct columns and data types.
    This is called if no saved master files are found on the first app run.

    Returns:
        tuple: A tuple containing the three empty (users, models, tools) DataFrames.
    """
    users_df = pd.DataFrame(columns=USER_COLS)
    models_df = pd.DataFrame(columns=MODEL_COLS)
    tools_df = pd.DataFrame(columns=TOOL_COLS)
    
    # Set data types for more efficient storage and operations
    users_df = users_df.astype({
        'week_start': 'datetime64[ns]', 'email': 'str', 'name': 'str', 'user_status': 'category', 
        'is_active': 'bool', 'messages': 'int', 'gpts_messaged': 'int', 'tools_messaged': 'int', 
        'projects_created': 'int', 'last_day_active': 'datetime64[ns]'
    })
    models_df = models_df.astype({'week_start': 'datetime64[ns]', 'email': 'str', 'name': 'str', 'model': 'str', 'messages': 'int'})
    tools_df = tools_df.astype({'week_start': 'datetime64[ns]', 'email': 'str', 'name': 'str', 'tool': 'str', 'messages': 'int'})
    
    return users_df, models_df, tools_df


def save_master_dataframes(users_df, models_df, tools_df, path='.'):
    """
    Saves the master DataFrames to Parquet files for persistence.
    This is called after a new file is successfully uploaded and processed.

    Args:
        users_df (pd.DataFrame): The updated master users DataFrame.
        models_df (pd.DataFrame): The updated master models DataFrame.
        tools_df (pd.DataFrame): The updated master tools DataFrame.
        path (str): The directory where the files will be saved.
    """
    users_df.to_parquet(os.path.join(path, 'master_users.parquet'))
    models_df.to_parquet(os.path.join(path, 'master_models.parquet'))
    tools_df.to_parquet(os.path.join(path, 'master_tools.parquet'))


def load_master_dataframes(path='.'):
    """
    Loads the master DataFrames from Parquet files if they exist. If they don't,
    it calls initialize_master_dataframes() to start fresh.

    Args:
        path (str): The directory where the files are stored.

    Returns:
        tuple: A tuple containing the three master (users, models, tools) DataFrames.
    """
    try:
        users_df = pd.read_parquet(os.path.join(path, 'master_users.parquet'))
        models_df = pd.read_parquet(os.path.join(path, 'master_models.parquet'))
        tools_df = pd.read_parquet(os.path.join(path, 'master_tools.parquet'))
        return users_df, models_df, tools_df
    except FileNotFoundError:
        # If files don't exist, it's the first run.
        return initialize_master_dataframes()


def _flatten_data(df, id_vars, col_to_flatten, new_col_names):
    """
    A helper function to flatten columns that contain dictionary-like strings.
    It unnests the data into a tidy format.
    """
    # Drop rows where the column to flatten or the user email is missing
    df = df.dropna(subset=id_vars + [col_to_flatten])
    
    # Filter out non-dictionary or empty values (e.g., '0' or NaN)
    df = df[df[col_to_flatten].astype(str).str.startswith('{')]
    
    if df.empty:
        return pd.DataFrame(columns=id_vars + new_col_names)

    # Use ast.literal_eval to safely convert the string to a dictionary
    df[col_to_flatten] = df[col_to_flatten].apply(ast.literal_eval)
    
    records = []
    for _, row in df.iterrows():
        for key, value in row[col_to_flatten].items():
            record = {var: row[var] for var in id_vars}
            record[new_col_names[0]] = key
            record[new_col_names[1]] = value
            records.append(record)
            
    return pd.DataFrame(records) if records else pd.DataFrame(columns=id_vars + new_col_names)


def process_uploaded_file(df, filename):
    """
    Processes a raw DataFrame from a single CSV file and splits it into three
    clean DataFrames: user details, model usage, and tool usage.

    Args:
        df (pd.DataFrame): The raw DataFrame from the uploaded file.
        filename (str): The name of the file (currently unused but kept for future use).

    Returns:
        tuple: A tuple containing the three processed (users, models, tools) DataFrames.
    """
    df.dropna(subset=['email'], inplace=True)
    df.rename(columns={'period_start': 'week_start'}, inplace=True)

    # --- 1. Date and Type Conversions ---
    date_cols = ['week_start', 'last_day_active']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    numeric_cols = ['messages', 'gpts_messaged', 'tools_messaged', 'projects_created']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df['is_active'] = df['is_active'].astype('bool')
    df['user_status'] = df['user_status'].astype('category')

    

    # --- 2. Create the User Details DataFrame ---
    users_df = df.reindex(columns=USER_COLS).copy()

    # --- 3. Create the Model and Tool Usage DataFrames ---
    id_vars = ['week_start', 'email', 'name']
    models_df = _flatten_data(df, id_vars, 'model_to_messages', ['model', 'messages'])
    tools_df = _flatten_data(df, id_vars, 'tool_to_messages', ['tool', 'messages'])
    
    # Ensure correct data types for the flattened frames
    if not models_df.empty:
        models_df['messages'] = pd.to_numeric(models_df['messages'], errors='coerce').fillna(0).astype(int)

    if not tools_df.empty:
        tools_df['messages'] = pd.to_numeric(tools_df['messages'], errors='coerce').fillna(0).astype(int)

    return users_df, models_df, tools_df