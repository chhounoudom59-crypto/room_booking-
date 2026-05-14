"""
Database utilities for Streamlit app authentication and booking analytics.
Handles user verification, booking queries, room data, and face embeddings.
"""

import os
import sys
import django
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q, Count
from pathlib import Path
import json
import numpy as np
from datetime import datetime, timedelta
import pandas as pd

# Add project root to Python path to find room_booking_system
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "room_booking_system.settings")
django.setup()

from django.contrib.auth import get_user_model
from booking.models import Booking, Room, BookingRule

User = get_user_model()

# Face embeddings storage directory
EMBEDDINGS_DIR = Path(__file__).parent / "face_embeddings"
EMBEDDINGS_DIR.mkdir(exist_ok=True)


def _infer_embedding_method(embedding, embedding_method: str | None = None) -> str:
    """Infer embedding method for metadata/debugging.

    Both FaceNet and this project's histogram fallback are 128-D, so vector
    length alone cannot distinguish them.
    """
    if embedding_method in {"facenet", "histogram", "unknown"}:
        return embedding_method

    try:
        arr = np.asarray(embedding, dtype=float).reshape(-1)
    except Exception:
        return "unknown"

    if arr.size != 128:
        return "unknown"

    # FaceNet embeddings usually contain negative values; histograms do not.
    if np.any(arr < 0):
        return "facenet"
    return "histogram"


def verify_user_credentials(email: str, password: str) -> bool:
    """
    Verify user email and password against Django User model.
    
    Args:
        email: User email address
        password: User password
        
    Returns:
        True if credentials are valid, False otherwise
    """
    try:
        user = User.objects.get(email=email)
        return user.check_password(password)
    except User.DoesNotExist:
        return False


def get_user_by_email(email: str) -> dict | None:
    """
    Retrieve user information by email.
    
    Args:
        email: User email address
        
    Returns:
        Dictionary with user info or None if not found
    """
    try:
        user = User.objects.get(email=email)
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "email_verified": user.email_verified if hasattr(user, "email_verified") else False,
        }
    except User.DoesNotExist:
        return None


def user_exists(email: str) -> bool:
    """Check if user exists in database."""
    return User.objects.filter(email=email).exists()


# ============================================================================
# BOOKING DATA FUNCTIONS
# ============================================================================

def fetch_all_bookings(status: str = None, limit: int = None) -> list:
    """
    Fetch all booking records from database.
    
    Args:
        status: Filter by status ('confirmed', 'cancelled', or None for all)
        limit: Maximum number of records to return
        
    Returns:
        List of dictionaries containing booking data
    """
    try:
        query = Booking.objects.select_related('user', 'room')
        
        if status:
            query = query.filter(status=status)
        
        if limit:
            query = query[:limit]
        
        bookings = []
        for booking in query:
            bookings.append({
                'id': booking.id,
                'user_email': booking.user.email,
                'user_name': booking.user.get_full_name(),
                'room_name': booking.room.name,
                'room_number': booking.room.room_number,
                'room_type': booking.room.room_type,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
                'purpose': booking.purpose,
                'status': booking.status,
                'attendees': booking.attendees,
                'created_at': booking.created_at.isoformat(),
            })
        
        return bookings
    
    except Exception as e:
        print(f"Error fetching bookings: {e}")
        return []


def fetch_user_bookings(email: str, status: str = None) -> list:
    """
    Fetch bookings for a specific user.
    
    Args:
        email: User email address
        status: Filter by status ('confirmed', 'cancelled', or None for all)
        
    Returns:
        List of dictionaries containing booking data
    """
    try:
        user = User.objects.get(email=email)
        query = Booking.objects.filter(user=user).select_related('room')
        
        if status:
            query = query.filter(status=status)
        
        bookings = []
        for booking in query:
            bookings.append({
                'id': booking.id,
                'room_name': booking.room.name,
                'room_number': booking.room.room_number,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
                'purpose': booking.purpose,
                'status': booking.status,
                'attendees': booking.attendees,
            })
        
        return bookings
    
    except User.DoesNotExist:
        return []
    except Exception as e:
        print(f"Error fetching user bookings: {e}")
        return []


