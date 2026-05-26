"""
Quick Setup Guide for Analytics Dashboard
Run this script to install dependencies and test the dashboard
"""

import os
import subprocess
import sys


def install_requirements():
    """Install required packages for the dashboard"""

    packages = [
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "plotly>=5.17.0"
    ]

    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            return False

    return True

def check_django_setup():
    """Verify Django is configured correctly"""

    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'room_booking_system.settings')
        import django
        django.setup()

        from booking.models import Booking, Room

        Room.objects.count()
        Booking.objects.count()

        return True

    except Exception:
        return False

def run_dashboard():
    """Start the Streamlit dashboard"""

    subprocess.call([sys.executable, "-m", "streamlit", "run", "dashboard_analytics.py"])

def main():

    # Step 1: Install dependencies
    if not install_requirements():
        return

    # Step 2: Check Django
    if not check_django_setup():
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Step 3: Run dashboard
    response = input("\nStart the dashboard now? (y/n): ")

    if response.lower() == 'y':
        run_dashboard()
    else:
        pass

if __name__ == "__main__":
    main()
