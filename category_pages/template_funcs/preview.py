# category_pages/template_funcs/preview.py

import streamlit as st
import os
import base64

def render(category_name: str):
    """
    uploaded_pdfs/<category_name>/<document_name>.pdf 단일 파일이 아니라,
    chroma_db/<category_name>/<document_name> 폴더 리스트의 각 document_name 기준으로 preview 합니다.
    """
    base_folder = os.path.join("chroma_db", category_name)
    if not os.path.exists(base_folder):
        return

    # vectordb 저장 폴더명을 PDF 파일명으로 간주
    subfolders = [
        d for d in os.listdir(base_folder)
        if os.path.isdir(os.path.join(base_folder, d))
    ]
    if not subfolders:
        return

    st.subheader("📚 저장된 문서 목록")
    for doc_name in subfolders:
        pdf_path = os.path.join("uploaded_pdfs", f"{doc_name}.pdf")
        toggle_key = f"toggle_{category_name}_{doc_name}"
        if toggle_key not in st.session_state:
            st.session_state[toggle_key] = False

        if st.button(f"📄 {doc_name}", key=f"btn_preview_{category_name}_{doc_name}"):
            st.session_state[toggle_key] = not st.session_state[toggle_key]

        if st.session_state[toggle_key]:
            if not os.path.exists(pdf_path):
                st.warning("⚠️ PDF 원본 파일이 존재하지 않습니다.")
                continue

            st.markdown("---")
            st.subheader(f"📖 미리보기: {doc_name}")

            with open(pdf_path, "rb") as f:
                data = f.read()

            st.download_button(
                label="⬇️ PDF 다운로드",
                data=data,
                file_name=f"{doc_name}.pdf",
                mime="application/pdf"
            )

            # inline viewer
            b64 = base64.b64encode(data).decode("utf-8")
            iframe = (
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="800px" '
                f'style="border:1px solid #ccc; border-radius:8px;"></iframe>'
            )
            st.markdown(iframe, unsafe_allow_html=True)
