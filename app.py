# app.py
import os
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd

# ------------------------------
# Load Gemini API Key
# ------------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("API key not found! Please set GEMINI_API_KEY in .env file.")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ------------------------------
# Helper: Extract Text from PDF/DOCX
# ------------------------------
def extract_text(file):
    try:
        text = ""
        if file.type == "application/pdf":
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = file.read().decode("utf-8", errors="ignore")
        if not text.strip():
            raise ValueError("No text found in the file.")
        return text
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

# ------------------------------
# Branding & Header
# ------------------------------
st.set_page_config(page_title="Answerly – AI Document Q&A", page_icon="🤖", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50;'>🤖 Answerly – AI Document Q&A</h1>
    <p style='text-align: center; color: #555;'>Upload your documents (PDF or DOCX), ask questions, and let AI give you instant answers.</p>
    """,
    unsafe_allow_html=True
)

st.write("---")

# Instructions
with st.expander("📌 How to Use Answerly"):
    st.markdown("""
    1. **Upload** a PDF or DOCX file.  
    2. **Type a question** about the document.  
    3. **Get an AI-generated answer** instantly.  
    4. **Check History Tab** to review previous Q&A for all files.
    """)

# ------------------------------
# Tabs for Q&A and History
# ------------------------------
tab1, tab2 = st.tabs(["💬 Ask AI", "📜 History"])

# Q&A Tab
with tab1:
    uploaded_file = st.file_uploader("Upload your document (PDF/DOCX):", type=["pdf", "docx"], help="Supported formats: PDF or DOCX.")
    question = st.text_input("Ask a question about the document:", placeholder="e.g., What is the summary of this document?")

    if uploaded_file and question:
        with st.spinner("🤖 Thinking... Please wait..."):
            content = extract_text(uploaded_file)
            if content:
                try:
                    prompt = f"Answer the following question based on the document:\n\nDocument:\n{content}\n\nQuestion: {question}"
                    response = model.generate_content(prompt)
                    st.subheader("Answer:")
                    st.write(response.text)

                    # Store Q&A in session state
                    if "qa_history" not in st.session_state:
                        st.session_state.qa_history = []
                    st.session_state.qa_history.append({
                        "file_name": uploaded_file.name,
                        "question": question,
                        "answer": response.text
                    })
                except Exception as api_err:
                    st.error(f"Error from AI: {api_err}")

# History Tab
with tab2:
    if "qa_history" in st.session_state and st.session_state.qa_history:
        st.subheader("📜 Previous Q&A")
        for qa in reversed(st.session_state.qa_history):
            st.markdown(f"**File:** {qa['file_name']}")
            st.markdown(f"**Q:** {qa['question']}")
            st.markdown(f"**A:** {qa['answer']}")
            st.write("---")

        # Download as CSV
        df = pd.DataFrame(st.session_state.qa_history)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Q&A History as CSV",
            data=csv,
            file_name="answerly_history.csv",
            mime="text/csv",
        )
    else:
        st.info("No history yet. Ask some questions first!")

# Footer
st.write("---")
st.markdown("<p style='text-align:center; color:grey;'>Built with ❤️ during Summer of AI 2025 Internship</p>", unsafe_allow_html=True)
