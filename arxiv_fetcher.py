import requests
import xml.etree.ElementTree as ET
import streamlit as st

# Function to fetch arXiv papers based on query and filters
def fetch_papers(query, from_date, to_date, category, max_results=1000):
    base_url = "http://export.arxiv.org/api/query?"

    # Prepare the search query
    search_query = f"search_query=all:{query}"
    if category:
        search_query += f"+AND+cat:{category}"

    # Add date filters
    if from_date:
        search_query += f"+AND+submittedDate:[{from_date}0000+TO+{to_date}2359]"

    # Construct the full API URL
    url = f"{base_url}{search_query}&start=0&max_results={max_results}"

    # Error handling for API request
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching papers: {e}")
        return []

    return parse_papers(response.text)

# Helper function to extract key details from the API response
def parse_papers(response_text):
    root = ET.fromstring(response_text)
    papers = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        paper = {
            'title': entry.find("{http://www.w3.org/2005/Atom}title").text,
            'published': entry.find("{http://www.w3.org/2005/Atom}published").text[:10],  # Only keep the date part
            'pdf_url': entry.find("{http://www.w3.org/2005/Atom}id").text.split('/')[-1]  # Extract paper ID for PDF
        }

        # Extract authors using the namespace
        authors = []
        for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
            author_name = author.find("{http://www.w3.org/2005/Atom}name").text
            # Debug log to check how author names are being extracted
            print(f"Author extracted: {author_name}")
            authors.append(author_name)

        # Correctly join authors with "and" separator
        paper['authors'] = " and ".join(authors)

        # Check if the abstract exists
        abstract_element = entry.find("{http://www.w3.org/2005/Atom}summary")
        if abstract_element is not None:
            paper['abstract'] = abstract_element.text.strip()
        else:
            paper['abstract'] = "Abstract not available."  # Default message if no abstract
        
        papers.append(paper)
    return papers