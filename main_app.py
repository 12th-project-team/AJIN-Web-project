import streamlit as st
import os
import importlib
import shutil
import re
from dotenv import load_dotenv
import openai
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from vectorstore_utils import list_chroma_files, delete_chroma_vectorstore
from category_pages import computer
from category_pages.computer_funcs.summary import render as render_summary
from category_pages.computer_funcs.quiz import render as render_quiz
from category_pages.computer_funcs.exam import render as render_exam
from category_pages.computer_funcs.chatbot import render as render_chatbot

# ───────────────────────────────
# 0) 환경 변수 및 OpenAI 키 설정
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "")

# ───────────────────────────────
# 1) 기본(Base) 카테고리
BASE_CATEGORIES = {
    "컴퓨터활용능력": computer.render,
}

# ───────────────────────────────
# 2) 임베딩 모델 & Chroma 초기화
embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY", "")
)
PERSIST_DIR = "./chroma_db"
vectordb = Chroma(
    collection_name="custom_categories",
    persist_directory=PERSIST_DIR,
    embedding_function=embedding
)

# ───────────────────────────────
# 3) 세션에 슬러그 맵 저장
if "slug_map" not in st.session_state:
    st.session_state.slug_map = {}

def generate_slug(category_name: str) -> str:
    """
    OpenAI로부터 영숫자 슬러그를 받아옵니다.
    """
    system = (
        "You are a slug generator.  "
        "Given a Korean category name, respond with exactly one "
        "lowercase alphanumeric slug (letters a–z and digits 0–9 only). "
        "Do NOT output anything else—only the slug."
    )
    user = f"Generate slug for category: {category_name}"
    resp = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.0,
        max_tokens=16,
    )
    slug = resp.choices[0].message.content.strip().lower()
    slug = re.sub(r"[^a-z0-9]", "", slug)
    if not re.fullmatch(r"[a-z0-9]+", slug):
        raise ValueError(f"Invalid slug: {slug}")
    return slug

def get_slug(category_name: str) -> str:
    """
    캐시에 슬러그가 있으면 사용, 없으면 생성 후 캐싱
    """
    if category_name in st.session_state.slug_map:
        return st.session_state.slug_map[category_name]
    slug = generate_slug(category_name)
    st.session_state.slug_map[category_name] = slug
    return slug

def delete_pycache(root: str = "category_pages"):
    for dirpath, dirnames, _ in os.walk(root):
        if "__pycache__" in dirnames:
            shutil.rmtree(os.path.join(dirpath, "__pycache__"), ignore_errors=True)

def get_saved_custom_categories() -> list[str]:
    docs = vectordb.similarity_search("category", k=100)
    return list({doc.page_content for doc in docs})

# ───────────────────────────────
# 4) 동적 카테고리 생성
def create_new_category_with_funcs(category_name: str):
    slug = get_slug(category_name)
    src       = "category_pages/template_funcs"
    dst_funcs = f"category_pages/{slug}_funcs"
    dst_page  = f"category_pages/{slug}.py"

    # funcs 템플릿 전체 복사 (init.py 포함)
    if not os.path.exists(dst_funcs):
        shutil.copytree(src, dst_funcs)

    # 페이지 모듈 생성
    if not os.path.exists(dst_page):
        with open(dst_page, "w", encoding="utf-8") as f:
            f.write(f'''\
import streamlit as st
from category_pages import {slug}_funcs as funcs

def render():
    st.header("📘 {category_name}")

    # 업로드 탭
    funcs.upload("{category_name}")
    st.markdown("---")

    # 미리보기 탭
    funcs.preview("{category_name}")
    st.markdown("---")

    # AI 탭
    tab1, tab2, tab3, tab4 = st.tabs(["요약","기출문제","퀴즈","챗봇"])
    with tab1: funcs.summary("{category_name}")
    with tab2: funcs.exam("{category_name}")
    with tab3: funcs.quiz("{category_name}")
    with tab4: funcs.chatbot("{category_name}")
''')

    # vectordb에도 등록
    vectordb.add_texts(texts=[category_name], ids=[category_name])
    vectordb.persist()

