# app.py

import os
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd

# -----------------------------
# Load Gemini API Key
# -----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("API key not found! Set GEMINI_API_KEY in .env file.")
    st.stop()

genai.configure(api_key=API_KEY)

# Latest supported model
model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# Extract text from file
# -----------------------------
def extract_text(file):

    text = ""

    if file.type == "application/pdf":
        pdf = PdfReader(file)

        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)

        for para in doc.paragraphs:
            text += para.text + "\n"

    return text


# -----------------------------
# Split text into chunks
# -----------------------------
def split_text(text, chunk_size=1000, overlap=200):

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# -----------------------------
# Retrieve relevant chunks
# -----------------------------
def get_relevant_chunks(chunks, question, top_k=3):

    question_words = set(question.lower().split())

    scored_chunks = []

    for chunk in chunks:

        chunk_words = set(chunk.lower().split())

        score = len(question_words.intersection(chunk_words))

        scored_chunks.append((score, chunk))

    scored_chunks.sort(reverse=True)

    return [chunk for score, chunk in scored_chunks[:top_k]]


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Answerly – AI Document Q&A",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# Header
# -----------------------------
st.markdown(
"""
<h1 style='text-align:center; color:#4CAF50;'>🤖 Answerly – AI Document Q&A</h1>
<p style='text-align:center;'>Upload a document, ask questions, and get AI answers instantly.</p>
""",
unsafe_allow_html=True
)

st.write("---")

# -----------------------------
# Instructions
# -----------------------------
with st.expander("📌 How to Use Answerly"):

    st.markdown("""
1. Upload a **PDF or DOCX**
2. Ask a question about the document
3. AI generates an answer
4. View previous Q&A in History tab
""")


# -----------------------------
# Tabs
# -----------------------------
tab1, tab2 = st.tabs(["💬 Ask AI", "📜 History"])


# -----------------------------
# Ask AI Tab
# -----------------------------
with tab1:

    uploaded_file = st.file_uploader(
        "Upload your document",
        type=["pdf", "docx"]
    )

    question = st.text_input("Ask a question about the document")

submit = st.button("🔍 Get Answer")

if uploaded_file and question and submit:

        with st.spinner("🤖 Thinking..."):

            text = extract_text(uploaded_file)

            if text.strip() == "":
                st.error("No text could be extracted.")
            else:

                chunks = split_text(text)

                relevant_chunks = get_relevant_chunks(
                    chunks,
                    question
                )

                context = "\n\n".join(relevant_chunks)

                prompt = f"""
Answer the question using ONLY the context below.

Context:
{context}

Question:
{question}
"""

                try:

                    response = model.generate_content(prompt)

                    answer = response.text

                    st.subheader("Answer")
                    st.write(answer)

                    # Store history
                    if "qa_history" not in st.session_state:
                        st.session_state.qa_history = []

                    st.session_state.qa_history.append({
                        "file": uploaded_file.name,
                        "question": question,
                        "answer": answer
                    })

                except Exception as e:

                    st.error(f"AI Error: {e}")


# -----------------------------
# History Tab
# -----------------------------
with tab2:

    if "qa_history" in st.session_state and st.session_state.qa_history:

        st.subheader("📜 Previous Questions")

        for item in reversed(st.session_state.qa_history):

            st.markdown(f"**File:** {item['file']}")
            st.markdown(f"**Q:** {item['question']}")
            st.markdown(f"**A:** {item['answer']}")
            st.write("---")

        df = pd.DataFrame(st.session_state.qa_history)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Q&A History",
            csv,
            "answerly_history.csv",
            "text/csv"
        )

    else:

        st.info("No questions asked yet.")


# -----------------------------
# Footer
# -----------------------------
st.write("---")

st.markdown(
"<p style='text-align:center; color:grey;'>Built with ❤️ using Streamlit and Google Gemini AI</p>",
unsafe_allow_html=True
)