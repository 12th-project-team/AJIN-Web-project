import os
import re
import streamlit as st
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

# -------------------------
# 0. 환경 변수 로드
# -------------------------
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# -------------------------
# 1. PDF 문서 로드 및 전처리
# -------------------------
@st.cache_data
def load_documents():
    loader = PyMuPDFLoader("컴활2급.pdf")
    docs = loader.load()

    def clean_text(text):
        text = text.replace("\r", "")
        text = re.sub(r"[•●▪◦·]", " ", text)
        text = re.sub(r"[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣA-Za-z0-9.,!?\"'()\n<>:;\/\\\-+=&%#@ ]", "", text)
        return text.strip()

    for doc in docs:
        doc.page_content = clean_text(doc.page_content)

    return docs

documents = load_documents()

# -------------------------
# 2. 청크 분할 및 임베딩
# -------------------------
@st.cache_resource
def load_vectorstore():
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)

    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_api_key
    )

    faiss_path = "faiss_db"
    if not os.path.exists(faiss_path):
        vectordb = FAISS.from_documents(chunks, embedding_model)
        vectordb.save_local(faiss_path)
    else:
        vectordb = FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)

    return vectordb

vectordb = load_vectorstore()

# -------------------------
# 3. LLM + 검색 QA 체인
# -------------------------
llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # 또는 gpt-4 사용 가능
    temperature=0,
    openai_api_key=openai_api_key
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=False
)

# -------------------------
# 4. Streamlit UI 
# -------------------------
st.set_page_config(page_title="컴활 2급 챗봇", layout="wide")
st.title("컴활 2급 챗봇")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.chat_input("궁금한 내용을 입력하세요!")

if user_query:
    st.session_state.chat_history.append({"role": "user", "text": user_query})

    with st.spinner("답변 생성 중..."):
        response = qa_chain.run(user_query)

    st.session_state.chat_history.append({"role": "assistant", "text": response})

# 대화 내용 표시
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["text"])
