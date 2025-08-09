# app.py
import uuid
import requests
import streamlit as st

st.set_page_config(page_title="n8n Webhook Chat", page_icon="💬")

# --- Sidebar: 설정 ---
st.sidebar.header("설정")
webhook_url = st.sidebar.text_input(
    "Webhook URL",
    value="https://6311df04c601.ngrok-free.app/webhook/9406d6e4-77ef-4d8d-9f9b-117cacf0f45e",
)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
st.session_state.session_id = st.sidebar.text_input(
    "session_id",
    value=st.session_state.session_id,
)

timeout_sec = st.sidebar.slider("요청 타임아웃(초)", 10, 120, 60, 5)

# --- 대화 상태 ---
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role":"user"/"assistant", "content": "..."}]

st.title("n8n Webhook Chat 💬")
st.caption("좌측에서 Webhook URL과 session_id를 설정하세요.")

# --- 과거 메시지 렌더 ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- content 추출 (간소/안전) ---
def extract_content(data):
    # 기대 구조: {"message":{"content": "..."}}
    if isinstance(data, dict) and "message" in data:
        msg = data["message"]
        if isinstance(msg, dict) and "content" in msg:
            return msg["content"]
    # 대안: [ { "message": { "content": ... } } ]
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and "message" in first:
            msg = first["message"]
            if isinstance(msg, dict) and "content" in msg:
                return msg["content"]
    # 마지막 방어: 문자열로 반환
    return str(data)

# --- 입력 박스 ---
user_input = st.chat_input("메시지를 입력하세요…")

if user_input:
    # 1) 유저 메시지 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2) 호출 & 응답 표시
    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("요청 중…"):
            try:
                params = {
                    "chatInput": user_input,
                    "session_id": st.session_state.session_id,
                }
                r = requests.get(webhook_url, params=params, timeout=timeout_sec)
                r.raise_for_status()
                # JSON 우선, 실패 시 텍스트
                content_type = r.headers.get("Content-Type", "")
                if content_type.startswith("application/json"):
                    data = r.json()
                    content = extract_content(data)
                else:
                    content = r.text
            except requests.RequestException as e:
                content = f"요청 실패: {e}"
            except ValueError as e:
                content = f"JSON 디코딩 실패: {e}"

        placeholder.markdown(content)
        st.session_state.messages.append({"role": "assistant", "content": content})

