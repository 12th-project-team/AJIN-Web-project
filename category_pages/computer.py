import streamlit as st
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore, list_chroma_files
from category_pages.computer_funcs.summary import render as render_summary
from category_pages.computer_funcs.quiz import render as render_quiz
from category_pages.computer_funcs.exam import render as render_exam
from category_pages.computer_funcs.chatbot import render as render_chatbot
from category_pages.computer_funcs.preview import render as preview  # ⚡️여기서 단일 함수로 import

CATEGORY_NAME = "컴퓨터활용능력"
UPLOAD_DIR = "uploaded_pdfs"

def render():
    st.header(f"📁 {CATEGORY_NAME}")

    # 📤 PDF 업로드
    uploaded_file = st.file_uploader("📤 PDF 업로드", type=["pdf"], key="upload_computer")
    if uploaded_file:
        with st.spinner("📄 PDF 분석 및 저장 중..."):
            filename = Path(uploaded_file.name).stem
            pdf_path = os.path.join(UPLOAD_DIR, f"{filename}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            save_path = save_chroma_vectorstore(docs, CATEGORY_NAME, filename)
            st.success(f"✅ 저장 완료: `{save_path}`")

    # 📑 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📌 요점정리", "✅ 퀴즈", "📄 기출문제", "🤖 챗봇"
    ])
    with tab1:
        render_summary(CATEGORY_NAME)
    with tab2:
        render_quiz(CATEGORY_NAME)
    with tab3:
        render_exam(CATEGORY_NAME)
    with tab4:
        render_chatbot(CATEGORY_NAME)

    st.markdown("---")
    st.subheader("📚 저장된 문서 목록")

    subfolders = list_chroma_files(CATEGORY_NAME)
    if subfolders:
        for folder in subfolders:
            preview(folder)   # ◀️ .render() 가 아니라 함수 자체를 호출합니다
    else:
        st.info("❗ 저장된 문서가 없습니다.")
