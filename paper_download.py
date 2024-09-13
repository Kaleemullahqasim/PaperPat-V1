import os
import requests
from datetime import datetime
import streamlit as st
import re
from concurrent.futures import ThreadPoolExecutor
from time import sleep

# Function to sanitize filenames and folder names
def sanitize_filename(name):
    sanitized_name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    return sanitized_name.strip()

# Function to download a single PDF with retries and file size check
def download_pdf(paper, folder_name):
    sanitized_title = sanitize_filename(paper['title'])
    file_path = os.path.join(folder_name, f"{sanitized_title}.pdf")
    pdf_url = f"https://arxiv.org/pdf/{paper['pdf_url']}.pdf"

    try:
        for attempt in range(3):  # Retry up to 3 times
            response = requests.get(pdf_url, stream=True)
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                # Check if the file size is larger than a small threshold (to prevent corrupted files)
                if os.path.getsize(file_path) > 10 * 1024:  # File size should be larger than 10KB
                    return sanitized_title  # Successfully downloaded
                else:
                    st.warning(f"File too small for {paper['title']}, retrying...")

            sleep(1)  # Delay before retrying

        st.error(f"Failed to download {paper['title']} after 3 attempts.")
        return None  # Return None if the file couldn't be downloaded correctly

    except Exception as e:
        st.error(f"Error downloading {paper['title']}: {e}")
        return None

# Function to bulk download selected papers using multithreading
def bulk_download(papers, query):
    sanitized_query = sanitize_filename(query)
    folder_name = f"{sanitized_query}_{datetime.now().strftime('%Y-%m-%d')}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    total_papers = len(papers)
    downloaded_count = 0

    with st.spinner('Downloading papers...'):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(download_pdf, paper, folder_name) for paper in papers]

            downloaded_papers = [future.result() for future in futures]

    downloaded_count = len([paper for paper in downloaded_papers if paper is not None])
    st.success(f"Downloaded {downloaded_count} out of {total_papers} papers.")
    st.write(f"Files saved to folder: {folder_name}")

    # Generate and save the BibTeX file
    bibtex_content = generate_bibtex(papers)
    save_bibtex_file(bibtex_content, folder_name)

# Function to generate BibTeX content
def generate_bibtex(papers):
    bib_entries = []
    for paper in papers:
        authors = paper.get('authors', 'Unknown')
        eprint = paper.get('pdf_url', 'XXXX.XXXXX')
        doi_url = f"https://doi.org/10.48550/arXiv.{eprint}"
        arxiv_url = f"https://arxiv.org/abs/{eprint}"
        cite_key = f"{sanitize_filename(paper['title'])}_{paper['published'][:4]}"

        bib_entry = f"""
        @misc{{{cite_key}}},
          title = {{{paper['title']}}},
          author = {{{authors}}},
          year = {{{paper['published'][:4]}}},
          eprint = {{{eprint}}},
          archivePrefix = {{arXiv}},
          primaryClass = {{{paper.get('category', 'cs.CL')}}},
          abstract = {{{paper.get('abstract', 'No abstract available')}}},
          url = {{{arxiv_url}}},
          doi = {{{doi_url}}}
        }}
        """
        bib_entries.append(bib_entry.strip())
    return "\n\n".join(bib_entries)

# Function to save BibTeX file in the folder
def save_bibtex_file(bibtex_content, folder_name):
    file_path = os.path.join(folder_name, f"{folder_name}.bib")
    with open(file_path, "w", encoding="utf-8") as bib_file:
        bib_file.write(bibtex_content)
    st.success(f"BibTeX file generated: {file_path}")