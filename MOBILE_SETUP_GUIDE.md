# 📱 Mobile App Setup & Image Fix Guide

## ✅ What Was Fixed

1. **Auto-assigned all room images** from `/media/room_images/` to 29 rooms in database
2. **Enhanced Flutter image loading** with caching, better error handling, and improved placeholders
3. **Upgraded API client** with 15s timeout and better error messages
4. **Django backend** now properly returns absolute image URLs

---

## 🚀 How to Run (Complete Setup)

### **Step 1: Start Django Backend**

```bash
# Terminal 1 (Python terminal):
cd c:\Users\ROG Zephyrus G15\Desktop\Intelligent_Room_Booking
python manage.py runserver 0.0.0.0:8001
```

Expected output:
```
Starting development server at http://0.0.0.0:8001/
```

### **Step 2: Verify API Returns Images**

```bash
# Terminal 2 (PowerShell):
curl http://127.0.0.1:8001/booking/api/rooms/ -s | Select-String -Pattern '"image"' | Select-Object -First 3
```

Should show image URLs like:
```
"image": "http://127.0.0.1:8001/media/room_images/room1.jpg"
```

### **Step 3: Configure Flutter for Android Emulator**

Edit this file:
```
flutter_extracted/room_booking_flutter/lib/core/constants/api_constants.dart
```

Change:
```dart
// FROM:
static const String baseUrl = 'http://127.0.0.1:8001';

// TO (for Android Emulator):
static const String baseUrl = 'http://10.0.2.2:8001';
```

### **Step 4: Run Flutter App**

```bash
# Terminal 3 (PowerShell in flutter_extracted folder):
cd c:\Users\ROG Zephyrus G15\Desktop\Intelligent_Room_Booking\flutter_extracted
flutter run
```

Or use the Android Emulator:
```bash
flutter run -d emulator-5554
```

---

## 🖼️ Image Display Checklist

- [ ] Django backend running on `http://127.0.0.1:8001`
- [ ] API returns image URLs: `curl http://127.0.0.1:8001/booking/api/rooms/`
- [ ] `api_constants.dart` set to correct baseUrl for your device
- [ ] Flutter app refreshed after code changes
- [ ] Room cards now show images in the UI

---

## 🔍 Troubleshooting

### **Images Still Not Showing?**

1. **Check API Response:**
   ```bash
   curl http://127.0.0.1:8001/booking/api/rooms/ | Select-String "image"
   ```
   Should return URLs, not empty strings.

2. **Check Flutter Logs:**
   ```bash
   flutter run -v
   ```
   Look for image load errors or network issues.

3. **Check Network Access:**
   - Android Emulator → Backend: Use `http://10.0.2.2:8001`
   - Windows Desktop: Use `http://127.0.0.1:8001`
   - Physical Phone: Use your PC IP (find with `ipconfig`)

4. **Clear Cache & Rebuild:**
   ```bash
   flutter clean
   flutter pub get
   flutter run
   ```

---

## 📊 Database Status

All **29 rooms** now have images assigned:
```
✓ Booking Check Room (BC101)
✓ Booking Check Room 2 (BC102)
✓ Sample Rooms 1-21 (RM100-RM120)
✓ IFL Room (RM121)
✓ RUPP Rooms (RM122-RM126)
```

---

## 📸 Image Files Available

Located in: `/media/room_images/`

```
20230707105917_IMG_9846_2.jpg
images.jpg
room1.jpg
room2.jpg
room3.jpg
room_rupp1.jpg
room_rupp2.jpg
room_rupp3.jpg
... and 14 more
```

---

## ✨ Features Now Working

- ✅ Room images display with caching
- ✅ Loading spinner while images load
- ✅ Graceful error placeholders if image fails
- ✅ API returns absolute URLs for mobile
- ✅ Better error messages in logs
- ✅ 15s timeout for slow connections

---

## 🎯 Next Steps

1. Start backend: `python manage.py runserver 0.0.0.0:8001`
2. Update API URL in Flutter if using Android Emulator
3. Run Flutter app: `flutter run`
4. Verify images appear in room cards ✅

