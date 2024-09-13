# Import required libraries
import requests

# Function to send a chunk of text to the LLM for summarization
def summarize_with_llm(text_chunk):
    # API details
    api_url = "http://localhost:1234/v1/chat/completions"  # Your local LLM API URL
    headers = {
        "Authorization": "Bearer YOUR_API_KEY",  # Add the API key for your local LLM
        "Content-Type": "application/json"
    }

    # Create data for the LLM
    data = {
        "model": "model-identifier",  # Use your model identifier
        "messages": [
            {"role": "system", "content": "Summarize the following text:"},
            {"role": "user", "content": text_chunk}
        ],
        "temperature": 0.5  # Adjust temperature as needed
    }

    # Send the request to the local LLM
    response = requests.post(api_url, headers=headers, json=data)
    response_json = response.json()

    # Extract the summary from the LLM response
    summary = response_json["choices"][0]["message"]["content"]
    return summary

# Function to chunk the extracted text into smaller pieces for LLM processing
def chunk_text(text, max_words=2000):
    paragraphs = text.split("\n\n")  # Split the text into paragraphs based on double newlines
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # Check if adding this paragraph exceeds the maximum word count
        if len(current_chunk.split()) + len(paragraph.split()) <= max_words:
            current_chunk += paragraph + "\n\n"
        else:
            chunks.append(current_chunk.strip())  # Add the current chunk to the list
            current_chunk = paragraph + "\n\n"   # Start a new chunk with the current paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())  # Add the final chunk

    return chunks

