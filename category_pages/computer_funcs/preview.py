# category_pages/computer_funcs/preview.py
import streamlit as st
import os

def render(folder_name):
    if st.button(f"📄 {folder_name}", key=f"preview_{folder_name}"):
        pdf_path = os.path.join("uploaded_pdfs", f"{folder_name}.pdf")
        if os.path.exists(pdf_path):
            st.subheader(f"📖 미리보기: {folder_name}")
            st.download_button("PDF 다운로드", data=open(pdf_path, "rb"), file_name=f"{folder_name}.pdf")
            with open(pdf_path, "rb") as f:
                base64_pdf = f.read()
                pdf_display = f"<iframe src='data:application/pdf;base64,{base64_pdf.decode('latin1')}' width='100%' height='600' type='application/pdf'></iframe>"
                st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.warning("⚠️ PDF 원본 파일이 존재하지 않습니다.")