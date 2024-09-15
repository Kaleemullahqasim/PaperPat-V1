# arxiv_fetcher.py

import arxiv
import datetime
import streamlit as st
import logging
from db_manager import get_connection
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def save_search_history(user_id, query):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO search_history (user_id, query) VALUES (?, ?)', (user_id, query))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving search history: {e}")

def get_cached_results(query):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT results FROM cached_results WHERE query = ?', (query,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None
    except Exception as e:
        st.error(f"Error retrieving cached results: {e}")
        return None

def save_cached_results(query, results):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO cached_results (query, results) VALUES (?, ?)', (query, json.dumps(results)))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving cached results: {e}")

def fetch_papers(query, from_date_str, to_date_str, category=None, max_results=1000):
    if st.session_state.get('logged_in'):
        user_id = st.session_state['user_id']
        save_search_history(user_id, query)

    # Check if results are cached
    papers = get_cached_results(query)
    if papers:
        st.info("Loaded results from cache.")
        return papers
    else:
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
        
        # Save results to cache
        save_cached_results(query, papers)

        return papers