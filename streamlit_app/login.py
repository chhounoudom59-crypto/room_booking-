"""
Login authentication UI for Streamlit app.
Handles user identification and password verification.
"""

import streamlit as st
from database import verify_user_credentials, get_user_by_email, user_exists
from utils import mark_password_verified


def show_email_login_ui() -> str | None:
    """
    Display email login form.
    
    Returns:
        User email if entered, None otherwise
    """
    st.subheader("📧 Email Login")
    
    email = st.text_input(
        "Email Address",
        placeholder="user@example.com",
        key="login_email_input"
    )
    
    if email and st.button("Continue with Email"):
        if user_exists(email):
            return email
        else:
            st.error("❌ Email not found. Please check and try again.")
    
    return None


def show_password_ui(email: str) -> bool:
    """
    Display password verification form.
    
    Args:
        email: User email for password verification
        
    Returns:
        True if password verified successfully, False otherwise
    """
    st.subheader("🔑 Enter Password")
    
    # Display user info
    user_info = get_user_by_email(email)
    if user_info:
        st.write(f"Welcome, **{user_info.get('first_name', 'User')}**!")
    
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password_input"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Verify Password", use_container_width=True):
            if password:
                if verify_user_credentials(email, password):
                    mark_password_verified(user_info)
                    st.success("✓ Password verified!")
                    st.session_state.user_email = email
                    return True
                else:
                    st.error("❌ Incorrect password. Please try again.")
            else:
                st.warning("⚠️ Please enter your password.")
    
    with col2:
        if st.button("Back", use_container_width=True):
            st.session_state.auth_step = "email_login"
            st.rerun()
    
    return False


def show_login_ui() -> bool:
    """
    Main login flow handler with multi-step authentication.
    
    Returns:
        True if password verification completed, False otherwise
    """
    st.set_page_config(
        page_title="Room Booking System - Login",
        page_icon="🔐",
        layout="centered"
    )
    
    # Title and branding
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏢 Room Booking System")
    with col2:
        st.write("")
        st.write("")
    
    st.markdown("---")
    
    # Login flow
    auth_step = st.session_state.auth_step
    
    if auth_step == "email_login":
        st.write("Sign in with your institutional email address.")
        email = show_email_login_ui()
        if email:
            st.session_state.auth_step = "password"
            st.rerun()
    
    elif auth_step == "password":
        if st.session_state.user_email:
            password_verified = show_password_ui(st.session_state.user_email)
            return password_verified
    
    return False


def show_logout_button():
    """Display logout button in sidebar."""
    with st.sidebar:
        st.write("---")
        if st.button("🚪 Logout", use_container_width=True):
            from utils import reset_auth_state
            reset_auth_state()
            st.rerun()
