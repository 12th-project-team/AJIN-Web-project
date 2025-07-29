from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic

# ✅ OpenAI와 Anthropic 키 (⚠️ 유출 주의!)
OPENAI_API_KEY = "ddA"
CLAUDE_API_KEY = "dd"

# ✅ 벡터 저장
def build_vectorstore_from_text(text, save_path="faiss_store"):
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_text(text)
    docs = [Document(page_content=chunk) for chunk in chunks]

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectordb = FAISS.from_documents(docs, embeddings)
    vectordb.save_local(save_path)

# ✅ 벡터 + Claude 연결된 RAG 체인 로드
def load_rag_chain(store_path="faiss_store"):
    vectordb = FAISS.load_local(store_path, OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY))
    llm = ChatAnthropic(
        model="claude-3-haiku-20240307",
        anthropic_api_key=CLAUDE_API_KEY
    )
    return RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