def fetch_bookings_dataframe(days: int = 7) -> pd.DataFrame:
    """
    Fetch recent bookings as a Pandas DataFrame for Streamlit charts.
    
    Args:
        days: Number of days in the past to fetch
        
    Returns:
        Pandas DataFrame with booking data
    """
    try:
        start_date = timezone.now() - timedelta(days=days)
        
        bookings = Booking.objects.filter(
            created_at__gte=start_date
        ).select_related('user', 'room').values(
            'id', 'user__email', 'room__name', 'room__room_type',
            'start_time', 'status', 'attendees', 'created_at'
        ).order_by('-created_at')
        
        df = pd.DataFrame(bookings)
        
        if df.empty:
            return pd.DataFrame()
        
        # Rename columns for clarity
        df.rename(columns={
            'user__email': 'User Email',
            'room__name': 'Room Name',
            'room__room_type': 'Room Type',
            'start_time': 'Booking Time',
            'status': 'Status',
            'attendees': 'Attendees',
            'created_at': 'Created At'
        }, inplace=True)
        
        return df
    
    except Exception as e:
        print(f"Error creating bookings dataframe: {e}")
        return pd.DataFrame()


# ============================================================================
# ROOM DATA FUNCTIONS
# ============================================================================

def fetch_all_rooms() -> list:
    """
    Fetch all room data from database.
    
    Returns:
        List of dictionaries containing room data
    """
    try:
        rooms = []
        for room in Room.objects.all():
            rooms.append({
                'id': room.id,
                'name': room.name,
                'room_number': room.room_number,
                'capacity': room.capacity,
                'room_type': room.room_type,
                'description': room.description,
                'equipment': room.equipment,
                'availability_status': room.availability_status,
                'is_available': room.is_available,
                'created_at': room.created_at.isoformat(),
            })
        
        return rooms
    
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        return []


def fetch_room_by_id(room_id: int) -> dict:
    """
    Fetch a specific room by ID.
    
    Args:
        room_id: Room ID
        
    Returns:
        Dictionary with room data or None if not found
    """
    try:
        room = Room.objects.get(id=room_id)
        return {
            'id': room.id,
            'name': room.name,
            'room_number': room.room_number,
            'capacity': room.capacity,
            'room_type': room.room_type,
            'description': room.description,
            'equipment': room.equipment,
            'availability_status': room.availability_status,
            'is_available': room.is_available,
        }
    
    except Room.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error fetching room: {e}")
        return None


def fetch_rooms_dataframe() -> pd.DataFrame:
    """
    Fetch all rooms as a Pandas DataFrame for Streamlit charts.
    
    Returns:
        Pandas DataFrame with room data
    """
    try:
        rooms = Room.objects.all().values(
            'id', 'name', 'room_number', 'capacity', 'room_type',
            'availability_status', 'is_available'
        ).order_by('room_number')
        
        df = pd.DataFrame(rooms)
        
        if df.empty:
            return pd.DataFrame()
        
        # Rename columns for clarity
        df.rename(columns={
            'name': 'Room Name',
            'room_number': 'Room Number',
            'capacity': 'Capacity',
            'room_type': 'Type',
            'availability_status': 'Status',
            'is_available': 'Active'
        }, inplace=True)
        
        return df
    
    except Exception as e:
        print(f"Error creating rooms dataframe: {e}")
        return pd.DataFrame()


# ============================================================================
# ROOM AVAILABILITY ANALYTICS
# ============================================================================

