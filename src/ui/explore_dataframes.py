import streamlit as st

def show_explore_dataframes(users_df_view, models_df_view, tools_df_view):
    """Renders the dataframe exploration section with tabs for Users, Models, and Tools."""
    
    st.header("Explore the Dataframes")
    tab1, tab2, tab3 = st.tabs(["Users", "Models", "Tools"])
    
    # Display each dataframe in its respective tab
    with tab1:
        st.dataframe(users_df_view)
    with tab2:
        st.dataframe(models_df_view)
    with tab3:
        st.dataframe(tools_df_view) 