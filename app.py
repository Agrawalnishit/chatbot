import streamlit as st
from google import genai
import os
import json
from datetime import datetime
import re

# =====================================
# GEMINI CLIENT
# =====================================
client = genai.Client(api_key=("AIzaSyAZluA8KZzCJ5glOB87UV1RDV12qtlXCF8"))

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="AI Technical Interviewer",
    page_icon="💬",
    layout="centered"
)

# =====================================
# SESSION STATE
# =====================================
if "sessions" not in st.session_state:
    st.session_state.sessions = {"Session 1": []}

if "current_session" not in st.session_state:
    st.session_state.current_session = "Session 1"

if "mode" not in st.session_state:
    st.session_state.mode = "Ask Question"

if "scores" not in st.session_state:
    st.session_state.scores = []

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

# =====================================
# SIDEBAR – SESSIONS
# =====================================
st.sidebar.title("💬 Chat Sessions")

session_names = list(st.session_state.sessions.keys())
selected_session = st.sidebar.selectbox(
    "Select Session",
    session_names,
    index=session_names.index(st.session_state.current_session)
)

if selected_session != st.session_state.current_session:
    st.session_state.current_session = selected_session
    st.session_state.interview_started = False
    st.rerun()

if st.sidebar.button("➕ New Session"):
    name = f"Session {len(st.session_state.sessions) + 1}"
    st.session_state.sessions[name] = []
    st.session_state.current_session = name
    st.session_state.interview_started = False
    st.rerun()

st.sidebar.markdown("---")

# =====================================
# INTERVIEW SETTINGS
# =====================================
interviewer_role = st.sidebar.selectbox(
    "Interviewer Role",
    [
        "SDE-1 Interviewer",
        "Backend Developer Interviewer",
        "Frontend Developer Interviewer",
        "DevOps Interviewer",
        "System Design Interviewer"
    ]
)

interview_topic = st.sidebar.selectbox(
    "Interview Topic",
    ["DSA", "Python", "Java", "System Design", "SQL"]
)

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"]
)

# =====================================
# MODE
# =====================================
st.sidebar.markdown("---")
mode = st.sidebar.radio(
    "Interview Mode",
    ["Ask Question", "Answer Evaluation"]
)

if mode != st.session_state.mode:
    st.session_state.mode = mode
    st.session_state.interview_started = False

# =====================================
# SCORE SUMMARY + AUTO DIFFICULTY
# =====================================
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Interview Summary")

effective_difficulty = difficulty

if st.session_state.scores:
    avg = sum(st.session_state.scores) / len(st.session_state.scores)
    st.sidebar.write(f"Questions Evaluated: {len(st.session_state.scores)}")
    st.sidebar.write(f"Average Score: {avg:.1f} / 10")

    if avg >= 8:
        effective_difficulty = "Hard"
        st.sidebar.success("Auto Difficulty: HARD")
    elif avg >= 5:
        effective_difficulty = "Medium"
        st.sidebar.info("Auto Difficulty: MEDIUM")
    else:
        effective_difficulty = "Easy"
        st.sidebar.warning("Auto Difficulty: EASY")
else:
    st.sidebar.write("No evaluations yet")

# =====================================
# MAIN UI
# =====================================
st.title("💬 AI Technical Interviewer")
st.info(
    f"Mode: **{st.session_state.mode}** | "
    f"Difficulty Used: **{effective_difficulty}**"
)

# Buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ Clear Chat"):
        st.session_state.sessions[st.session_state.current_session] = []
        st.session_state.scores = []
        st.session_state.interview_started = False
        st.success("Chat cleared")

with col2:
    if st.button("💾 Save Chat"):
        chat = st.session_state.sessions[st.session_state.current_session]
        if chat:
            name = f"{st.session_state.current_session}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(name, "w") as f:
                json.dump(chat, f, indent=2)
            st.success(f"Saved as {name}")

st.markdown("---")

# =====================================
# CHAT HISTORY
# =====================================
history = st.session_state.sessions[st.session_state.current_session]

for msg in history:
    st.chat_message(msg["role"]).write(msg["text"])

# =====================================
# INTERVIEW MODE – ASK FIRST
# =====================================
if st.session_state.mode == "Answer Evaluation" and not st.session_state.interview_started:
    prompt = f"""
You are a {interviewer_role}.
Topic: {interview_topic}
Difficulty: {effective_difficulty}

Ask ONE interview question.
Do not answer it.
"""
    with st.spinner("Interviewer is asking..."):
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        history.append({"role": "assistant", "text": res.text})
        st.session_state.interview_started = True
        st.rerun()

# =====================================
# USER INPUT
# =====================================
user_input = st.chat_input("Type here...")

if user_input:
    history.append({"role": "user", "text": user_input})

    if st.session_state.mode == "Ask Question":
        prompt = f"""
You are a {interviewer_role}.
Topic: {interview_topic}
Difficulty: {effective_difficulty}

Answer clearly and professionally.
"""
    else:
        prompt = f"""
You are a {interviewer_role}.
Evaluate the answer.

Give:
1. Strengths
2. Weaknesses
3. Improvements
4. Final score

IMPORTANT:
Write score exactly like:
SCORE: X/10
"""

    convo = [{"role": "user", "parts": [{"text": prompt}]}]
    for m in history:
        convo.append({
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["text"]}]
        })

    with st.spinner("Thinking..."):
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=convo
        )
        reply = res.text

    history.append({"role": "assistant", "text": reply})

    if st.session_state.mode == "Answer Evaluation":
        match = re.search(r"SCORE:\s*(\d+)\s*/\s*10", reply)
        if match:
            st.session_state.scores.append(int(match.group(1)))

    st.rerun()
