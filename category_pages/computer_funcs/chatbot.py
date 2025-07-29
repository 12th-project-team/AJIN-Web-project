import streamlit as st
from langchain_openai import ChatOpenAI
from vectorstore_utils import load_chroma_vectorstore
import os

CATEGORY_NAME = "컴퓨터활용능력"

def render():
    st.header(f"🤖 {CATEGORY_NAME} - 문서 기반 챗봇")

    base_path = os.path.join("chroma_db", CATEGORY_NAME)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    subfolders = os.listdir(base_path)
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다. 먼저 PDF를 업로드하세요.")
        return

    selected_doc = st.selectbox("질문할 문서를 선택하세요", subfolders)

    try:
        vectordb = load_chroma_vectorstore(CATEGORY_NAME, selected_doc)
    except Exception as e:
        st.error(f"벡터스토어 로드 실패: {e}")
        return

    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    query = st.text_input("질문을 입력하세요:")

    def get_context(query):
        docs = retriever.get_relevant_documents(query)
        return "\n".join([doc.page_content for doc in docs])

    if st.button("답변 생성") and query:
        context = get_context(query)
        with st.spinner("답변 생성 중..."):
            prompt = f"""
아래 내용을 바탕으로 사용자의 질문에 정확하고 간결하게 답변해 주세요.

[질문]
{query}

[문서 내용]
{context}
"""
            response = llm.invoke(prompt)

        st.subheader("🤖 답변")
        if hasattr(response, "content"):
            st.write(response.content)
        else:
            st.write(response)  # fallback for str or 기타 객체
