import streamlit as st
import os, importlib, shutil
from dotenv import load_dotenv
# from langchain_community.embeddings import OpenAIEmbeddings  # 🔒 추후 사용 예정
from langchain_community.vectorstores import Chroma
from category_pages import computer, info, word, itq, office

# ───────────────────────────────
# ✅ 기본 카테고리 등록
BASE_CATEGORIES = {
    "컴퓨터활용능력": computer.render,
    "정보처리": info.render,
    "워드프로세서": word.render,
    "ITQ/GTQ": itq.render,
    "사무자동화": office.render,
}

# ───────────────────────────────
# ✅ 환경변수에서 OpenAI API 키 불러오기 (추후 복구 시 사용)
load_dotenv()

# 🔒 아래 코드는 나중에 OpenAI API 키 복구되면 주석 해제
# embedding = OpenAIEmbeddings(
#     model="text-embedding-3-small",
#     openai_api_key=os.getenv("OPENAI_API_KEY")
# )

# ───────────────────────────────
# ✅ ChromaDB 설정 (지금은 embedding_function 없이)
persist_dir = "./chroma_db"
vectordb = Chroma(
    collection_name="custom_categories",
    persist_directory=persist_dir
    # embedding_function=embedding  # 🔓 나중에 OpenAIEmbeddings 연동 시 주석 해제
)

# ───────────────────────────────
# ✅ 저장된 사용자 카테고리 로딩 (유사도 검색 대신 직접 문서 불러오기)
# 🔒 추후 OpenAI Embedding 사용 시 아래 코드로 복구
# def get_saved_custom_categories():
#     docs = vectordb.similarity_search("category", k=100)
#     return list(set([doc.page_content for doc in docs]))

def get_saved_custom_categories():
    try:
        data = vectordb._collection.get(include=["documents"])
        return list(set(data["documents"]))
    except Exception:
        return []

# ───────────────────────────────
# ✅ snake_case 변환 함수
def snake_case(text):
    return text.lower().replace(" ", "_").replace("-", "_")

# ───────────────────────────────
# ✅ 새로운 카테고리 파일 및 폴더 자동 생성
def create_new_category_with_funcs(category_name):
    module_base = snake_case(category_name)
    page_file = f"category_pages/{module_base}.py"
    funcs_src = "category_pages/computer_funcs"
    funcs_dest = f"category_pages/{module_base}_funcs"

    # 기능 폴더 복사
    if not os.path.exists(funcs_dest):
        shutil.copytree(funcs_src, funcs_dest)

    # 메인 파일 생성
    if not os.path.exists(page_file):
        with open(page_file, "w", encoding="utf-8") as f:
            f.write(f'''
import streamlit as st
from category_pages import {module_base}_funcs

def render():
    st.header("📘 {category_name}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "요약", "문제풀이", "미리보기", "퀴즈", "챗봇", "업로드"
    ])

    with tab1:
        {module_base}_funcs.summary.render()
    with tab2:
        {module_base}_funcs.exam.render()
    with tab3:
        {module_base}_funcs.preview.render()
    with tab4:
        {module_base}_funcs.quiz.render()
    with tab5:
        {module_base}_funcs.chatbot.render()
    with tab6:
        {module_base}_funcs.upload.render()
'''.strip())

# ───────────────────────────────
# ✅ 동적 모듈 로딩
def load_dynamic_category(category_name):
    module_name = snake_case(category_name)
    try:
        mod = importlib.import_module(f"category_pages.{module_name}")
        return mod.render
    except:
        return lambda: st.error("❌ 해당 카테고리 모듈을 찾을 수 없습니다.")

# ───────────────────────────────
# ✅ 세션 초기화 및 카테고리 로딩
if "all_categories" not in st.session_state:
    all_cats = BASE_CATEGORIES.copy()
    for name in get_saved_custom_categories():
        all_cats[name] = load_dynamic_category(name)
    st.session_state.all_categories = all_cats

if "selected_category" not in st.session_state:
    st.session_state.selected_category = list(st.session_state.all_categories.keys())[0]

# ───────────────────────────────
# ✅ 상단 버튼 탭 UI + 간이 팝업 카테고리 추가
st.title("📚 자격증 문서 기반 AI 학습 플랫폼")
st.markdown("### 📂 카테고리를 선택하거나 새로 추가하세요")

# ➕ 버튼 포함된 열 구성
cols = st.columns(len(st.session_state.all_categories) + 1, gap="small")

# 기존 카테고리 버튼 렌더링
for i, cat in enumerate(st.session_state.all_categories):
    with cols[i]:
        color = "red" if st.session_state.selected_category == cat else "gray"
        if st.button(f"**:{color}[{cat}]**"):
            st.session_state.selected_category = cat

# ➕ 버튼으로 입력창 열기
with cols[-1]:
    if st.button("➕"):
        st.session_state.show_add_expander = True

# 입력창 (간이 모달 역할)
if st.session_state.get("show_add_expander", False):
    with st.expander("➕ 새 카테고리 추가", expanded=True):
        new_cat_name = st.text_input("카테고리 이름 입력", placeholder="예: 전자상거래")
        if st.button("추가하기"):
            if new_cat_name and new_cat_name not in st.session_state.all_categories:
                create_new_category_with_funcs(new_cat_name)

                # 🔒 추후 OpenAI Embedding 사용 시 아래 코드로 복구
                # vectordb.add_texts([new_cat_name])
                # 🔓 지금은 임시 저장 생략 (Chroma는 embedding_function 없이는 저장 불가)
                # vectordb._collection.add(documents=[new_cat_name], ids=[new_cat_name])
                # vectordb.persist()

                render_func = load_dynamic_category(new_cat_name)
                st.session_state.all_categories[new_cat_name] = render_func
                st.session_state.selected_category = new_cat_name
                st.session_state.show_add_expander = False
                st.experimental_rerun()

st.markdown("---")
st.session_state.all_categories[st.session_state.selected_category]()
