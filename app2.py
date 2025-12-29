import streamlit as st
import requests
from google import genai
import os
import json
from datetime import datetime

# ================================
# CONFIG
# ================================

MOJOAUTH_API_KEY = "test-aac4f940-f5b3-478f-adb6-b0ab36ec9d25"
GEMINI_API_KEY ="AIzaSyAZluA8KZzCJ5glOB87UV1RDV12qtlXCF8"

client = genai.Client(api_key=GEMINI_API_KEY)

MOJOAUTH_BASE_URL = "https://api.mojoauth.com"

# ================================
# PAGE CONFIG
# ================================

st.set_page_config(
    page_title="AI Technical Interviewer",
    page_icon="🔐",
    layout="centered"
)

# ================================
# SESSION STATE INIT
# ================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "mojoauth_token" not in st.session_state:
    st.session_state.mojoauth_token = None

# ================================
# AUTH FUNCTIONS (MOJOAUTH)
# ================================

def send_email_otp(email):
    url = f"{MOJOAUTH_BASE_URL}/users/emailotp"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": MOJOAUTH_API_KEY
    }
    payload = {
        "email": email
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 200


def verify_email_otp(email, otp):
    url = f"{MOJOAUTH_BASE_URL}/users/emailotp/verify"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": MOJOAUTH_API_KEY
    }
    payload = {
        "email": email,
        "otp": otp
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("token")
    return None

# ================================
# LOGIN / SIGNUP UI
# ================================

if not st.session_state.authenticated:

    st.title("🔐 Login / Signup")
    st.write("Secure authentication using **MojoAuth**")

    email = st.text_input("📧 Enter your email")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send OTP"):
            if email:
                success = send_email_otp(email)
                if success:
                    st.success("OTP sent to your email")
                else:
                    st.error("Failed to send OTP")
            else:
                st.warning("Please enter email")

    otp = st.text_input("🔑 Enter OTP")

    with col2:
        if st.button("Verify OTP"):
            if email and otp:
                token = verify_email_otp(email, otp)
                if token:
                    st.session_state.authenticated = True
                    st.session_state.mojoauth_token = token
                    st.success("Login successful 🎉")
                    st.rerun()
                else:
                    st.error("Invalid OTP")
            else:
                st.warning("Enter email and OTP")

    st.stop()  # 🔴 IMPORTANT: Stop app here if not logged in

# ================================
# CHATBOT LOGIC (UNCHANGED)
# ================================

if "sessions" not in st.session_state:
    st.session_state.sessions = {"Session 1": []}

if "current_session" not in st.session_state:
    st.session_state.current_session = "Session 1"

# ================================
# SIDEBAR
# ================================

st.sidebar.title("👤 User")
st.sidebar.success("Authenticated")

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.mojoauth_token = None
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.title("💬 Sessions")

session_names = list(st.session_state.sessions.keys())
selected_session = st.sidebar.selectbox(
    "Select Session",
    session_names,
    index=session_names.index(st.session_state.current_session)
)

if selected_session != st.session_state.current_session:
    st.session_state.current_session = selected_session
    st.rerun()

if st.sidebar.button("➕ New Session"):
    new_session = f"Session {len(st.session_state.sessions) + 1}"
    st.session_state.sessions[new_session] = []
    st.session_state.current_session = new_session
    st.rerun()

# ================================
# MAIN CHAT UI
# ================================

st.title("💬 AI Technical Interviewer")

history = st.session_state.sessions[st.session_state.current_session]

for msg in history:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["text"])
    else:
        st.chat_message("assistant").write(msg["text"])

user_input = st.chat_input("Ask your interview question...")

if user_input:
    history.append({"role": "user", "text": user_input})

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": user_input}]}]
    )

    reply = response.text
    history.append({"role": "assistant", "text": reply})
    st.rerun()
