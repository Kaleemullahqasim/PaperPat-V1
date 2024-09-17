
import os
import requests
from datetime import datetime
import streamlit as st
import re
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define the base download path
BASE_PATH = "/Volumes/Research Papers/arxiv/"

# Create necessary folders if they don't exist
os.makedirs(os.path.join(BASE_PATH, "bulk_download"), exist_ok=True)
os.makedirs(os.path.join(BASE_PATH, "singlepaper"), exist_ok=True)

# Function to sanitize filenames and folder names
def sanitize_filename(name):
    sanitized_name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    sanitized_name = sanitized_name.strip(' ._')
    return sanitized_name


# Function to download a single PDF with retries and file size check
def download_pdf(paper, folder_name=None):
    # Determine if this is a single paper download and set the appropriate folder
    if folder_name is None:
        folder_name = os.path.join(BASE_PATH, "singlepaper")
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    sanitized_title = sanitize_filename(paper['title'])
    file_path = os.path.join(folder_name, f"{sanitized_title}.pdf")
    pdf_url = paper['pdf_url']  # Use the direct PDF URL

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
                    # Generate and save BibTeX file for the single paper
                    bibtex_content = generate_bibtex([paper])  # Pass a list with the single paper
                    save_bibtex_file(bibtex_content, folder_name)
                    
                    return sanitized_title  # Successfully downloaded
                else:
                    # Retry if the file size is too small
                    st.warning(f"File too small for '{paper['title']}', retrying...")
            else:
                st.warning(f"Failed to download '{paper['title']}' (status code: {response.status_code}), retrying...")

            sleep(1)  # Delay before retrying

        st.error(f"Failed to download '{paper['title']}' after 3 attempts.")
        return None  # Return None if the file couldn't be downloaded correctly

    except Exception as e:
        st.error(f"Error downloading '{paper['title']}': {e}")
        return None


# Function to bulk download selected papers using multithreading (no changes needed)
def bulk_download(papers, query):
    sanitized_query = sanitize_filename(query)
    folder_name = os.path.join(BASE_PATH, "bulk_download", f"{sanitized_query}_{datetime.now().strftime('%Y-%m-%d')}")
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
                    # You can handle failed downloads if needed
                except Exception as e:
                    # Handle exceptions if needed
                    pass

                # Update progress bar and status text
                progress = i / total_papers
                progress_bar.progress(progress)
                status_text.text(f"Downloaded {downloaded_count} out of {total_papers} papers.")

    # After all downloads are complete
    progress_bar.empty()
    status_text.empty()
    st.success(f"Downloaded {downloaded_count} out of {total_papers} papers.")
    st.write(f"Files saved to folder: {folder_name}")

    # Generate and save the BibTeX file in the same folder
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
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    bib_filename = f"arxiv_papers_{timestamp}.bib"
    file_path = os.path.join(folder_name, bib_filename)
    try:
        with open(file_path, "w", encoding="utf-8") as bib_file:
            bib_file.write(bibtex_content)
        st.success(f"BibTeX file generated: {file_path}")
    except Exception as e:
        st.error(f"Error saving BibTeX file: {e}")

# New function for single paper download
def download_single_paper(paper):
    # Create singlepaper folder path
    folder_name = os.path.join(BASE_PATH, "singlepaper")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Download the paper
    result = download_pdf(paper, folder_name)
    if result:
        st.success(f"Downloaded: {result}.pdf")

        # Generate and save BibTeX file for the single paper
        bibtex_content = generate_bibtex([paper])  # Pass a list with the single paper
        save_bibtex_file(bibtex_content, folder_name)
    else:
        st.error(f"Failed to download '{paper['title']}'")