import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from vectorstore_utils import save_chroma_vectorstore, delete_chroma_vectorstore

def handle_upload(category_name):
    doc_type = st.radio("문서 유형을 선택하세요", ["이론", "기출문제"], horizontal=True, key=f"doctype_{category_name}")
    uploaded_file = st.file_uploader("📤 PDF 업로드", type=["pdf"], key=f"upload_{category_name}")

    if uploaded_file:
        with st.spinner("PDF 분석 및 저장 중..."):
            base_dir = os.path.join("uploaded_pdfs", doc_type)
            os.makedirs(base_dir, exist_ok=True)
            pdf_path = os.path.join(base_dir, uploaded_file.name)

            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            filename = uploaded_file.name.split(".")[0]
            save_path = save_chroma_vectorstore(docs, category_name, filename)

            st.success(f"✅ `{doc_type}` 문서 저장 완료: `{save_path}`")

            with st.expander("👀 문서 미리보기", expanded=False):
                for page in docs[:3]:
                    st.markdown(f"**- {page.metadata['page']}페이지**")
                    st.write(page.page_content[:500] + ("..." if len(page.page_content) > 500 else ""))

    # 삭제 UI
    st.markdown("---")
    st.markdown(f"### 📂 `{doc_type}` 문서 목록")
    folder_path = os.path.join("uploaded_pdfs", doc_type)
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        for f in files:
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"- 📄 `{f}`")
            with col2:
                if st.button("🗑", key=f"delete_{f}_{category_name}"):
                    filename = f.split(".")[0]
                    delete_chroma_vectorstore(category_name, filename, doc_type)
                    st.success("삭제 완료!")
                    st.experimental_rerun()
    else:
        st.info("📭 아직 업로드된 문서가 없습니다.")
