import streamlit as st

def render(category_name, retriever, llm):
    st.info(f"📄 기출문제 탭 - {category_name}")
    
    query = st.text_input("기출문제 생성 주제를 입력하세요:")

    def get_context(query):
        docs = retriever.get_relevant_documents(query)
        return "\n".join([doc.page_content for doc in docs])
    
    if st.button("기출문제 생성") and query:
        context = get_context(query)
        with st.spinner("기출문제 생성 중..."):
            prompt = f"""
다음 내용을 기반으로 컴활 1급 필기 시험에 나올 수 있는 객관식 문제 10개를 만들어줘.
각 문제는 보기, 정답과 구체적인 해설을 포함해.

{context}
"""
            result = llm.invoke(prompt)
        st.subheader("📄 기출문제")
        st.write(result.content)
