# app.py
import streamlit as st
from pdf_utils import extract_text_from_pdf
from rag_pipeline import build_vectorstore_from_text, load_rag_chain
import os

st.title("📘 자격증 요약 챗봇")

uploaded = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
question = st.text_input("궁금한 내용을 입력하세요")

if uploaded:
    file_path = f"temp/{uploaded.name}"
    os.makedirs("temp", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded.read())

    with st.spinner("PDF 처리 중..."):
        text = extract_text_from_pdf(file_path)
        build_vectorstore_from_text(text)
        st.success("문서 임베딩 완료!")

    rag = load_rag_chain()
    if question:
        answer = rag.run(question)
        st.write("🧠 Claude의 답변:")
        st.success(answer)
