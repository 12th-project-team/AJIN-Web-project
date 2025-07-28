import streamlit as st

def render(category_name, retriever, llm):
    st.info(f"🤖 챗봇 탭 - {category_name}")

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
            result = llm.invoke(prompt)
        st.subheader("🤖 답변")
        st.write(result.content)
