import streamlit as st
from paper_download import download_pdf
from datetime import datetime
import os
from db_manager import get_connection
import re

# Function to display papers with pagination
def display_papers_with_pagination(papers, items_per_page=10):
    # The custom CSS is now handled in app.py based on the selected theme

    # Initialize session state for pagination
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 0

    total_pages = (len(papers) - 1) // items_per_page + 1  # Calculate total number of pages

    # Get the current page of papers
    start_idx = st.session_state['current_page'] * items_per_page
    end_idx = min(start_idx + items_per_page, len(papers))
    papers_to_display = papers[start_idx:end_idx]

    selected_papers = []

    # Retrieve query from session state
    query = st.session_state['query'] if 'query' in st.session_state else 'query'
    folder_name = sanitize_filename(f"{query}_{datetime.now().strftime('%Y-%m-%d')}")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Display papers for the current page
    cols = st.columns(2)  # Display in 2-column format for better readability
    for i, paper in enumerate(papers_to_display):
        with cols[i % 2]:  # Tile structure with 2-column layout
            # Create a container for each paper to apply styling
            with st.container():
                st.markdown(
                    f"<div class='paper-title'><a href='https://arxiv.org/abs/{paper['pdf_url']}' target='_blank'>{paper['title']}</a></div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='paper-authors'><b>Authors:</b> {paper.get('authors', 'N/A')}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='paper-published'><b>Published:</b> {paper['published']}</div>",
                    unsafe_allow_html=True
                )

                with st.expander("Show Abstract", expanded=False):
                    st.markdown(f"<div class='paper-abstract'>{paper['abstract']}</div>", unsafe_allow_html=True)

                # Buttons and checkboxes in a row
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"Download PDF {start_idx + i + 1}", key=f"download_{start_idx + i}"):
                        download_pdf(paper)  # Pass the folder name
                        if st.session_state.get('logged_in'):
                            log_user_interaction(st.session_state['user_id'], paper['pdf_url'], 'download')
                with col2:
                    if st.checkbox(f"Select Paper {start_idx + i + 1}", key=f"select_{start_idx + i}"):
                        selected_papers.append(paper)
                        if st.session_state.get('logged_in'):
                            log_user_interaction(st.session_state['user_id'], paper['pdf_url'], 'select')

    # Pagination controls
    st.markdown(f"Page {st.session_state['current_page'] + 1} of {total_pages}")

    # Navigation buttons for pagination
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.session_state['current_page'] > 0:
            if st.button("Previous"):
                st.session_state['current_page'] -= 1
                st.rerun()

    with col3:
        if st.session_state['current_page'] < total_pages - 1:
            if st.button("Next"):
                st.session_state['current_page'] += 1
                st.rerun()

    return selected_papers

# Function to log user interactions
def log_user_interaction(user_id, paper_id, action):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_interactions (user_id, paper_id, action) VALUES (?, ?, ?)', (user_id, paper_id, action))
        conn.commit()
        conn.close()
        # # Debug: Indicate successful logging
        # st.write(f"Logged {action} action for user_id: {user_id}, paper_id: {paper_id}")
    except Exception as e:
        st.error(f"Error logging user interaction: {e}")

# Function to sanitize filenames and folder names
def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)  # Replace non-alphanumeric characters with underscores