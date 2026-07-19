# """
# app.py
# ------
# Entry point of the Cutoff College Predictor app.
# Run with:  streamlit run app.py

# This page handles Login / Sign Up. Once logged in, the user is pointed to
# the other pages in the sidebar (Predict College, My History, Admin Dashboard).
# Streamlit's built-in multi-page mechanism auto-detects every file inside the
# `pages/` folder and adds it to the sidebar automatically.
# """

import streamlit as st
from database import init_db, add_user, authenticate_user

st.set_page_config(
    page_title="Cutoff College Predictor",
    page_icon="🎓",
    layout="centered",
)

# Create the SQLite tables on first run (safe to call every time)
init_db()

# ---- session state defaults ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None


def login_form():
    st.subheader("Login to your account")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", use_container_width=True, type="primary"):
        if not username or not password:
            st.warning("Please fill in both fields.")
        else:
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"Welcome back, {user['username']}! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid username or password.")


def signup_form():
    st.subheader("Create a new account")
    username = st.text_input("Choose a username", key="signup_username")
    email = st.text_input("Email address", key="signup_email")
    password = st.text_input("Choose a password", type="password", key="signup_password")
    confirm = st.text_input("Confirm password", type="password", key="signup_confirm")

    if st.button("Sign Up", use_container_width=True, type="primary"):
        if not (username and email and password and confirm):
            st.warning("Please fill in every field.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 4:
            st.error("Password should be at least 4 characters long.")
        else:
            success, message = add_user(username, email, password)
            if success:
                st.success(message + " You can now log in from the Login tab.")
            else:
                st.error(message)


# ---------------- Page body ----------------
st.title("🎓 Cutoff College Predictor")
st.caption("Predict which colleges & branches you're eligible for, based on your entrance exam percentile.")

if st.session_state.logged_in:
    st.success(f"You are logged in as **{st.session_state.user['username']}**")
    st.info("👈 Use the sidebar to open **Predict College** or **My History**.")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
else:
    tab_login, tab_signup = st.tabs(["🔐 Login", "🆕 Sign Up"])
    with tab_login:
        login_form()
    with tab_signup:
        signup_form()

st.divider()
st.caption(
    "Sample data notice: the cutoff numbers shipped with this project are "
    "randomly generated for demo purposes. Replace `data/cutoff_data.csv` "
    "with real cutoff data for accurate predictions."
)