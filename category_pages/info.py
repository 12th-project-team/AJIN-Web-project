# category_pages/info.py
import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore, list_chroma_files

CATEGORY_NAME = "정보처리기사"

def render():
    st.header(f"📁 {CATEGORY_NAME}")
    uploaded_file = st.file_uploader("📤 PDF 업로드", type=["pdf"], key="upload_info")

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
        st.info("요점정리 탭 내용")
    with tab2:
        st.info("퀴즈 탭 내용")
    with tab3:
        st.info("기출문제 탭 내용")
    with tab4:
        st.info("챗봇 탭 내용")

    st.markdown("---")
    st.subheader("📚 저장된 문서 목록")
    subfolders = list_chroma_files(CATEGORY_NAME)
    if subfolders:
        for folder in subfolders:
            st.markdown(f"🔹 `{folder}`")
    else:
        st.info("❗ 저장된 문서가 없습니다.")