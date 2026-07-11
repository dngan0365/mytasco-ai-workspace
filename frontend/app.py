"""
Demo UI tối giản cho My Tasco AI Workspace, gọi thẳng vào orchestrator (FastAPI).
Chạy: streamlit run app.py
"""
import httpx
import streamlit as st

BACKEND_URL = st.sidebar.text_input("Orchestrator URL", "http://localhost:8000")

st.set_page_config(page_title="My Tasco AI Workspace", page_icon="🤖", layout="wide")
st.title("🤖 My Tasco AI Workspace — Demo")

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.chat_history = []


def api_get(path: str, **kwargs):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    return httpx.get(f"{BACKEND_URL}{path}", headers=headers, timeout=30, **kwargs)


def api_post(path: str, json: dict):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    return httpx.post(f"{BACKEND_URL}{path}", json=json, headers=headers, timeout=60)


# ---------------- Sidebar: đăng nhập ----------------
with st.sidebar:
    st.header("Đăng nhập (demo)")
    if st.session_state.token is None:
        try:
            demo_users = api_get("/auth/demo-users").json()
        except Exception as exc:
            demo_users = []
            st.error(f"Không kết nối được orchestrator: {exc}")

        options = {f"{u['full_name']} — {u['role']} ({u['department']})": u["user_id"] for u in demo_users}
        if options:
            chosen = st.selectbox("Chọn user mẫu", list(options.keys()))
            if st.button("Đăng nhập"):
                resp = api_post("/auth/login", {"user_id": options[chosen]})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.rerun()
                else:
                    st.error(resp.text)
    else:
        user = st.session_state.user
        st.success(f"Đang đăng nhập: {user['full_name']} ({user['role']} · {user['department']})")
        if st.button("Đăng xuất"):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.chat_history = []
            st.rerun()

if st.session_state.token is None:
    st.info("Chọn 1 user mẫu ở sidebar và đăng nhập để bắt đầu.")
    st.stop()

tab_chat, tab_search, tab_docs = st.tabs(["💬 AI Chat", "🔎 AI Search", "📁 Thư viện tài liệu"])

# ---------------- Tab: AI Chat ----------------
with tab_chat:
    for role, content, sources in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(content)
            if sources:
                with st.expander("Nguồn tài liệu"):
                    for s in sources:
                        st.caption(f"[{s['document_id']}] {s['title']} — {s['classification']}")

    question = st.chat_input("Hỏi về chính sách, chấm công, đơn từ, lương...")
    if question:
        st.session_state.chat_history.append(("user", question, None))
        with st.spinner("Đang suy nghĩ..."):
            resp = api_post("/chat/ask", {"question": question})
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.chat_history.append(("assistant", data["answer"], data.get("sources", [])))
        else:
            st.session_state.chat_history.append(("assistant", f"Lỗi: {resp.text}", None))
        st.rerun()

# ---------------- Tab: AI Search ----------------
with tab_search:
    query = st.text_input("Tìm kiếm tài liệu (ngôn ngữ tự nhiên)")
    if query:
        resp = api_post("/search", {"query": query, "top_k": 5})
        if resp.status_code == 200:
            for r in resp.json():
                st.markdown(f"**[{r['document_id']}] {r['title']}** — {r['department']} · {r['classification']} (score: {r['score']:.3f})")
        else:
            st.error(resp.text)

# ---------------- Tab: Thư viện tài liệu ----------------
with tab_docs:
    resp = api_get("/documents")
    if resp.status_code == 200:
        docs = resp.json()
        st.caption(f"{len(docs)} tài liệu bạn được phép xem")
        for d in docs:
            with st.expander(f"[{d['document_id']}] {d['title']} — {d['classification']}"):
                st.write(f"Phòng ban: {d['department']} · Owner: {d.get('owner')}")
                detail = api_get(f"/documents/{d['document_id']}")
                if detail.status_code == 200:
                    st.write(detail.json().get("content_vi", ""))
    else:
        st.error(resp.text)