def get_room_occupancy_stats(days: int = 7) -> dict:
    """
    Get room occupancy statistics for the past N days.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Dictionary with occupancy statistics by room
    """
    try:
        start_date = timezone.now() - timedelta(days=days)
        
        rooms = Room.objects.annotate(
            total_bookings=Count('bookings', filter=Q(
                bookings__start_time__gte=start_date,
                bookings__status='confirmed'
            ))
        ).values('id', 'name', 'room_number', 'total_bookings')
        
        stats = {}
        for room in rooms:
            stats[room['room_number']] = {
                'name': room['name'],
                'bookings': room['total_bookings']
            }
        
        return stats
    
    except Exception as e:
        print(f"Error getting occupancy stats: {e}")
        return {}


# ============================================================================
# FACE EMBEDDING STORAGE & RETRIEVAL
# ============================================================================

def store_admin_face_embedding(
    user_id: int,
    embedding: np.ndarray,
    user_email: str = None,
    embedding_method: str | None = None,
) -> bool:
    """
    Store face embedding for an admin/staff member for face verification.
    
    Args:
        user_id: User ID
        embedding: Face embedding as NumPy array (any dimensions)
        user_email: User email (optional, for identification)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get or verify user is admin/staff
        user = User.objects.get(id=user_id)
        
        if not (user.is_staff or user.is_superuser or user.is_admin):
            print(f"User {user_id} is not admin/staff")
            return False
        
        # Convert embedding to list for JSON storage
        embedding_data = {
            'user_id': user_id,
            'user_email': user.email,
            'embedding': embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
            'embedding_dim': len(embedding) if isinstance(embedding, (list, np.ndarray)) else None,
            'stored_at': datetime.now().isoformat(),
            'embedding_method': _infer_embedding_method(embedding, embedding_method)
        }
        
        # Save to JSON file
        filename = f"admin_{user_id}_{user.email.split('@')[0]}.json"
        filepath = EMBEDDINGS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(embedding_data, f, indent=2)
        
        print(f"✓ Stored embedding for {user.email}")
        return True
    
    except User.DoesNotExist:
        print(f"User {user_id} not found")
        return False
    except Exception as e:
        print(f"Error storing embedding: {e}")
        return False


def retrieve_admin_face_embedding(user_id: int = None, user_email: str = None) -> np.ndarray:
    """
    Retrieve face embedding for admin verification.
    
    Args:
        user_id: User ID (preferred)
        user_email: User email (fallback)
        
    Returns:
        NumPy array with embedding, or None if not found
    """
    try:
        # Find the embedding file
        if user_id:
            user = User.objects.get(id=user_id)
            pattern = f"admin_{user_id}_*.json"
        elif user_email:
            user = User.objects.get(email=user_email)
            email_prefix = user_email.split('@')[0]
            pattern = f"admin_*_{email_prefix}.json"
        else:
            return None
        
        # Search for file
        import glob
        files = glob.glob(str(EMBEDDINGS_DIR / pattern))
        
        if not files:
            print(f"No embedding found for user")
            return None
        
        # Load embedding
        with open(files[0], 'r') as f:
            data = json.load(f)
        
        embedding = np.array(data['embedding'])
        print(f"✓ Retrieved embedding (dim={data['embedding_dim']}, method={data['embedding_method']})")
        
        return embedding
    
    except User.DoesNotExist:
        print(f"User not found")
        return None
    except Exception as e:
        print(f"Error retrieving embedding: {e}")
        return None


def list_admin_embeddings() -> list:
    """
    List all stored admin face embeddings.
    
    Returns:
        List of dictionaries with admin embedding info
    """
    try:
        embeddings = []
        
        for filepath in EMBEDDINGS_DIR.glob("admin_*.json"):
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            embeddings.append({
                'user_id': data['user_id'],
                'user_email': data['user_email'],
                'embedding_dim': data['embedding_dim'],
                'embedding_method': data['embedding_method'],
                'stored_at': data['stored_at'],
            })
        
        return embeddings
    
    except Exception as e:
        print(f"Error listing embeddings: {e}")
        return []


def delete_admin_face_embedding(user_id: int) -> bool:
    """
    Delete stored face embedding for an admin.
    
    Args:
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import glob
        
        pattern = f"admin_{user_id}_*.json"
        files = glob.glob(str(EMBEDDINGS_DIR / pattern))
        
        if not files:
            print(f"No embedding found for user {user_id}")
            return False
        
        for filepath in files:
            Path(filepath).unlink()
            print(f"✓ Deleted embedding for user {user_id}")
        
        return True
    
    except Exception as e:
        print(f"Error deleting embedding: {e}")
        return False


