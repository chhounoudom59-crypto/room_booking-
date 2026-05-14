"""
Main Streamlit Application with Two-Factor Authentication (2FA)
Implements:
1. Password-based login
2. Face verification via webcam
Grants access to analytics dashboard only after both steps pass.

Features:
- Secure session-based authentication
- Multi-step authentication flow (email → password → face verification)
- Real-time authentication progress tracking
- Database-driven user verification
- Face embedding validation
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path

# Import authentication modules
from utils import (
    init_session_state,
    is_authenticated,
    complete_authentication,
    reset_auth_state,
    mark_password_verified,
    mark_face_verified,
)
from database import (
    verify_user_credentials,
    get_user_by_email,
    user_exists,
    fetch_all_bookings,
    fetch_rooms_dataframe,
    get_room_occupancy_stats,
)
from verification import verify_face_from_pil

APP_ROOT = Path(__file__).resolve().parent


def _load_admin_npy_embeddings(admin_id: int) -> list[dict]:
    admin_dir = APP_ROOT / "embeddings" / "admin_embeddings" / f"admin_{admin_id}"
    if not admin_dir.exists():
        return []

    items: list[dict] = []
    for file_path in sorted(admin_dir.glob("*.npy")):
        angle = file_path.stem
        try:
            embedding = np.load(str(file_path))
        except Exception:
            continue
        items.append({"angle": angle, "embedding": embedding})

    return items


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Room Booking System with 2FA",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom styling
    st.markdown(
        """
        <style>
        .auth-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 2rem;
        }
        .stApp {background-color: #f5f7fa;}
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# AUTHENTICATION STEPS
# ============================================================================

def show_email_step():
    """
    Step 1: Email verification.
    Check if email exists in database.
    """
    st.markdown("### Step 1: Email Verification")
    st.write("Enter your email address to continue.")

    email = st.text_input(
        "Email Address",
        placeholder="user@university.edu",
        key="auth_email_input",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("Continue →", use_container_width=True, key="email_continue"):
            if not email:
                st.error("❌ Please enter an email address")
            elif user_exists(email):
                st.session_state.user_email = email
                st.session_state.auth_step = "password"
                st.session_state.password_attempts = 0
                st.success("✓ Email found! Proceeding to password verification...")
                st.rerun()
            else:
                st.error("❌ Email not found in system. Please check and try again.")

    with col2:
        st.info(" Tips:\n- Use your university email\n- Check spelling carefully")


def show_password_step():
    """
    Step 2: Password verification.
    Verify password for the email entered in step 1.
    """
    st.markdown("###  Step 2: Password Verification")

    email = st.session_state.user_email
    user_info = get_user_by_email(email)

    if user_info:
        st.write(f"Welcome, **{user_info.get('first_name', 'User')}**!")

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="auth_password_input",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("Verify Password →", use_container_width=True, key="password_verify"):
            if not password:
                st.error("❌ Please enter your password")
            else:
                # Verify credentials
                if verify_user_credentials(email, password):
                    mark_password_verified(user_info)
                    st.session_state.auth_step = "face"
                    st.success("✓ Password verified! Proceeding to face verification...")
                    st.rerun()
                else:
                    st.session_state.password_attempts = st.session_state.get(
                        "password_attempts", 0
                    ) + 1

                    if st.session_state.password_attempts >= 3:
                        st.error(
                            "❌ Too many failed attempts. Please restart the login process."
                        )
                        if st.button("← Start Over", use_container_width=True):
                            reset_auth_state()
                            st.rerun()
                    else:
                        remaining = 3 - st.session_state.password_attempts
                        st.error(
                            f"❌ Incorrect password ({remaining} attempts remaining)"
                        )

    with col2:
        if st.button("← Back", use_container_width=True, key="password_back"):
            st.session_state.auth_step = "email"
            st.session_state.password_attempts = 0
            st.rerun()

    # Progress indicator
    st.info("✓ Email verified\n🔄 Password verification (current step)")


def show_face_verification_step():
    """
    Step 3: Face verification.
    Capture live face image and verify against stored embedding.
    """
    st.markdown("### 👤 Step 3: Face Verification")

    email = st.session_state.user_email
    user_info = get_user_by_email(email)

    st.write(
        f"**{user_info.get('first_name')}**, please verify your identity using face recognition."
    )

    # Create two columns for instructions and camera
    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(
            """
            **Instructions:**
            1. Position your face clearly in the camera
            2. Ensure good lighting
            3. Face the camera directly
            4. Click the camera button to capture
            """
        )

        face_verified = False

        threshold = st.slider(
            "ArcFace Similarity Threshold",
            min_value=0.2,
            max_value=0.7,
            value=0.35,
            step=0.01,
            help="Higher = stricter matching.",
        )
        histogram_threshold = st.slider(
            "Histogram Fallback Threshold",
            min_value=0.7,
            max_value=0.99,
            value=0.9,
            step=0.01,
            help="Used if ArcFace fails or histogram embeddings are stored.",
        )

        # Capture image using Streamlit's camera input
        picture = st.camera_input(
            "Take a picture of your face",
            key="auth_face_camera",
        )

        if picture:
            st.write("📸 Image captured. Analyzing...")

            # Retrieve stored embedding for this user
            from database import retrieve_user_face_embeddings, retrieve_admin_face_embedding

            stored_embeddings = retrieve_user_face_embeddings(user_email=email)
            if not stored_embeddings:
                if user_info and (user_info.get("is_staff") or user_info.get("is_superuser")):
                    stored_embeddings = _load_admin_npy_embeddings(int(user_info["id"]))
            if not stored_embeddings:
                # Backward compatibility: check admin embeddings if user embeddings not found
                admin_embedding = retrieve_admin_face_embedding(user_email=email)
                if admin_embedding is not None:
                    stored_embeddings = [{"angle": None, "embedding": admin_embedding}]

            if stored_embeddings:
                # Verify the captured face against all stored embeddings
                verified, details = verify_face_from_pil(
                    picture,
                    stored_embeddings,
                    threshold=threshold,
                    histogram_threshold=histogram_threshold,
                )

                if verified:
                    best_similarity = details.get("best_similarity", 0)
                    method = details.get("method", "unknown")
                    spoof = details.get("spoof_detected", False)
                    st.success(
                        f"✓ Face verified! (Similarity: {best_similarity:.2%}, method: {method})"
                    )
                    if spoof:
                        st.warning("Spoofing checks flagged risk, but verification passed.")
                    mark_face_verified()
                    # Complete authentication and grant dashboard access
                    complete_authentication(user_info)
                    st.success("✓ Authentication complete! Redirecting to dashboard...")
                    st.rerun()
                else:
                    error_msg = details.get("errors", "Face verification failed")
                    st.error(f"❌ {error_msg}")
                    st.info(
                        f"Similarity score: {details.get('best_similarity', 0):.2%}\n"
                        f"Method: {details.get('method', 'unknown')}\n"
                        f"Spoofing detected: {details.get('spoof_detected', False)}"
                    )
            else:
                st.error(
                    f"❌ No face embedding found for {email}.\n"
                    f"Please enroll your face or contact administrator."
                )

    with col2:
        st.subheader("Progress")
        st.write("✓ Email verified")
        st.write("✓ Password verified")
        st.write("→ Face verification (current)")

        if st.button("← Back", use_container_width=True, key="face_back"):
            st.session_state.auth_step = "password"
            st.rerun()


def show_authentication_ui():
    """Manage the authentication flow with multiple steps."""
    # Create authentication container
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("## Two-Factor Authentication")
        st.markdown("---")

        auth_step = st.session_state.auth_step

        if auth_step == "email":
            show_email_step()

        elif auth_step == "password":
            show_password_step()

        elif auth_step == "face":
            show_face_verification_step()


# ============================================================================
# DASHBOARD
# ============================================================================

def show_logout_button():
    """Show logout button in sidebar."""
    with st.sidebar:
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            reset_auth_state()
            st.rerun()


def show_dashboard():
    """Display analytics dashboard after 2FA passes."""
    # Show user info in sidebar
    user_info = st.session_state.user_info
    with st.sidebar:
        st.markdown("---")
        st.subheader("👤 Logged In As")
        st.write(f"**{user_info.get('first_name')} {user_info.get('last_name')}**")
        st.write(f"📧 {user_info.get('email')}")
        st.write(
            f"🔑 {'Admin' if user_info.get('is_staff') else 'User'}"
        )

    show_logout_button()

    # Main dashboard content
    st.markdown("## 📊 Room Booking Analytics Dashboard")
    st.markdown("---")

    try:
        # Fetch data
        bookings = fetch_all_bookings(limit=100)
        df_rooms = fetch_rooms_dataframe()
        occupancy_stats = get_room_occupancy_stats(days=7)

        # KPI Cards
        st.subheader("📈 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            confirmed = len([b for b in bookings if b["status"] == "confirmed"])
            st.metric("Total Bookings", confirmed)

        with col2:
            if df_rooms is not None and not df_rooms.empty:
                st.metric("Total Rooms", len(df_rooms))
            else:
                st.metric("Total Rooms", "---")

        with col3:
            if occupancy_stats:
                total_occupancy = sum(r["bookings"] for r in occupancy_stats.values())
                st.metric("Occupancy (7d)", total_occupancy)
            else:
                st.metric("Occupancy (7d)", "---")

        with col4:
            users = len(set(b["user_email"] for b in bookings))
            st.metric("Active Users", users)

        st.markdown("---")

        # Detailed views
        tab1, tab2, tab3 = st.tabs(
            ["📅 Bookings", "🏠 Rooms", "📊 Analytics"]
        )

        # Tab 1: Bookings
        with tab1:
            st.subheader("Recent Bookings")
            if bookings:
                df_bookings = pd.DataFrame(bookings)
                st.dataframe(
                    df_bookings[
                        [
                            "user_name",
                            "room_name",
                            "start_time",
                            "end_time",
                            "purpose",
                            "status",
                        ]
                    ],
                    use_container_width=True,
                )

                # Download button
                csv = df_bookings.to_csv(index=False)
                st.download_button(
                    label="📥 Download Bookings (CSV)",
                    data=csv,
                    file_name=f"bookings_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No bookings found")

        # Tab 2: Rooms
        with tab2:
            st.subheader("Room Overview")
            if df_rooms is not None and not df_rooms.empty:
                st.dataframe(
                    df_rooms[["Room Number", "Room Name", "Capacity", "Type"]],
                    use_container_width=True,
                )

                # Room type distribution
                st.subheader("Rooms by Type")
                type_counts = df_rooms["Type"].value_counts()
                st.bar_chart(type_counts)
            else:
                st.info("No rooms found")

        # Tab 3: Analytics
        with tab3:
            st.subheader("Occupancy Trends")
            if occupancy_stats:
                df_stats = pd.DataFrame(
                    [
                        {"Room": k, "Bookings": v["bookings"]}
                        for k, v in occupancy_stats.items()
                    ]
                )
                st.bar_chart(df_stats.set_index("Room"))

                # Booking status pie chart
                if bookings:
                    status_counts = {}
                    for b in bookings:
                        status = b["status"]
                        status_counts[status] = status_counts.get(status, 0) + 1

                    st.subheader("Booking Status Distribution")
                    status_df = pd.DataFrame(
                        [(status, count) for status, count in status_counts.items()],
                        columns=["status", "count"],
                    )
                    fig_status = px.pie(
                        status_df,
                        names="status",
                        values="count",
                        title="Booking Status Distribution",
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No occupancy data available")

        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        st.error(f"⚠️ Error loading dashboard: {str(e)}")
        st.info("Please check your database connection and try again.")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    configure_page()
    init_session_state()

    # Show 2FA flow or dashboard based on authentication status
    if not is_authenticated():
        # Display authentication flow
        show_authentication_ui()
    else:
        # Display dashboard for authenticated users
        show_dashboard()


if __name__ == "__main__":
    main()

