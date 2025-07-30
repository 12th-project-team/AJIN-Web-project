# category_pages/template_funcs/upload.py
# (또는 category_pages/computer_funcs/upload.py)

import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore, delete_chroma_vectorstore

def render(category_name: str):
    # 1) 문서 유형 선택
    doc_type = st.radio(
        "문서 유형을 선택하세요",
        ["이론", "기출문제"],
        horizontal=True,
        key=f"doctype_{category_name}"
    )

    # 2) PDF 업로드
    uploaded_file = st.file_uploader(
        "📤 PDF 업로드",
        type=["pdf"],
        key=f"upload_{category_name}"
    )

    if uploaded_file:
        with st.spinner("PDF 분석 및 저장 중..."):
            base_dir = os.path.join("uploaded_pdfs", doc_type)
            os.makedirs(base_dir, exist_ok=True)
            pdf_path = os.path.join(base_dir, uploaded_file.name)

            # 파일 저장
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # PDF 로딩 → 문서 리스트 생성
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            filename = os.path.splitext(uploaded_file.name)[0]

            # Chroma 벡터스토어 저장
            save_path = save_chroma_vectorstore(docs, category_name, filename)
            st.success(f"✅ `{doc_type}` 문서 저장 완료: `{save_path}`")

            # 간단 미리보기
            with st.expander("👀 문서 미리보기", expanded=False):
                for page in docs[:3]:
                    st.markdown(f"**- {page.metadata['page']}페이지**")
                    st.write(page.page_content[:500] + ("..." if len(page.page_content) > 500 else ""))

    # 3) 저장된 문서 목록 & 삭제 UI
    st.markdown("---")
    st.markdown(f"### 📂 `{doc_type}` 문서 목록")
    folder_path = os.path.join("uploaded_pdfs", doc_type)

    if os.path.exists(folder_path):
        for fname in os.listdir(folder_path):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"- 📄 `{fname}`")
            with col2:
                if st.button("🗑", key=f"delete_{fname}_{category_name}"):
                    file_id = os.path.splitext(fname)[0]
                    delete_chroma_vectorstore(category_name, file_id, doc_type)
                    st.success("삭제 완료!")
                    st.rerun()
    else:
        st.info("📭 아직 업로드된 문서가 없습니다.")
