import os
import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 카카오톡 말풍선 스타일 CSS
CHAT_CSS = """
<style>
.chat-container { max-width:700px; margin:0 auto 30px; }
.bubble { padding:12px 18px; border-radius:20px; margin:8px 0; display:inline-block; }
.user { background:#DCF8C6; float:right; clear:both; }
.bot { background:#F1F0F0; float:left; clear:both; }
.clearfix::after { content:""; display:table; clear:both; }
</style>
"""

# 1) 커스텀 프롬프트
CUSTOM_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
아래 문서 내용을 참고하여 질문에 친절하고 내용중심적으로 답변해 주세요.

문서 내용:
{context}

질문:
{question}

답변:
"""
)

def render_chat_history(chat_history):
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for q, a in chat_history:
        st.markdown(f'<div class="clearfix"><div class="bubble user">👤 {q}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="clearfix"><div class="bubble bot">🤖 {a}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def handle_submit(category_name: str):
    user_q = st.session_state[f"chat_input_{category_name}"]
    if not user_q.strip():
        st.warning("질문을 입력해주세요.")
        return

    base = os.path.join("chroma_db", category_name)
    selected = st.session_state[f"chat_doc_{category_name}"]
    vectordb = Chroma(
        persist_directory=os.path.join(base, selected),
        embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    )
    retriever = vectordb.as_retriever(search_type="similarity", k=3)
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": CUSTOM_PROMPT}
    )
    answer = qa.run(user_q)
    st.session_state.chat_history.append((user_q, answer))
    # 입력창 비우기
    st.session_state[f"chat_input_{category_name}"] = ""

def render(category_name: str):
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    st.header(f"💬 {category_name} 문서 기반 챗봇")

    base = os.path.join("chroma_db", category_name)
    if not os.path.exists(base):
        st.info("❗ 저장된 문서가 없습니다.")
        return

    subfolders = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다.")
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.selectbox(
        "📂 질문할 문서를 선택하세요",
        options=subfolders,
        key=f"chat_doc_{category_name}"
    )

    if st.session_state.chat_history:
        render_chat_history(st.session_state.chat_history)

    st.text_input(
        "❓ 질문을 입력하세요",
        key=f"chat_input_{category_name}",
        on_change=lambda: handle_submit(category_name)
    )
