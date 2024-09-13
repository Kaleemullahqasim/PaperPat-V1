import streamlit as st

# Function to initialize session state
def initialize_session_state():
    if 'papers' not in st.session_state:
        st.session_state.papers = []
    if 'selected_papers' not in st.session_state:
        st.session_state.selected_papers = []