import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pathlib import Path
import os
from dotenv import load_dotenv

# --- 환경변수 로드 ---
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("❌ OpenAI API 키가 환경변수에 없습니다. .env 파일을 확인하세요.")
    st.stop()

# --- 경로 설정 ---
pdf_path = Path(r"C:\woohyun\AJIN-12th-project\data\컴활1급.pdf")
save_dir = Path.cwd() / "faiss_db"
save_dir.mkdir(parents=True, exist_ok=True)

# --- 벡터스토어 생성 함수 ---
@st.cache_data(show_spinner=True)
def create_vectorstore():
    if not pdf_path.exists():
        st.error(f"PDF 파일이 없습니다: {pdf_path}")
        st.stop()

    loader = PyPDFLoader(str(pdf_path))
    all_docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    split_docs = text_splitter.split_documents(all_docs)

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(folder_path=str(save_dir), index_name="index")
    return vectorstore

# --- 벡터스토어 로드 함수 ---
@st.cache_resource(show_spinner=True)
def load_vectorstore():
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.load_local(
        str(save_dir),
        embeddings,
        index_name="index",
        allow_dangerous_deserialization=True
    )
    return vectorstore

# --- 메인 ---
st.title("📚 컴활1급 PDF 기반 질의응답 챗봇")

# 벡터스토어가 이미 있으면 불러오기, 없으면 생성
if not (save_dir / "index.faiss").exists():
    st.info("벡터스토어가 없습니다. PDF를 기반으로 벡터스토어를 생성합니다. 잠시만 기다려주세요...")
    vectorstore = create_vectorstore()
    st.success("벡터스토어 생성 완료!")
else:
    vectorstore = load_vectorstore()

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

prompt_template = """
당신은 친절하고 유능한 전문가입니다. 다음은 사용자의 질문과 관련된 참고 문서입니다:

{context}

질문: {question}

참고 문서를 기반으로 질문에 정확하게 답하세요. 모르는 내용은 추측하지 마세요.
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=openai_api_key)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt}
)

query = st.text_input("질문을 입력하세요:")

if query:
    with st.spinner("답변 생성 중..."):
        response = qa_chain.invoke({"query": query})
    st.write("🔍 질문:", query)
    st.write("💬 답변:", response['result'])