# ============================================================================
# USER FACE EMBEDDING STORAGE & RETRIEVAL
# ============================================================================

def store_user_face_embeddings(
    user_email: str,
    embeddings: list,
    embedding_method: str | None = None,
) -> bool:
    """
    Store multiple face embeddings for a user (multi-angle enrollment).

    Args:
        user_email: User email address
        embeddings: list of embeddings or list of dicts {angle, embedding}

    Returns:
        True if successful, False otherwise
    """
    try:
        user = User.objects.get(email=user_email)

        serialized = []
        for item in embeddings:
            if isinstance(item, dict):
                emb = item.get("embedding")
                angle = item.get("angle")
            else:
                emb = item
                angle = None

            emb_list = emb.tolist() if isinstance(emb, np.ndarray) else emb
            serialized.append(
                {
                    "angle": angle,
                    "embedding": emb_list,
                }
            )

        first_emb = serialized[0]["embedding"] if serialized else []

        embedding_data = {
            "user_id": user.id,
            "user_email": user.email,
            "embeddings": serialized,
            "embedding_dim": len(first_emb) if isinstance(first_emb, list) else None,
            "stored_at": datetime.now().isoformat(),
            "embedding_method": _infer_embedding_method(first_emb, embedding_method),
        }

        filename = f"user_{user.id}_{user.email.split('@')[0]}.json"
        filepath = EMBEDDINGS_DIR / filename

        with open(filepath, "w") as f:
            json.dump(embedding_data, f, indent=2)

        print(f"✓ Stored {len(serialized)} embeddings for {user.email}")
        return True

    except User.DoesNotExist:
        print(f"User with email {user_email} not found")
        return False
    except Exception as e:
        print(f"Error storing user embeddings: {e}")
        return False


def store_user_face_embedding(
    user_email: str,
    embedding: np.ndarray,
    embedding_method: str | None = None,
) -> bool:
    """
    Store a single face embedding (backward compatible).
    """
    return store_user_face_embeddings(user_email, [embedding], embedding_method=embedding_method)


def retrieve_user_face_embeddings(user_email: str) -> list:
    """
    Retrieve all stored embeddings for a user.

    Returns:
        List of dicts: {angle, embedding}
    """
    try:
        user = User.objects.get(email=user_email)

        import glob
        pattern = f"user_{user.id}_*.json"
        files = glob.glob(str(EMBEDDINGS_DIR / pattern))

        if not files:
            print(f"No user embedding found for {user_email}")
            return []

        with open(files[0], "r") as f:
            data = json.load(f)

        if "embeddings" in data:
            items = []
            for item in data["embeddings"]:
                items.append(
                    {
                        "angle": item.get("angle"),
                        "embedding": np.array(item.get("embedding")),
                    }
                )
            print(
                f"✓ Retrieved {len(items)} user embeddings "
                f"(dim={data.get('embedding_dim')}, method={data.get('embedding_method')})"
            )
            return items

        # Backward compatible single embedding format.
        embedding = np.array(data["embedding"])
        print(
            f"✓ Retrieved user embedding (dim={data.get('embedding_dim')}, method={data.get('embedding_method')})"
        )
        return [{"angle": None, "embedding": embedding}]

    except User.DoesNotExist:
        print(f"User with email {user_email} not found")
        return []
    except Exception as e:
        print(f"Error retrieving user embeddings: {e}")
        return []


def retrieve_user_face_embedding(user_email: str) -> np.ndarray | None:
    """
    Retrieve the first stored embedding for backward compatibility.
    """
    items = retrieve_user_face_embeddings(user_email)
    if not items:
        return None
    return items[0].get("embedding")
