import streamlit as st
import os
import base64

def render(category_name: str):
    """
    uploaded_pdfs/<category_name>.pdf 파일을 다운로드 및 인라인 뷰어로 표시합니다.
    """
    pdf_path = os.path.join("uploaded_pdfs", f"{category_name}.pdf")

    if not os.path.exists(pdf_path):
        st.warning("⚠️ PDF 원본 파일이 존재하지 않습니다.")
        return

    toggle_key = f"toggle_{category_name}"
    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = False

    if st.button(f"📄 {category_name}", key=f"btn_preview_{category_name}"):
        st.session_state[toggle_key] = not st.session_state[toggle_key]

    if st.session_state[toggle_key]:
        st.markdown("---")
        st.subheader(f"📖 미리보기: {category_name}")

        try:
            with open(pdf_path, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")
            return

        # 다운로드 버튼
        st.download_button(
            label="⬇️ PDF 다운로드",
            data=file_bytes,
            file_name=f"{category_name}.pdf",
            mime="application/pdf"
        )

        # 인라인 뷰어
        try:
            b64 = base64.b64encode(file_bytes).decode("utf-8")
            iframe = (
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="800px" '
                f'style="border:1px solid #ccc; border-radius:8px;"></iframe>'
            )
            st.markdown(iframe, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"PDF 표시 오류: {e}")
