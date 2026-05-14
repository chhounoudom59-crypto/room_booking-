#!/usr/bin/env python
"""
Simple test to verify database.py imports work correctly.
Run this to verify the fix works before running Streamlit apps.
"""

import sys
from pathlib import Path

# Test 1: Check we can import
print("=" * 60)
print("✓ Testing database.py imports...")
print("=" * 60)

try:
    from streamlit_app.database import (
        fetch_all_bookings,
        fetch_user_bookings,
        fetch_bookings_dataframe,
        fetch_all_rooms,
        fetch_room_by_id,
        fetch_rooms_dataframe,
        get_room_occupancy_stats,
        store_admin_face_embedding,
        retrieve_admin_face_embedding,
        list_admin_embeddings,
        delete_admin_face_embedding,
    )
    print("✅ All database functions imported successfully!")
    
    # Test 2: Try basic queries
    print("\n" + "=" * 60)
    print("✓ Testing basic database queries...")
    print("=" * 60)
    
    bookings = fetch_all_bookings(limit=1)
    print(f"✅ fetch_all_bookings(): {len(bookings)} records")
    
    rooms = fetch_all_rooms()
    print(f"✅ fetch_all_rooms(): {len(rooms)} records")
    
    stats = get_room_occupancy_stats(days=7)
    print(f"✅ get_room_occupancy_stats(): {len(stats)} rooms with data")
    
    embeddings = list_admin_embeddings()
    print(f"✅ list_admin_embeddings(): {len(embeddings)} stored")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n✨ You can now run:")
    print("   streamlit run streamlit_app/test_database_analytics.py")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
