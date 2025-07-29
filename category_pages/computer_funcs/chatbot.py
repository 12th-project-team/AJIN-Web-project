import os
import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CHAT_STYLE = """ 
<style>
.chat-container {
  max-width: 700px;
  margin: 0 auto 30px;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}
.bubble {
  padding: 12px 18px;
  border-radius: 20px;
  margin: 8px 0;
  max-width: 80%;
  word-wrap: break-word;
  font-size: 16px;
  line-height: 1.4;
  display: inline-block;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.user {
  background-color: #DCF8C6;
  float: right;
  clear: both;
  text-align: right;
}
.bot {
  background-color: #F1F0F0;
  float: left;
  clear: both;
  text-align: left;
}
.clearfix::after {
  content: "";
  clear: both;
  display: table;
}
h2 {
  font-weight: 700;
  font-size: 1.8rem;
  margin-bottom: 20px;
  color: #333;
}
.selectbox-label {
  font-weight: 600;
  margin-bottom: 5px;
  color: #444;
}
</style>
"""

custom_prompt = PromptTemplate(
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
    st.markdown(CHAT_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for question, answer in chat_history:
        st.markdown(
            '<div class="clearfix"><div class="bubble user">👤 ' 
            + question + '</div></div>', 
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="clearfix"><div class="bubble bot">🤖 ' 
            + answer + '</div></div>', 
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

def handle_submit(category_name: str):
    user_question = st.session_state.chatbot_question_input
    if not user_question.strip():
        st.warning("❗ 질문을 입력해주세요.")
        return
    
    base_path = os.path.join("chroma_db", category_name)
    selected_doc = st.session_state.chatbot_doc_select

    with st.spinner("⏳ 답변 생성 중... 잠시만 기다려주세요..."):
        vectordb = Chroma(
            persist_directory=os.path.join(base_path, selected_doc),
            embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        )
        retriever = vectordb.as_retriever(search_type="similarity", k=3)
        llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-4o-mini",
            openai_api_key=OPENAI_API_KEY
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": custom_prompt}
        )
        answer = qa_chain.run(user_question)
        st.session_state.chat_history.append((user_question, answer))
    
    st.session_state.chatbot_question_input = ""

def render(category_name: str):
    st.markdown(CHAT_STYLE, unsafe_allow_html=True)
    st.header(f"💬 {category_name} 문서 기반 챗봇")

    base_path = os.path.join("chroma_db", category_name)
    if not os.path.exists(base_path):
        st.info("❗ 저장된 문서가 없습니다.")
        return

    subfolders = [
        f for f in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, f))
    ]
    if not subfolders:
        st.info("❗ 저장된 문서가 없습니다.")
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.markdown(
        '<label class="selectbox-label">📂 질문할 문서를 선택하세요</label>',
        unsafe_allow_html=True
    )
    st.selectbox(
        label="",
        options=subfolders,
        key="chatbot_doc_select"
    )

    if st.session_state.chat_history:
        render_chat_history(st.session_state.chat_history)

    st.text_input(
        label="❓ 질문을 입력하세요",
        key="chatbot_question_input",
        placeholder="질문을 입력하고 Enter 키를 누르세요",
        on_change=lambda: handle_submit(category_name)
    )
