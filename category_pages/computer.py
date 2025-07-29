import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore, list_chroma_files
from category_pages.computer_funcs import preview  
from category_pages.computer_funcs.summary import render as render_summary
from category_pages.computer_funcs.quiz import render as render_quiz
from category_pages.computer_funcs.exam import render as render_exam
from category_pages.computer_funcs.chatbot import render as render_chatbot

CATEGORY_NAME = "컴퓨터활용능력"

def render():
    st.header(f"📁 {CATEGORY_NAME}")
    uploaded_file = st.file_uploader("📤 PDF 업로드", type=["pdf"], key="upload_computer")

    if uploaded_file:
        with st.spinner("PDF 분석 및 저장 중..."):
            pdf_path = os.path.join("uploaded_pdfs", uploaded_file.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            filename = uploaded_file.name.split(".")[0]
            save_path = save_chroma_vectorstore(docs, CATEGORY_NAME, filename)
            st.success(f"✅ 저장 완료: `{save_path}`")

    tab1, tab2, tab3, tab4 = st.tabs(["📌 요점정리", "✅ 퀴즈", "📄 기출문제", "🤖 챗봇"])
    with tab1:
        render_summary()
    with tab2:
        render_quiz()
    with tab3:
        render_exam()
    with tab4:
        render_chatbot()

    st.markdown("---")
    st.subheader("📚 저장된 문서 목록")
    subfolders = list_chroma_files(CATEGORY_NAME)

    if subfolders:
        for folder in subfolders:
            preview.render(folder)  # 🔁 버튼 클릭시 미리보기 포함
    else:
        st.info("❗ 저장된 문서가 없습니다.")
