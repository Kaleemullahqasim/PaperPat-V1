import os
import streamlit as st
from datetime import datetime

# Function to generate BibTeX entries for selected papers
def generate_bibtex(papers):
    bib_entries = []
    
    for paper in papers:
        # Use authors as-is, assuming authors were parsed correctly in fetch_papers
        authors = paper['authors'] if 'authors' in paper else "Unknown"

        # Ensure the correct ePrint is used for DOI and URL
        eprint = paper.get('pdf_url', paper.get('id', 'XXXX.XXXXX'))  # Fallback if eprint is missing
        doi_url = f"https://doi.org/10.48550/arXiv.{eprint}"
        arxiv_url = f"https://arxiv.org/abs/{eprint}"

        # Create a unique cite key from title and year
        cite_key = f"{paper['title'].replace(' ', '_')}_{paper['published'][:4]}"

        # Generate BibTeX entry with required fields, including DOI and URL
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

# Function to save BibTeX file in the current folder or a folder named by date
def save_bibtex_file(bibtex_content, folder_name=None):
    # Use the current date for folder name if none is provided
    if folder_name is None:
        folder_name = datetime.now().strftime('%Y-%m-%d')

    # Ensure the folder exists
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Define the path for the .bib file
    file_path = os.path.join(folder_name, f"{folder_name}.bib")
    
    # Write BibTeX content to the file
    with open(file_path, "w", encoding="utf-8") as bib_file:
        bib_file.write(bibtex_content)

    st.success(f"BibTeX file generated: {file_path}")
    return file_path