import os
import requests
from datetime import datetime
import streamlit as st
import re
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function to sanitize filenames and folder names
def sanitize_filename(name):
    sanitized_name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    sanitized_name = sanitized_name.strip(' ._')
    return sanitized_name

# Function to download a single PDF with retries and file size check
def download_pdf(paper, folder_name):
    sanitized_title = sanitize_filename(paper['title'])
    file_path = os.path.join(folder_name, f"{sanitized_title}.pdf")
    pdf_url = paper['pdf_url']  # Use the direct PDF URL

    logger.debug(f"Attempting to download PDF from: {pdf_url}")

    try:
        for attempt in range(3):  # Retry up to 3 times
            response = requests.get(pdf_url, stream=True)
            logger.debug(f"Download attempt {attempt + 1} for {pdf_url}, status code: {response.status_code}")
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                # Check if the file size is larger than a small threshold (to prevent corrupted files)
                if os.path.getsize(file_path) > 10 * 1024:  # File size should be larger than 10KB
                    logger.debug(f"Successfully downloaded: {file_path}")
                    return sanitized_title  # Successfully downloaded
                else:
                    # Delete the incomplete file
                    os.remove(file_path)
                    logger.warning(f"Incomplete download for {pdf_url}, file too small.")
                    sleep(1)  # Delay before retrying
            else:
                logger.warning(f"Failed to download {pdf_url}, status code: {response.status_code}")
                sleep(1)  # Delay before retrying

        # If all attempts fail
        logger.error(f"Failed to download paper: {paper['title']} after 3 attempts.")
        return None

    except Exception as e:
        logger.exception(f"Exception occurred while downloading '{paper['title']}': {e}")
        return None

# Function to bulk download selected papers using multithreading and progress bar
def bulk_download(papers, query):
    logger.debug(f"Starting bulk download for query: {query}")
    logger.debug(f"Number of papers to download: {len(papers)}")
    sanitized_query = sanitize_filename(query)
    folder_name = f"{sanitized_query}_{datetime.now().strftime('%Y-%m-%d')}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    total_papers = len(papers)
    downloaded_count = 0

    # Initialize progress bar and status text
    progress_bar = st.progress(0)
    status_text = st.empty()

    with st.spinner('Downloading papers...'):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(download_pdf, paper, folder_name): paper for paper in papers}

            for i, future in enumerate(as_completed(futures), 1):
                paper = futures[future]
                try:
                    result = future.result()
                    if result:
                        downloaded_count += 1
                    else:
                        logger.error(f"Failed to download paper: {paper['title']}")
                except Exception as e:
                    logger.exception(f"Error downloading paper '{paper['title']}': {e}")

                # Update progress bar and status text
                progress = i / total_papers
                progress_bar.progress(progress)
                status_text.text(f"Downloaded {downloaded_count} out of {total_papers} papers.")

    # After all downloads are complete
    progress_bar.empty()
    status_text.empty()
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
        arxiv_id = paper.get('arxiv_id', 'XXXX.XXXXX')
        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
        cite_key = f"{sanitize_filename(paper['title'])}_{paper['published'][:4]}"

        bib_entry = f"""@misc{{{cite_key},
  title = {{{{ {paper['title']} }}}},
  author = {{{{ {authors} }}}},
  year = {{{{ {paper['published'][:4]} }}}},
  eprint = {{{{ {arxiv_id} }}}},
  archivePrefix = {{arXiv}},
  primaryClass = {{{{ {paper.get('category', 'cs.CL')} }}}},
  abstract = {{{{ {paper.get('abstract', 'No abstract available')} }}}},
  url = {{{{ {arxiv_url} }}}}
}}"""
        bib_entries.append(bib_entry.strip())
    return "\n\n".join(bib_entries)

# Function to save BibTeX file in the folder
def save_bibtex_file(bibtex_content, folder_name):
    bib_filename = f"{folder_name}.bib"
    file_path = os.path.join(folder_name, bib_filename)
    try:
        with open(file_path, "w", encoding="utf-8") as bib_file:
            bib_file.write(bibtex_content)
        st.success(f"BibTeX file generated: {file_path}")
    except Exception as e:
        st.error(f"Error saving BibTeX file: {e}")