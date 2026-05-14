"""
Utility functions for Streamlit app.
General-purpose helpers for UI and state management.
"""

import streamlit as st


def init_session_state():
    """Initialize session state variables for 2FA flow."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "password_verified" not in st.session_state:
        st.session_state.password_verified = False
    if "face_verified" not in st.session_state:
        st.session_state.face_verified = False
    if "password_attempts" not in st.session_state:
        st.session_state.password_attempts = 0
    if "auth_step" not in st.session_state:
        # Steps: email → password → face → dashboard
        st.session_state.auth_step = "email"


def reset_auth_state():
    """Reset authentication state back to email step."""
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_info = None
    st.session_state.password_verified = False
    st.session_state.face_verified = False
    st.session_state.password_attempts = 0
    st.session_state.auth_step = "email"


def mark_password_verified(user_info: dict):
    """Mark password as verified and store user info."""
    st.session_state.password_verified = True
    st.session_state.user_info = user_info


def mark_face_verified():
    """Mark face as verified."""
    st.session_state.face_verified = True


def complete_authentication(user_info: dict):
    """Mark authentication as complete."""
    st.session_state.authenticated = True
    st.session_state.user_info = user_info
    st.session_state.auth_step = "dashboard"


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)