# ───────────────────────────────
# 5) 동적 모듈 로딩
def load_dynamic_category(category_name: str):
    slug = st.session_state.slug_map.get(category_name) or get_slug(category_name)
    importlib.invalidate_caches()
    try:
        mod = importlib.import_module(f"category_pages.{slug}")
        return mod.render
    except ImportError:
        return lambda: st.error(f"❌ 모듈을 찾을 수 없습니다: {category_name}")

# ───────────────────────────────
# 6) 카테고리 삭제
def delete_category(category_name: str):
    slug = st.session_state.slug_map.get(category_name) or get_slug(category_name)

    # 페이지 모듈 & funcs 폴더 삭제
    for path in [f"category_pages/{slug}.py", f"category_pages/{slug}_funcs"]:
        if os.path.exists(path):
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    # __pycache__ 제거
    delete_pycache("category_pages")

    # 문서 임베딩 삭제
    cat_dir = os.path.join(PERSIST_DIR, category_name)
    if os.path.exists(cat_dir):
        shutil.rmtree(cat_dir)

    # 문서별 vectorestore/PDF 삭제
    for fn in list_chroma_files(category_name):
        delete_chroma_vectorstore(category_name, fn)

    # vectordb 메타에서 제거
    vectordb.delete(ids=[category_name])
    vectordb.persist()

    # 세션/UI 정리
    st.session_state.all_categories.pop(category_name, None)
    st.session_state.slug_map.pop(category_name, None)
    if st.session_state.selected_category == category_name:
        st.session_state.selected_category = "컴퓨터활용능력"
    st.session_state.show_delete_confirm = False
    st.rerun()

# ───────────────────────────────
# 7) Streamlit 세션 초기화
if "all_categories" not in st.session_state:
    cats = BASE_CATEGORIES.copy()
    for name in get_saved_custom_categories():
        if name not in cats:
            st.session_state.slug_map[name] = generate_slug(name)
            cats[name] = load_dynamic_category(name)
    st.session_state.all_categories = cats

if "selected_category" not in st.session_state:
    st.session_state.selected_category = "컴퓨터활용능력"

# ───────────────────────────────
# 8) UI 구성
st.title("📚 자격증 문서 기반 AI 학습 플랫폼")
st.markdown("### 📂 카테고리를 선택하거나 새로 추가하세요")

cols = st.columns(len(st.session_state.all_categories) + 2, gap="small")
keys = list(st.session_state.all_categories.keys())

# 기존 카테고리 버튼
for i, cat in enumerate(keys):
    with cols[i]:
        color = "red" if st.session_state.selected_category == cat else "gray"
        if st.button(f"**:{color}[{cat}]**", key=f"btn_{cat}"):
            st.session_state.selected_category = cat

# ➕ 추가 버튼
with cols[-2]:
    if st.button("➕"):
        st.session_state.show_add = True

# 🗑️ 삭제 버튼
with cols[-1]:
    if st.button("🗑️"):
        st.session_state.show_delete_confirm = True

# ➕ 새 카테고리 추가 UI
if st.session_state.get("show_add", False):
    with st.expander("➕ 새 카테고리 추가", expanded=True):
        new_name = st.text_input("카테고리 이름 입력", placeholder="예: 전자상거래")
        if st.button("생성"):
            if not new_name:
                st.warning("카테고리 이름을 입력해주세요.")
            elif new_name in st.session_state.all_categories:
                st.warning("이미 존재하는 카테고리입니다.")
            else:
                create_new_category_with_funcs(new_name)
                st.session_state.all_categories[new_name] = load_dynamic_category(new_name)
                st.session_state.selected_category = new_name
                st.session_state.show_add = False
                st.rerun()

# 🗑️ 삭제 확인 UI
if st.session_state.get("show_delete_confirm", False):
    with st.expander(f"❗ '{st.session_state.selected_category}' 삭제하시겠습니까?", expanded=True):
        if st.button("삭제"):
            delete_category(st.session_state.selected_category)
        if st.button("취소"):
            st.session_state.show_delete_confirm = False
            st.rerun()

st.markdown("---")
# 선택된 카테고리 렌더링
st.session_state.all_categories[st.session_state.selected_category]()
