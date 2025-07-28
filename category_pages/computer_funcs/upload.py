# category_pages/computer_funcs/upload.py
import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore

def handle_upload(category_name):
    uploaded_file = st.file_uploader("📤 PDF 업로드", type=["pdf"], key=f"upload_{category_name}")
    if uploaded_file:
        with st.spinner("PDF 분석 및 저장 중..."):
            os.makedirs("uploaded_pdfs", exist_ok=True)
            pdf_path = os.path.join("uploaded_pdfs", uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            filename = uploaded_file.name.split(".")[0]
            save_path = save_chroma_vectorstore(docs, category_name, filename)
            st.success(f"✅ 저장 완료: `{save_path}`")