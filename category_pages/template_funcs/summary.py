# category_pages/template_funcs/summary.py

import streamlit as st
from vectorstore_utils import load_chroma_vectorstore
from langchain_openai import ChatOpenAI
import os

def render(category_name: str):
    st.header(f"📌 {category_name} - 요약")
    base_path = os.path.join("chroma_db", category_name)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    subfolders = [
        d for d in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, d))
    ]
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다.")
        return

    doc = st.selectbox("요약할 문서를 선택하세요", subfolders, key=f"summary_doc_{category_name}")
    topic = st.text_input("요약할 주제를 입력하세요:", key=f"summary_topic_{category_name}", placeholder="예) 핵심 내용, 키워드 등")

    if st.button("요약 실행", key=f"summary_run_{category_name}"):
        if not topic.strip():
            st.warning("주제를 입력해주세요.")
            return

        try:
            vectordb = load_chroma_vectorstore(category_name, doc)
            retriever = vectordb.as_retriever(search_kwargs={"k": 10})
            docs = retriever.get_relevant_documents(topic)
            context = "\n\n".join([d.page_content for d in docs])

            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)
            prompt = f"아래 내용을 '{topic}' 중심으로 요약해줘:\n\n{context}"
            resp = llm.invoke(prompt)
            summary = getattr(resp, "content", resp)
            st.markdown("**요약 결과**")
            st.write(summary)
        except Exception as e:
            st.error(f"요약 중 오류 발생: {e}")
