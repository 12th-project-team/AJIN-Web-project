# category_pages/computer_funcs/exam.py

import streamlit as st
import os
from langchain_openai import ChatOpenAI
from vectorstore_utils import load_chroma_vectorstore

CATEGORY_NAME = "컴퓨터활용능력"

def render():
    st.header(f"📄 {CATEGORY_NAME} - 기출문제 생성")

    base_path = os.path.join("chroma_db", CATEGORY_NAME)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    subfolders = os.listdir(base_path)
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    selected_doc = st.selectbox("기출문제를 생성할 문서를 선택하세요", subfolders)

    try:
        vectordb = load_chroma_vectorstore(CATEGORY_NAME, selected_doc)
    except Exception as e:
        st.error(f"벡터스토어 로드 실패: {e}")
        return

    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    query = st.text_input("기출문제 생성 주제를 입력하세요:")

    if st.button("기출문제 생성"):
        if not query.strip():
            st.warning("주제를 입력해주세요.")
            return

        docs = retriever.get_relevant_documents(query)
        context = "\n".join([doc.page_content for doc in docs])

        prompt = f"""
다음 내용을 바탕으로 객관식 기출문제 10개를 만들어줘.
각 문제는 보기 4개, 정답, 그리고 해설을 포함해줘:

{context}
"""

        with st.spinner("📄 기출문제 생성 중..."):
            result = llm(prompt)
        st.subheader("📄 생성된 기출문제")
        st.write(result.content)
