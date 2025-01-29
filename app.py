import streamlit as st
import fitz  # PyMuPDF
import requests
import json
import os
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

# Domo API Credentials
DOMO_DEVELOPER_TOKEN = os.getenv("DOMO_DEVELOPER_TOKEN")
API_URL = "https://gwcteq-partner.domo.com/api/ai/v1/text/generation"

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")  # Read from BytesIO
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Streamlit UI
st.title("📄 AI-Powered PDF Chatbot")
st.write("Upload a PDF and ask questions based on its content.")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file (Max: 5MB)", type=["pdf"], accept_multiple_files=False)

if uploaded_file is not None:
    if uploaded_file.size > 5 * 1024 * 1024:
        st.error("File size exceeds 5MB limit. Please upload a smaller file.")
    else:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(uploaded_file)
        
        # Chat input
        user_query = st.text_input("Ask a question based on the PDF content:")
        
        if st.button("Get Answer") and user_query:
            # Domo API Request
            payload = {
                "input": user_query,
                "model": "domo.domo_ai.domogpt-chat-small-v1:anthropic",
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
                st.success(result.get("output", "No response received."))
            else:
                st.error(f"Error: {response.status_code} - {response.text}")

