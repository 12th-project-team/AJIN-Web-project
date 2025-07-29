# category_pages/template_funcs/upload.py

import streamlit as st
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore

UPLOAD_DIR = "uploaded_pdfs"

def render(category_name: str):
    st.subheader("📤 PDF 업로드")
    uploaded_file = st.file_uploader(
        label=f"{category_name} PDF 업로드",
        type=["pdf"],
        key=f"upload_{category_name}"
    )
    if uploaded_file:
        with st.spinner("📄 PDF 분석 및 저장 중..."):
            filename = Path(uploaded_file.name).stem
            pdf_path = os.path.join(UPLOAD_DIR, f"{filename}.pdf")
            # 디렉터리 없으면 생성
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # 벡터스토어 저장
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            save_path = save_chroma_vectorstore(docs, category_name, filename)
            st.success(f"✅ 저장 완료: `{save_path}`")
