from datetime import datetime
import streamlit as st
from arxiv_fetcher import fetch_papers
from paper_display import display_papers_with_pagination
from paper_download import bulk_download
from paper_citation import generate_bibtex, save_bibtex_file  # Import BibTeX functions
from session_manager import initialize_session_state
import os
import re


# # Function to sanitize filenames and folder names
def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)  # Replace non-alphanumeric characters with underscores

# Main Streamlit app
def main():
    # Set page layout to wide to utilize full screen
    st.set_page_config(layout="wide")

    # Initialize session state
    initialize_session_state()

    # Sidebar for search input and filters
    with st.sidebar:
        st.title("🔍 arXiv Paper Search")

        # Search input
        query = st.text_input("Enter your search term (e.g., 'machine learning')", "")

        # Advanced search options
        st.markdown("### 📊 Advanced Search Options")

        from_date = st.date_input("📅 From Date", value=datetime(2023, 1, 1))
        to_date = st.date_input("📅 To Date", value=datetime.now())

        categories = {
            "All Categories": None,
            "Computer Science - Computation and Language": "cs.CL",
            "Machine Learning": "cs.LG",
            "Artificial Intelligence": "cs.AI",
            "Information Retrieval": "cs.IR"
        }
        category = st.selectbox("📂 Select Category", options=list(categories.keys()), index=0)

        # Max results slider
        max_results = st.slider("📝 Number of papers to retrieve", min_value=1, max_value=1000, value=100)

        # Search button
        search_button = st.button("🔍 Search")

    # Main content area for results
    st.title("arXiv Paper Search and Download Results")

    if search_button and query.strip():
        # Clear previous search results
        st.session_state.papers = []
        st.session_state.selected_papers = []
        
        # Store the query in session state
        st.session_state.query = query

        # Fetch the papers
        with st.spinner("Searching for papers..."):
            papers_response = fetch_papers(query, from_date.strftime('%Y%m%d'), to_date.strftime('%Y%m%d'), categories[category], max_results)

        if papers_response:
            # Store the fetched papers in session state
            st.session_state.papers = papers_response

    # Display paginated papers and download options
    if st.session_state.papers:
        selected_papers = display_papers_with_pagination(st.session_state.papers)

        # Option to select and download all papers at once
        if st.button("Select All Papers and Download"):
            st.session_state.selected_papers = st.session_state.papers
            bulk_download(st.session_state.papers, st.session_state.query)  # Use query from session state


if __name__ == "__main__":
    main()
