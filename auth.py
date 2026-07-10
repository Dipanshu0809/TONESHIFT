import streamlit as st
import sqlite3
import bcrypt
from pathlib import Path

DATABASE = "users.db"
APP_DIR = Path(__file__).parent

def get_connection():
    return sqlite3.connect(DATABASE, check_same_thread=False)

def create_user(username, email, password):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO users(username,email,password) VALUES(?,?,?)",
            (username, email, hashed),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        if bcrypt.checkpw(password.encode(), user[0]):
            return True
    return False

def login_page():
    # 1. Inject the rewritten layout rules
    login_css = APP_DIR / "styles" / "login.css"
    if login_css.exists():
        st.markdown(f"<style>{login_css.read_text()}</style>", unsafe_allow_html=True)

    # 2. Logo box (its own separate card)
    with st.container(border=True):
        st.markdown('<div class="auth-logo">ToneShift</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">AI-Powered Audience Rewriter</div>', unsafe_allow_html=True)

    # 3. Form box (its own separate card, below the logo box)
    with st.container(border=True):
        tab1, tab2 = st.tabs(["🔒 Sign In", "✨ Create Account"])

        # ---------------- SIGNIN FORM ----------------
        with tab1:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            if st.button("Sign In", use_container_width=True):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

        # ---------------- SIGNUP FORM ----------------
        with tab2:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            username = st.text_input("Pick Username", key="signup_username", placeholder="e.g., alex_dev")
            email = st.text_input("Email Address", key="signup_email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a strong password")
            confirm = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Repeat your password")

            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True):
                if not username or not email or not password:
                    st.warning("Please fill out all fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    if create_user(username, email, password):
                        st.success("🎉 Account created! You can now sign in.")
                    else:
                        st.error("Username or email already exists.")