"""
Admin Login Page for Streamlit using Django API authentication
Demonstrates the usage of admin_auth module for API-based authentication
"""

import streamlit as st
from admin_auth import (
    verify_admin_credentials,
    verify_admin_credentials_with_retry,
    set_admin_session,
    clear_admin_session,
    is_admin_authenticated,
    get_admin_info,
    ADMIN_AUTH_ENDPOINT,
)


def show_admin_login_form():
    """Display admin login form."""
    st.subheader("🔐 Admin Login")
    st.write("Enter your credentials to access the admin dashboard.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        username = st.text_input(
            "Email or Username",
            placeholder="admin@example.com",
            key="admin_username_input"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="admin_password_input"
        )
        
        # Login button
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                with st.spinner("🔍 Verifying credentials..."):
                    # Use retry logic for better reliability
                    success, user_data = verify_admin_credentials_with_retry(
                        username,
                        password,
                        max_retries=2
                    )
                    
                    if success:
                        # Set session state
                        set_admin_session(user_data)
                        st.success("✓ Login successful! Redirecting to dashboard...")
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed. Please check your credentials.")
    
    with col2:
        st.info(
            "**Requirements:**\n\n"
            "✓ Active admin account\n"
            "✓ Staff privileges\n"
            "✓ Django is running\n"
            "✓ Connection available"
        )


def show_admin_dashboard():
    """Display admin dashboard for authenticated admin."""
    # Display admin info in sidebar
    with st.sidebar:
        st.write("---")
        st.subheader("👤 Admin Info")
        
        admin_info = get_admin_info()
        if admin_info:
            st.write(f"**Name:** {admin_info.get('first_name', '')} {admin_info.get('last_name', '')}")
            st.write(f"**Email:** {admin_info.get('email', '')}")
            st.write(f"**Role:** {'Super Admin' if admin_info.get('is_superuser') else 'Staff Admin'}")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                clear_admin_session()
                st.rerun()
    
    # Main dashboard content
    st.title("📊 Admin Dashboard")
    st.markdown("---")
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📅 Bookings", "🏠 Rooms", "⚙️ Settings"])
    
    with tab1:
        st.subheader("Dashboard Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bookings", "---")
        
        with col2:
            st.metric("Available Rooms", "---")
        
        with col3:
            st.metric("Active Users", "---")
        
        with col4:
            st.metric("Today's Bookings", "---")
        
        st.info("Dashboard data will be loaded from the database once configured.")
    
    with tab2:
        st.subheader("Booking Management")
        st.write("View and manage all room bookings here.")
        st.info("Booking management interface coming soon...")
    
    with tab3:
        st.subheader("Room Management")
        st.write("Add, edit, or delete rooms from the system.")
        st.info("Room management interface coming soon...")
    
    with tab4:
        st.subheader("System Settings")
        st.write("Configure booking rules and system preferences.")
        st.info("Settings panel coming soon...")


def main():
    """Main entry point for admin page."""
    st.set_page_config(
        page_title="Room Booking System - Admin",
        page_icon="👨‍💼",
        layout="wide"
    )
    
    # Sidebar branding
    with st.sidebar:
        st.title("🏢 Room Booking")
        st.write("**Admin Panel**")
    
    # Check authentication
    if is_admin_authenticated():
        show_admin_dashboard()
    else:
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.title("🏢 Room Booking System")
            st.write("---")
            show_admin_login_form()
        
        # Footer info
        st.write("---")
        st.info(
            f"**API Connection Info:**\n\n"
            f"Endpoint: `{ADMIN_AUTH_ENDPOINT}`\n\n"
            "Make sure Django development server is running on port 8000."
        )


if __name__ == "__main__":
    main()
