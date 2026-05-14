"""
Admin authentication via Django backend API
Streamlit module for verifying admin credentials using requests library.
"""

import streamlit as st
import requests
from typing import Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration
DJANGO_API_BASE_URL = "http://localhost:8000"  # Adjust based on your Django server
ADMIN_AUTH_ENDPOINT = f"{DJANGO_API_BASE_URL}/booking/api/auth/admin-verify/"
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3


@st.cache_resource
def get_session():
    """Get a requests session with connection pooling."""
    session = requests.Session()
    return session


def verify_admin_credentials(username: str, password: str) -> Tuple[bool, Optional[dict]]:
    """
    Verify admin credentials by sending a POST request to Django backend API.
    
    Args:
        username: Admin username or email
        password: Admin password
        
    Returns:
        Tuple of (authentication_success: bool, user_data: dict or None)
        - (True, user_data_dict): Authentication successful
        - (False, None): Authentication failed or error occurred
        
    Raises:
        No exceptions - all errors are handled safely
        
    Example:
        >>> success, user_data = verify_admin_credentials("admin@example.com", "password123")
        >>> if success:
        ...     print(f"Welcome {user_data['first_name']}")
    """
    if not username or not password:
        logger.warning("Username or password is empty")
        return False, None
    
    try:
        session = get_session()
        
        # Prepare request payload
        payload = {
            "username": username.strip(),
            "password": password,
        }
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Send POST request to Django API
        logger.info(f"Attempting admin authentication for user: {username}")
        
        response = session.post(
            ADMIN_AUTH_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        
        # Check response status
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success", False):
                user_data = data.get("user", {})
                logger.info(f"Admin authentication successful for: {username}")
                return True, user_data
            else:
                error_msg = data.get("message", "Authentication failed")
                logger.warning(f"Admin authentication failed: {error_msg}")
                return False, None
        
        elif response.status_code == 401:
            logger.warning("Authentication failed: Invalid credentials")
            return False, None
        
        elif response.status_code == 403:
            logger.warning("Authentication failed: User does not have admin privileges")
            return False, None
        
        else:
            logger.warning(f"Unexpected response status: {response.status_code}")
            return False, None
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: Cannot reach Django API at {DJANGO_API_BASE_URL}")
        st.error("🔌 Cannot connect to authentication server. Please try again.")
        return False, None
    
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: Django API did not respond within {REQUEST_TIMEOUT} seconds")
        st.error("⏱️ Authentication server is slow to respond. Please try again.")
        return False, None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        st.error(f"⚠️ Authentication error: {str(e)}")
        return False, None
    
    except ValueError as e:
        logger.error(f"Invalid JSON response: {str(e)}")
        st.error("⚠️ Invalid response from authentication server.")
        return False, None
    
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        st.error(f"⚠️ Unexpected error: {str(e)}")
        return False, None


def verify_admin_credentials_with_retry(
    username: str, 
    password: str, 
    max_retries: int = MAX_RETRIES
) -> Tuple[bool, Optional[dict]]:
    """
    Verify admin credentials with automatic retry logic on network errors.
    
    Args:
        username: Admin username or email
        password: Admin password
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        Tuple of (authentication_success: bool, user_data: dict or None)
        
    Example:
        >>> success, user_data = verify_admin_credentials_with_retry("admin@example.com", "password123", max_retries=2)
    """
    for attempt in range(max_retries):
        try:
            success, user_data = verify_admin_credentials(username, password)
            if success or attempt == max_retries - 1:
                return success, user_data
            
            logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
            
        except Exception as e:
            logger.error(f"Authentication attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                return False, None
    
    return False, None


def set_admin_session(user_data: dict):
    """
    Set admin session state in Streamlit.
    
    Args:
        user_data: User dictionary from API response
    """
    st.session_state.admin_authenticated = True
    st.session_state.admin_user = user_data
    st.session_state.admin_id = user_data.get("id")
    st.session_state.admin_email = user_data.get("email")
    st.session_state.admin_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
    logger.info(f"Admin session created for: {st.session_state.admin_email}")


def clear_admin_session():
    """Clear admin session state."""
    if "admin_authenticated" in st.session_state:
        del st.session_state.admin_authenticated
    if "admin_user" in st.session_state:
        del st.session_state.admin_user
    if "admin_id" in st.session_state:
        del st.session_state.admin_id
    if "admin_email" in st.session_state:
        del st.session_state.admin_email
    if "admin_name" in st.session_state:
        del st.session_state.admin_name
    logger.info("Admin session cleared")


def is_admin_authenticated() -> bool:
    """Check if admin is currently authenticated."""
    return st.session_state.get("admin_authenticated", False)


def get_admin_info() -> Optional[dict]:
    """Get current authenticated admin's information."""
    if is_admin_authenticated():
        return st.session_state.get("admin_user")
    return None


# Configuration helper
def set_api_endpoint(base_url: str):
    """
    Update Django API base URL for authentication.
    
    Args:
        base_url: Base URL of Django server (e.g., "http://localhost:8000" or "https://yourdomain.com")
    """
    global DJANGO_API_BASE_URL, ADMIN_AUTH_ENDPOINT
    DJANGO_API_BASE_URL = base_url.rstrip('/')  # Remove trailing slash if present
    ADMIN_AUTH_ENDPOINT = f"{DJANGO_API_BASE_URL}/booking/api/auth/admin-verify/"
    logger.info(f"API endpoint updated to: {ADMIN_AUTH_ENDPOINT}")
