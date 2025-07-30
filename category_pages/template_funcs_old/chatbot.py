# category_pages/template_funcs/chatbot.py

import os
import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CHAT_STYLE = """<style>
.chat-container { max-width:700px; margin:0 auto; }
.bubble { padding:12px; border-radius:20px; margin:8px 0; max-width:80%; display:inline-block; }
.user { background:#DCF8C6; float:right; clear:both; }
.bot { background:#F1F0F0; float:left; clear:both; }
.clearfix::after { content:""; clear:both; display:table; }
</style>"""

custom_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
아래 문서 내용을 참고하여 답변해 주세요.

문서 내용:
{context}

질문:
{question}

답변:
"""
)

def render(category_name: str):
    st.markdown(CHAT_STYLE, unsafe_allow_html=True)
    st.header(f"🤖 {category_name} - 챗봇")

    base = os.path.join("chroma_db", category_name)
    if not os.path.exists(base):
        st.info("❗ 저장된 문서가 없습니다.")
        return

    docs = [
        d for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d))
    ]
    if not docs:
        st.info("❗ 저장된 문서가 없습니다.")
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    doc = st.selectbox("질문할 문서를 선택하세요", docs, key=f"chat_doc_{category_name}")
    for q,a in st.session_state.chat_history:
        st.markdown(f'<div class="clearfix"><div class="bubble user">👤 {q}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="clearfix"><div class="bubble bot">🤖 {a}</div></div>', unsafe_allow_html=True)

    question = st.text_input(
        "질문을 입력하세요",
        key=f"chat_input_{category_name}",
        placeholder="Enter 키로 전송",
        on_change=lambda: _on_submit(category_name)
    )

def _on_submit(category_name: str):
    user_q = st.session_state[f"chat_input_{category_name}"]
    if not user_q.strip():
        return

    base = os.path.join("chroma_db", category_name, st.session_state[f"chat_doc_{category_name}"])
    store = Chroma(
        persist_directory=base,
        embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    )
    retriever = store.as_retriever(search_type="similarity", k=3)
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)
    qa = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever,
        chain_type_kwargs={"prompt": custom_prompt}
    )
    answer = qa.run(user_q)
    st.session_state.chat_history.append((user_q, answer))
    st.session_state[f"chat_input_{category_name}"] = ""
