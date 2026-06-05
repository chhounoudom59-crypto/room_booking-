import 'package:flutter/foundation.dart' show kIsWeb;

class AppConstants {
  /// Must match Django: `python manage.py runserver 8000`
  static const int serverPort = 8000;

  /// • Web / Windows desktop → 127.0.0.1
  /// • Android emulator → 10.0.2.2 (host loopback)
  /// Physical phone: set true and update [lanHost] (run `ipconfig` on PC).
  static const bool usePhysicalDeviceHost = false;
  static const String lanHost = '10.1.79.142';

  static String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:$serverPort';
    }
    if (usePhysicalDeviceHost) {
      return 'http://$lanHost:$serverPort';
    }
    return 'http://10.0.2.2:$serverPort';
  }

  static String get loginUrl => '$baseUrl/accounts/api/login/';
  static String get registerUrl => '$baseUrl/accounts/api/register/';
  static String get logoutUrl => '$baseUrl/accounts/api/logout/';
  static String get profileUrl => '$baseUrl/accounts/api/profile/';

  static String get roomsUrl => '$baseUrl/booking/api/rooms/';
  static String get availabilityUrl => '$baseUrl/booking/api/rooms/availability/';
  static String get searchRoomsUrl => '$baseUrl/booking/api/rooms/search/';
  static String get bookingsUrl => '$baseUrl/booking/api/bookings/';
  static String get createBookingUrl => '$baseUrl/booking/api/bookings/create/';
  static String get cancelBookingUrl => '$baseUrl/booking/api/bookings/cancel/';
  static String get bookingRulesUrl => '$baseUrl/booking/api/rules/';

  static String get chatbotUrl => '$baseUrl/chatbot/chat/';
  static String get chatbotHealthUrl => '$baseUrl/chatbot/health/';
}
