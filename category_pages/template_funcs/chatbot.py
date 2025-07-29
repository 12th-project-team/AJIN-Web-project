import os
import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 간단한 말풍선 스타일
CHAT_CSS = """
<style>
.bubble { padding:8px 12px; border-radius:12px; margin:4px 0; }
.user { background:#DCF8C6; text-align:right; }
.bot  { background:#F1F0F0; text-align:left; }
</style>
"""

# 커스텀 QA 프롬프트
PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
문서 내용을 참고하여 질문에 답변해 주세요.

문서:
{context}

질문:
{question}

답변:
"""
)

def render(category_name: str):
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    st.header(f"💬 {category_name} - 문서 기반 챗봇")

    base_path = os.path.join("chroma_db", category_name)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다.")
        return

    docs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    if not docs:
        st.info("❗ 저장된 문서가 없습니다.")
        return

    # 문서 선택
    selected = st.selectbox("질문할 문서를 선택하세요", docs, key=f"chat_doc_{category_name}")

    # 채팅 기록 초기화
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 기록 렌더링
    for q,a in st.session_state.chat_history:
        st.markdown(f"<div class='bubble user'>👤 {q}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble bot'>🤖 {a}</div>", unsafe_allow_html=True)

    # 질문 입력
    question = st.text_input("질문을 입력하세요", key=f"chat_input_{category_name}")
    if st.button("전송", key=f"chat_send_{category_name}") and question:
        try:
            # 벡터 불러오기
            vectordb = Chroma(
                persist_directory=os.path.join(base_path, selected),
                embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            )
            retriever = vectordb.as_retriever(search_type="similarity", k=3)
            llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
            chain = RetrievalQA.from_chain_type(
                llm=llm, chain_type="stuff", retriever=retriever, chain_type_kwargs={"prompt": PROMPT}
            )
            answer = chain.run(question)
            st.session_state.chat_history.append((question, answer))
        except Exception as e:
            st.error(f"챗봇 오류: {e}")
