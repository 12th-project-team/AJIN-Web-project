import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from vectorstore_utils import load_chroma_vectorstore
import os

def render(category_name: str):
    st.header(f"📌 {category_name} - 요약")

    base_path = os.path.join("chroma_db", category_name)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    subfolders = os.listdir(base_path)
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    selected_doc = st.selectbox("요약할 문서를 선택하세요", subfolders)

    try:
        vectordb = load_chroma_vectorstore(category_name, selected_doc)
    except Exception as e:
        st.error(f"벡터스토어 로드 실패: {e}")
        return

    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    query = st.text_input("요약할 주제를 입력하세요:", placeholder="예) 핵심 내용, 주요 키워드 등")

    if st.button("요약 실행"):
        if not query.strip():
            st.warning("요약할 주제를 입력해주세요.")
            return

        docs = retriever.get_relevant_documents(query)
        context = "\n".join([doc.page_content for doc in docs])

        prompt = f"""
주제 10개 정도로 나눠서 다음 내용을 간단히 3~5줄씩 요약해줘.
내용이 없으면 '내용 없음'이라고 해줘:

{context}
"""

        with st.spinner("📘 요약 중..."):
            result = llm.invoke([HumanMessage(content=prompt)])

        st.subheader("📘 요약 결과")
        st.write(result.content)
