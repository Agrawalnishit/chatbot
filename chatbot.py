import streamlit as st
from google import genai
import os
import re

# =====================================
# GEMINI CLIENT
# =====================================
client = genai.Client(api_key=("AIzaSyAZluA8KZzCJ5glOB87UV1RDV12qtlXCF8"))

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="AI Interview & Career Guide",
    page_icon="🎯",
    layout="centered"
)

# =====================================
# SESSION STATE
# =====================================
if "normal_chat_history" not in st.session_state:
    st.session_state.normal_chat_history = []

if "interview_chat_history" not in st.session_state:
    st.session_state.interview_chat_history = []

if "interview_active" not in st.session_state:
    st.session_state.interview_active = False

if "interview_phase" not in st.session_state:
    st.session_state.interview_phase = "greeting"

if "scores" not in st.session_state:
    st.session_state.scores = []

# =====================================
# SIDEBAR – MODE SELECTION
# =====================================
st.sidebar.title("🧭 App Mode")

app_mode = st.sidebar.radio(
    "Choose how you want to use the app",
    ["Normal Chat (Guided)", "Interview Practice"]
)

st.sidebar.markdown("---")

# =====================================
# NORMAL CHAT SETUP
# =====================================
if app_mode == "Normal Chat (Guided)":
    st.sidebar.subheader("🎓 Learning Focus")

    normal_role = st.sidebar.selectbox(
        "Target Role",
        [
            "SDE-1",
            "Backend Developer",
            "Frontend Developer",
            "DevOps Engineer",
            "System Design Learner"
        ]
    )

# =====================================
# INTERVIEW SETUP
# =====================================
if app_mode == "Interview Practice":
    st.sidebar.subheader("🎛 Interview Setup")

    company = st.sidebar.selectbox(
        "Company",
        ["Google", "Amazon", "Microsoft", "Startup"]
    )

    interview_role = st.sidebar.selectbox(
        "Interview Role",
        [
            "SDE-1 Interviewer",
            "Backend Developer Interviewer",
            "Frontend Developer Interviewer",
            "DevOps Interviewer",
            "System Design Interviewer"
        ]
    )

    personality = st.sidebar.selectbox(
        "Interviewer Personality",
        ["Friendly", "Strict", "Socratic", "FAANG-style"]
    )

    topic = st.sidebar.selectbox(
        "Primary Topic",
        ["DSA", "Python", "Java", "System Design", "SQL"]
    )

    difficulty = st.sidebar.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    if st.sidebar.button("▶️ Start Interview"):
        st.session_state.interview_active = True
        st.session_state.interview_phase = "greeting"
        st.session_state.interview_chat_history = []
        st.session_state.scores = []

    if st.sidebar.button("⏹ Exit Interview"):
        st.session_state.interview_active = False
        st.session_state.interview_phase = "greeting"

# =====================================
# SELECT ACTIVE HISTORY
# =====================================
history = (
    st.session_state.normal_chat_history
    if app_mode == "Normal Chat (Guided)"
    else st.session_state.interview_chat_history
)

# =====================================
# MAIN UI
# =====================================
st.title("🎯 AI Interview & Career Guide")

if app_mode == "Normal Chat (Guided)":
    st.info(f"🎓 Guided learning for **{normal_role}** (mentor-style)")
else:
    st.info("🧪 Interview Practice Mode – real interview simulation")

# =====================================
# DISPLAY CHAT HISTORY
# =====================================
for msg in history:
    st.chat_message(msg["role"]).write(msg["text"])

# =====================================
# INTERVIEW GREETING
# =====================================
if app_mode == "Interview Practice" and st.session_state.interview_active:
    if st.session_state.interview_phase == "greeting":
        greeting = f"""
Hi, how are you today?

Welcome to the interview at **{company}**.
I'm your **{interview_role}**.

Please introduce yourself briefly.
"""
        history.append({"role": "assistant", "text": greeting})
        st.session_state.interview_phase = "intro"
        st.rerun()

# =====================================
# USER INPUT
# =====================================
user_input = st.chat_input("Type here...")

if user_input:
    history.append({"role": "user", "text": user_input})

    # =====================================================
    # NORMAL CHAT (STRICT ROLE-GUIDED)
    # =====================================================
    if app_mode == "Normal Chat (Guided)":

        # STEP 1: RELEVANCE CHECK
        relevance_prompt = f"""
You are an interview preparation expert.

Target Role: {normal_role}

Question:
"{user_input}"

Reply with ONLY one word:
YES or NO

YES → If this question is directly relevant for {normal_role} interviews.
NO → If it is generic or irrelevant.
"""
        relevance_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": relevance_prompt}]}]
        )

        is_relevant = relevance_response.text.strip().upper()

        # STEP 2: ANSWER OR GUIDE
        if is_relevant == "YES":
            answer_prompt = f"""
You are a senior mentor guiding a {normal_role} candidate.

Answer the question STRICTLY from a {normal_role} interview perspective.

Question:
{user_input}
"""
        else:
            answer_prompt = f"""
You are a professional interview mentor.

Politely explain that:
- This question is NOT usually asked in a {normal_role} interview or exam.
- Suggest what topics the candidate should focus on instead.
- Keep the tone encouraging and professional.

Question:
{user_input}
"""

        convo = [{"role": "user", "parts": [{"text": answer_prompt}]}]
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=convo
        )

        history.append({"role": "assistant", "text": response.text})
        st.rerun()

    # =====================================================
    # INTERVIEW PRACTICE MODE
    # =====================================================
    else:
        if st.session_state.interview_phase == "intro":
            prompt = f"""
You are a {personality} interviewer at {company}.
Role: {interview_role}
Topic: {topic}
Difficulty: {difficulty}

Ask ONE technical interview question.
Do not give the answer.
"""
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )
            history.append({"role": "assistant", "text": res.text})
            st.session_state.interview_phase = "technical"
            st.rerun()

        elif st.session_state.interview_phase == "technical":
            prompt = f"""
You are a {personality} interviewer at {company}.
Role: {interview_role}

Evaluate the candidate's answer.

Give:
1. Strengths
2. Weaknesses
3. Improvement tips
4. Confidence (Low/Medium/High)
5. Technical Depth (Low/Medium/High)
6. Final score

IMPORTANT:
Write score exactly as:
SCORE: X/10
"""
            convo = [{"role": "user", "parts": [{"text": prompt}]}]
            for m in history:
                convo.append({
                    "role": "user" if m["role"] == "user" else "model",
                    "parts": [{"text": m["text"]}]
                })

            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=convo
            )
            reply = res.text
            history.append({"role": "assistant", "text": reply})

            match = re.search(r"SCORE:\s*(\d+)\s*/\s*10", reply)
            if match:
                st.session_state.scores.append(int(match.group(1)))

            st.session_state.interview_phase = "intro"
            st.rerun()
