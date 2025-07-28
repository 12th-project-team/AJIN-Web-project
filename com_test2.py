from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS  
import os

# -------------------------
# 1. PDF 문서 로드
# -------------------------
pdf_path = "data/컴활2급.pdf"  
loader = PyPDFLoader(pdf_path)
documents = loader.load()

# -------------------------
# 2. PDF 문서를 청크로 분할
# -------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)

# -------------------------
# 3. 임베딩 모델 생성
# -------------------------
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# -------------------------
# 4. 벡터스토어에 저장 (FAISS 기준)
# -------------------------
vectordb = FAISS.from_documents(chunks, embedding_model)
vectordb.save_local("faiss_db")  

print("✅ 벡터스토어 저장 완료: faiss_db/")
