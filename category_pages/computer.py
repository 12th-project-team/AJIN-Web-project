import streamlit as st
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore, list_chroma_files
from category_pages.computer_funcs import preview  # ✅ 미리보기 모듈 그대로 사용

CATEGORY_NAME = "컴퓨터활용능력"
UPLOAD_DIR = "uploaded_pdfs"

def render():
    st.header(f"📁 {CATEGORY_NAME}")

    # 📤 PDF 업로드
    uploaded_file = st.file_uploader("📤 PDF 업로드", type=["pdf"], key="upload_computer")

    if uploaded_file:
        with st.spinner("📄 PDF 분석 및 저장 중..."):
            filename = Path(uploaded_file.name).stem  # 확장자 제거
            pdf_path = os.path.join(UPLOAD_DIR, f"{filename}.pdf")

            # 저장
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 분석 및 벡터 저장
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            save_path = save_chroma_vectorstore(docs, CATEGORY_NAME, filename)
            st.success(f"✅ 저장 완료: `{save_path}`")

    # 📑 탭 구성
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

    # chroma vectorstore에서 저장된 폴더명 가져오기
    subfolders = list_chroma_files(CATEGORY_NAME)

    if subfolders:
        for folder in subfolders:
            preview.render(folder)  # 🔁 폴더명 기준으로 미리보기 실행
    else:
        st.info("❗ 저장된 문서가 없습니다.")
