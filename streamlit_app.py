import os
from importlib.metadata import distributions

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="오늘의 할 일", page_icon="✅")
st.title("✅ 오늘의 할 일")
st.caption("Streamlit 화면에서 할 일을 관리합니다. 데이터는 FastAPI와 SQLite에 저장됩니다.")

with st.sidebar:
    st.markdown("[🏪 메인페이지로 돌아가기](/)")
    st.divider()
    st.header("📦 패키지 관리")
    st.caption("프론트·백엔드 공통 가상환경 · uv")
    search = st.text_input("설치 패키지 검색")
    packages = sorted(
        [{"패키지": d.metadata["Name"], "버전": d.version} for d in distributions()],
        key=lambda item: item["패키지"].lower(),
    )
    st.dataframe(
        [p for p in packages if search.lower() in p["패키지"].lower()],
        hide_index=True,
    )
    st.code("uv add 패키지명\nuv remove 패키지명\nuv sync --locked", language="bash")
    st.caption("서버 터미널에서 실행 후 앱을 재시작하세요.")


def api_request(method: str, path: str, **kwargs) -> requests.Response:
    try:
        response = requests.request(
            method, f"{API_BASE_URL}{path}", timeout=5, **kwargs
        )
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        detail = ""
        if error.response is not None:
            try:
                detail = error.response.json().get("detail", "")
            except ValueError:
                detail = error.response.text
        st.error(f"백엔드 요청에 실패했습니다: {detail or error}")
        st.stop()


with st.form("create-task", clear_on_submit=True):
    title = st.text_input("새 할 일", max_chars=200, placeholder="예: 장보기")
    submitted = st.form_submit_button("추가", type="primary")

if submitted:
    if not title.strip():
        st.warning("할 일 내용을 입력해 주세요.")
    else:
        api_request("POST", "/tasks", json={"title": title})
        st.rerun()

tasks = api_request("GET", "/tasks").json()
completed_count = sum(task["done"] for task in tasks)
st.progress(completed_count / len(tasks) if tasks else 0)
st.caption(f"완료 {completed_count} / 전체 {len(tasks)}")

if not tasks:
    st.info("등록된 할 일이 없습니다. 새 할 일을 추가해 보세요.")

for task in tasks:
    checkbox_col, delete_col = st.columns([8, 1])
    with checkbox_col:
        done = st.checkbox(
            task["title"],
            value=task["done"],
            key=f"task-{task['id']}",
        )
    if done != task["done"]:
        api_request("PATCH", f"/tasks/{task['id']}", json={"done": done})
        st.rerun()
    with delete_col:
        if st.button("삭제", key=f"delete-{task['id']}"):
            api_request("DELETE", f"/tasks/{task['id']}")
            st.rerun()
