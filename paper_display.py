import streamlit as st
from paper_download import download_pdf
from datetime import datetime
import os

# Injecting custom CSS for improved layout and styling
def load_custom_css():
    custom_css = """
    <style>
    /* Paper Container */
    .paper-container {
        border-radius: 8px;
        border: 1px solid #333;
        padding: 15px;
        margin: 15px 0;
        background-color: #1f1f1f;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
    }

    .paper-container:hover {
        transform: scale(1.02);
    }

    /* Title Styling */
    .paper-title {
        font-family: 'Arial', sans-serif;
        font-size: 18px;
        font-weight: bold;
        color: #3498db;
        margin-bottom: 10px;
    }

    .paper-title a {
        text-decoration: none;
        color: #3498db;
    }

    .paper-title a:hover {
        text-decoration: underline;
        color: #2980b9;
    }

    /* Published Date Styling */
    .paper-published {
        font-family: 'Arial', sans-serif;
        font-size: 14px;
        color: #95a5a6;
        margin-bottom: 10px;
    }

    /* Abstract Styling */
    .paper-abstract {
        font-family: 'Fira Code', monospace;
        font-size: 15px;
        color: #ecf0f1;
        line-height: 1.6;
        padding-top: 5px;
    }

    /* Button Styling */
    .stButton button {
        background-color: #e74c3c;
        color: white;
        border: none;
        padding: 8px 12px;
        cursor: pointer;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
        transition: background-color 0.3s, transform 0.2s;
    }

    .stButton button:hover {
        background-color: #c0392b;
        transform: scale(1.05);
    }

    /* Checkbox Styling */
    .stCheckbox div {
        font-family: 'Arial', sans-serif;
        font-size: 14px;
        color: #ecf0f1;
    }

    /* Expander Styling */
    .stExpander {
        background-color: #2c2c2c;
        border-radius: 8px;
        padding: 10px;
    }

    .stExpander > div:first-child {
        font-family: 'Arial', sans-serif;
        font-size: 16px;
        color: #3498db;
    }

    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# Function to display papers with pagination
def display_papers_with_pagination(papers, items_per_page=10):
    # Load custom CSS
    load_custom_css()

    # Initialize session state for pagination
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    
    total_pages = (len(papers) - 1) // items_per_page + 1  # Calculate total number of pages

    # Get the current page of papers
    start_idx = st.session_state.current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(papers))
    papers_to_display = papers[start_idx:end_idx]

    selected_papers = []

    # Retrieve query from session state
    query = st.session_state.query if 'query' in st.session_state else 'query'
    folder_name = f"{query}_{datetime.now().strftime('%Y-%m-%d')}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Display papers for the current page
    cols = st.columns(2)  # Display in 2-column format for more readability
    for i, paper in enumerate(papers_to_display):
        with cols[i % 2]:  # Tile structure with 2-column layout
            st.markdown(f"<div class='paper-title'><a href='{paper['pdf_url']}' target='_blank'>{paper['title']}</a></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='paper-published'><b>Published:</b> {paper['published']}</div>", unsafe_allow_html=True)

            with st.expander("Show Abstract", expanded=False):
                st.markdown(f"<div class='paper-abstract'>{paper['abstract']}</div>", unsafe_allow_html=True)

            if st.button(f"Download PDF {start_idx + i + 1}", key=f"download_{start_idx + i}"):
                download_pdf(paper, folder_name)  # Pass the folder name

            if st.checkbox(f"Select {paper['title']}", key=f"select_{start_idx + i}"):
                selected_papers.append(paper)

    # Pagination controls
    st.markdown(f"Page {st.session_state.current_page + 1} of {total_pages}")

    # Navigation buttons for pagination
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.session_state.current_page > 0:
            if st.button("Previous"):
                st.session_state.current_page -= 1
                st.rerun()

    with col3:
        if st.session_state.current_page < total_pages - 1:
            if st.button("Next"):
                st.session_state.current_page += 1
                st.rerun()

    return selected_papers