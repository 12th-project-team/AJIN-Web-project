import streamlit as st
import os
import fitz  # PyMuPDF
from io import BytesIO

def render(folder_name: str):
    pdf_path = os.path.join("uploaded_pdfs", f"{folder_name}.pdf")

    if not os.path.exists(pdf_path):
        st.warning("⚠️ PDF 원본 파일이 존재하지 않습니다.")
        return

    toggle_key = f"toggle_{folder_name}"
    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = False

    # 버튼 클릭 시 토글
    if st.button(f"📄 {folder_name}", key=f"button_{folder_name}"):
        st.session_state[toggle_key] = not st.session_state[toggle_key]

    if st.session_state[toggle_key]:
        st.markdown("---")
        st.subheader(f"📖 미리보기: {folder_name} (앞 10페이지)")

        # 다운로드 버튼
        try:
            with open(pdf_path, "rb") as f:
                file_bytes = f.read()
            st.download_button(
                label="⬇️ PDF 다운로드 (전체)",
                data=file_bytes,
                file_name=f"{folder_name}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"원본 파일 읽기 오류: {e}")

        # PDF -> 이미지 슬라이더로 한 장씩 보기
        try:
            doc = fitz.open(pdf_path)
            max_pages = min(len(doc), 10)
            # 슬라이더로 페이지 선택
            page_num = st.slider("페이지", min_value=1, max_value=max_pages, value=1, step=1, key=f"page_slider_{folder_name}")
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
            img_bytes = BytesIO(pix.tobytes("png"))
            st.image(img_bytes, caption=f"{page_num}페이지", use_container_width=True)  # use_container_width=True로 경고 해결
            doc.close()
        except Exception as e:
            st.error(f"PDF 미리보기 이미지 변환 오류: {e}")
