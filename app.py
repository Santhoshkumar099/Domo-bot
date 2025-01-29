import streamlit as st
import fitz  # PyMuPDF
import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Domo API Credentials
DOMO_DEVELOPER_TOKEN = os.getenv("DOMO_DEVELOPER_TOKEN")
API_URL = "https://gwcteq-partner.domo.com/api/ai/v1/text/generation"

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf") 
    pages = []
    for page_num, page in enumerate(doc):
        page_text = page.get_text("text")
        pages.append({"page_number": page_num + 1, "content": page_text})
    return pages

# Function to highlight query in text
def highlight_text(text, query):
    """Wraps matched words in bold to highlight them."""
    if query.strip():
        highlighted_text = re.sub(f"({re.escape(query)})", r"**\1**", text, flags=re.IGNORECASE)
        return highlighted_text
    return text

# Streamlit UI
st.title("📄 AI-Powered PDF Chatbot")
st.write("Upload a PDF and ask questions based on its content.")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file (Max: 5MB)", type=["pdf"], accept_multiple_files=False)

# Store response in session state
if "answer" not in st.session_state:
    st.session_state.answer = None
if "pdf_pages" not in st.session_state:
    st.session_state.pdf_pages = []

if uploaded_file is not None:
    if uploaded_file.size > 5 * 1024 * 1024:
        st.error("File size exceeds 5MB limit. Please upload a smaller file.")
    else:
        # Extract text from PDF
        pdf_pages = extract_text_from_pdf(uploaded_file)
        st.session_state.pdf_pages = pdf_pages  # Store pages in session

        # Chat input
        user_query = st.text_input("Ask a question based on the PDF content:")

        if st.button("Get Answer") and user_query:
            # Domo API Request
            payload = {
                "input": user_query,
                "model": "domo.domo_ai.domogpt-chat-medium-v1.1:anthropic",
                "system": """
                    You are a chatbot that answers questions based on the given PDF text.
                    Provide concise answers, limited to 2 lines, ensuring clarity and relevance.
                """
            }
            headers = {
                "Content-Type": "application/json",
                "X-DOMO-Developer-Token": DOMO_DEVELOPER_TOKEN
            }

            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                result = response.json()
                st.session_state.answer = result.get("output", "No response received.")
            else:
                st.session_state.answer = f"Error: {response.status_code} - {response.text}"

        # Display answer
        if st.session_state.answer:
            st.success(st.session_state.answer)

            # Expander 
            with st.expander("Expand to view your question in PDF"):
                found = False  # Flag to check if query matches any page
                for page in st.session_state.pdf_pages:
                    if user_query.lower() in page["content"].lower():
                        st.write(f"**Page {page['page_number']}**")
                        highlighted_content = highlight_text(page["content"], user_query)
                        st.markdown(highlighted_content)  # Display with markdown for bold effect
                        st.write("-----------------------------")
                        found = True  
                if not found:
                    st.write("No relevant content found in the PDF.")
