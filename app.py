import os
import re
from datetime import datetime
import streamlit as st
from arxiv_fetcher import fetch_papers
from paper_display import display_papers_with_pagination
from paper_download import bulk_download
from authentication import register_user, login_user
from db_manager import init_db
from db_manager import get_connection


# Function to sanitize filenames and folder names
def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)  # Replace non-alphanumeric characters with underscores

def main():
    # Initialize the database
    init_db()


    # Set page layout to wide to utilize full screen
    st.set_page_config(layout="wide")

    # Initialize session state for authentication
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_id'] = None
        st.session_state['username'] = ''

    # Sidebar for theme selection and navigation
    with st.sidebar:
        st.title("🔍 arXiv Paper Search")

        # Theme selection
        theme = st.selectbox('Select Theme', ['Dark', 'Coding'], index=0)
        st.session_state['theme'] = theme  # Store theme in session state

        # Navigation menu
        if st.session_state['logged_in']:
            menu = ["Home", "Logout"]
        else:
            menu = ["Login", "Register"]
        choice = st.selectbox("Menu", menu)

    # Apply custom CSS based on the selected theme
    apply_theme(st.session_state['theme'])

    # Main content area
    if st.session_state['logged_in']:
        if choice == "Home":
            display_search_page()
        elif choice == "Logout":
            display_logout()
    else:
        if choice == "Login":
            display_login_page()
        elif choice == "Register":
            display_register_page()

def apply_theme(theme):
    css_file = ''
    if theme == 'Dark':
        css_file = 'css/dark_theme.css'
    elif theme == 'Coding':
        css_file = 'css/coding_theme.css'
    else:
        css_file = 'css/coding_theme.css'  # Default to Coding theme

    # Read the CSS file
    with open(css_file) as f:
        css = f"<style>{f.read()}</style>"
    st.markdown(css, unsafe_allow_html=True)

def display_login_page():
    st.title("🔑Login🔑")
    

    # Center the login form using columns
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form(key='login_form'):
            st.markdown("Please enter your credentials to log in.")
            # Username input
            st.markdown("<label for='login_username'>Username</label>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username", label_visibility='collapsed')

            # Password input
            st.markdown("<label for='login_password'>Password</label>", unsafe_allow_html=True)
            password = st.text_input("Password", type='password', key="login_password", label_visibility='collapsed')

            login_button = st.form_submit_button("Login")

    # Handle login logic
    if login_button:
        user_id = login_user(username, password)
        if user_id:
            st.session_state['logged_in'] = True
            st.session_state['user_id'] = user_id
            st.session_state['username'] = username
            st.success(f"Logged in as {username}")
            st.rerun()
        else:
            st.error("Invalid username or password")

def display_register_page():
    st.title("Register")
    st.markdown("Create a new account.")

    # Center the register form using columns
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form(key='register_form'):
            # Username input
            st.markdown("<label for='new_username'>Username</label>", unsafe_allow_html=True)
            new_username = st.text_input("Username", key="new_username", label_visibility='collapsed')

            # Password input
            st.markdown("<label for='new_password'>Password</label>", unsafe_allow_html=True)
            new_password = st.text_input("Password", type='password', key="new_password", label_visibility='collapsed')

            # Register button
            register_button = st.form_submit_button("Register")

    # Handle registration logic
    if register_button:
        if register_user(new_username, new_password):
            st.success("Registration successful! Please log in.")
            st.rerun()
        else:
            st.error("Username already exists. Please choose a different one.")

def display_logout():
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = ''
    st.success("You have been logged out.")
    st.rerun()

def display_search_page():
    st.title("🔍 arXiv Paper Search")

    # Main search input wrapped in a container for styling
    st.markdown("<div class='search-form'>", unsafe_allow_html=True)
    st.markdown("<label for='search_query'>Search Term</label>", unsafe_allow_html=True)
    query = st.text_input("Search Term", key="search_query", label_visibility='collapsed')
    st.markdown("</div>", unsafe_allow_html=True)

    # Advanced search options inside an expander
    with st.expander("📊 Advanced Search Options"):
        st.markdown("<div class='advanced-options'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        # Use current real date to prevent future dates
        today = datetime.now().date()
        with col1:
            from_date = st.date_input("📅 From Date", value=datetime(2023, 1, 1).date(), max_value=today)
            categories = {
                "All Categories": None,
                "Computer Science - Computation and Language": "cs.CL",
                "Machine Learning": "cs.LG",
                "Artificial Intelligence": "cs.AI",
                "Information Retrieval": "cs.IR"
            }
            category = st.selectbox("📂 Select Category", options=list(categories.keys()), index=0)
        with col2:
            to_date = st.date_input("📅 To Date", value=today, max_value=today)
            max_results = st.slider("📝 Number of papers to retrieve", min_value=1, max_value=1000, value=20)
        st.markdown("</div>", unsafe_allow_html=True)

    # Center the search button
    st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
    search_button = st.button("Search")
    st.markdown("</div>", unsafe_allow_html=True)

    if search_button and query.strip():
        # Clear previous search results
        st.session_state.papers = []
        st.session_state.selected_papers = []

        # Store the query in session state
        st.session_state.query = query

        # Fetch the papers
        with st.spinner("Searching for papers..."):
            papers_response = fetch_papers(
                query,
                from_date.strftime('%Y%m%d'),
                to_date.strftime('%Y%m%d'),
                categories[category],
                max_results
            )

        if papers_response:
            # Store the fetched papers in session state
            st.session_state.papers = papers_response

    # Display paginated papers and download options
    if 'papers' in st.session_state and st.session_state.papers:
        selected_papers = display_papers_with_pagination(st.session_state.papers)

        # Option to select and download all papers at once
        st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
        if st.button("Select All Papers and Download"):
            st.session_state.selected_papers = st.session_state.papers
            bulk_download(st.session_state.papers, st.session_state.query)  # Use query from session state
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()



