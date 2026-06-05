# 🚀 Running the Intelligent Room Booking System

This guide explains how to start both the **Django Backend** and the **Flutter Mobile Application**.

## 1. Prerequisites
Ensure you have the following installed on your system:
*   **Python 3.10+**
*   **Flutter SDK** (Stable channel)
*   **Git**

---

## 2. Running the Django Backend

The backend handles the database, business logic, and the AI chatbot API.

### Step 1: Activate Virtual Environment
Open a terminal in the project root (`Intelligent_Room_Booking`) and run:
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
(If not already done)
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Server
Start the development server on port **8000** (must match Flutter `lib/constants.dart`):
```powershell
python manage.py runserver 8000
```
> **Note**: The server must be running for the Mobile App to fetch data and log in.

---

## 3. Running the Flutter Mobile App

UI matches [MobileApp_Intelligence_University_Room_Booking_System](https://github.com/samaolthun/MobileApp_Intelligence_University_Room_Booking_System) (purple theme, drawer, room image cards).  
Data comes from the **same Django API** as the website (`http://127.0.0.1:8000`).

### Step 1: Navigate to Flutter Directory
Open a **new** terminal (keep the backend running) and go to:
```powershell
cd "C:\Users\ROG Zephyrus G15\Desktop\Intelligent_Room_Booking\flutter_extracted\room_booking_flutter"
flutter pub get
flutter run
```

Or from repo root:
```powershell
cd flutter_extracted\room_booking_flutter
```

### Step 2: Get Dependencies
```powershell
flutter pub get
```

### Step 3: Launch the App
You can run the app on Windows or Chrome:

**For Windows Desktop:**
```powershell
flutter run -d windows
```

**For Web (Chrome):**
```powershell
flutter run -d chrome
```

---

## 4. Test Credentials

Use these credentials to log in and test all features:

| Account Type | Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@example.com` | `password123` |
| **Lecturer/User** | `lecturer@example.com` | `password123` |

> **Important**: When logging in via the **Website**, ensure you select the correct **Account Type** (Administrator or User) from the dropdown.

---

## 5. Troubleshooting

*   **Connection Error on Mobile**: If the mobile app cannot connect to the backend, check `flutter_extracted/room_booking_flutter/lib/core/constants/api_constants.dart`.
    *   For **Chrome/Windows**: Use `http://127.0.0.1:8000`
    *   For **Android Emulator**: Use `http://10.0.2.2:8000`
    *   For **Physical Phone**: Use your PC's LAN IP (run `ipconfig`) with port `8000`
*   **AI Chatbot Not Responding**:
    1. Log in as **User** (not Administrator) — `lecturer@example.com` / `password123`
    2. `.env`: `AI_ENABLED=True`, `LLM_PROVIDER=huggingface`, `HF_API_TOKEN`, `HF_MODEL=Qwen/Qwen2.5-7B-Instruct`
    3. Restart Django: `python manage.py runserver 8000`
    4. Hard refresh browser (**Ctrl+F5**)
    5. Click the **purple chat button** (bottom-right) or **Chat Now** on Home
    6. Check [http://127.0.0.1:8000/chatbot/health/](http://127.0.0.1:8000/chatbot/health/) — `rag_initialized` must be `true`
    *   **Ollama** alternative: set `LLM_PROVIDER=ollama` and run `ollama serve`
*   **ModuleNotFoundError: PIL**: Activate the virtual environment first (`.\.venv\Scripts\Activate.ps1`) before running Django commands.
*   **Database Issues**: If you see "Table not found" errors, run:
    ```powershell
    python manage.py migrate
    ```
