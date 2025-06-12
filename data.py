import streamlit as st
import pandas as pd


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