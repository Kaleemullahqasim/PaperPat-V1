import arxiv
import datetime
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function to save search history to the database
def save_search_history(user_id, query):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO search_history (user_id, query) VALUES (?, ?)', (user_id, query))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving search history: {e}")

def fetch_papers(query, from_date_str, to_date_str, category=None, max_results=1000):
    if st.session_state.get('logged_in'):
        user_id = st.session_state['user_id']
        save_search_history(user_id, query)

    # Convert date strings to datetime.date objects
    from_date = datetime.datetime.strptime(from_date_str, '%Y%m%d').date()
    to_date = datetime.datetime.strptime(to_date_str, '%Y%m%d').date()

    # Ensure to_date is not in the future
    today = datetime.datetime.now().date()
    if to_date > today:
        to_date = today

    # Construct the query
    search_query = query
    if category:
        search_query += f' AND cat:{category}'

    # Create the search
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    for result in search.results():
        published_date = result.published.date()
        if from_date <= published_date <= to_date:
            paper = {
                'title': result.title,
                'authors': ', '.join(author.name for author in result.authors),
                'published': result.published.strftime('%Y-%m-%d'),
                'summary': result.summary,
                'arxiv_url': result.entry_id,
                'pdf_url': result.pdf_url,
                'arxiv_id': result.get_short_id(),
                'abstract': result.summary,
                'category': category or 'N/A'
            }
            logger.debug(f"Fetched paper: {paper['title']}, PDF URL: {paper['pdf_url']}")
            papers.append(paper)
    return papers