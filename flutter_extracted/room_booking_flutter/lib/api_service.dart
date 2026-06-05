import 'dart:convert';
import 'package:http/http.dart' as http;
import 'constants.dart';

class ApiService {
  static String? _sessionCookie;
  static String? _csrfToken;
  static String? authToken;
  static Map<String, dynamic>? currentUser;

  static String? get userEmail =>
      currentUser?['email']?.toString();

  static Map<String, String> get _headers {
    final h = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (_sessionCookie != null) h['Cookie'] = _sessionCookie!;
    if (_csrfToken != null) h['X-CSRFToken'] = _csrfToken!;
    if (authToken != null) h['Authorization'] = 'Token $authToken';
    return h;
  }


  static void _saveSession(http.Response response) {
    final cookies = response.headers['set-cookie'];
    if (cookies == null) return;
    _sessionCookie = cookies.split(';').first;
    final csrfMatch = RegExp(r'csrftoken=([^;]+)').firstMatch(cookies);
    if (csrfMatch != null) {
      _csrfToken = csrfMatch.group(1);
    }
  }

  static Map<String, dynamic> _decodeBody(http.Response response) {
    try {
      final data = jsonDecode(response.body);
      if (data is Map<String, dynamic>) return data;
      if (data is Map) return Map<String, dynamic>.from(data);
    } catch (_) {}
    return {};
  }

  /// Fix relative or wrong-port image URLs from the API.
  static String resolveImageUrl(String? url) {
    if (url == null || url.trim().isEmpty) return '';
    var u = url.trim();
    if (u.startsWith('/')) {
      u = '${AppConstants.baseUrl}$u';
    }
    final parsed = Uri.tryParse(u);
    final base = Uri.parse(AppConstants.baseUrl);
    if (parsed != null &&
        parsed.hasScheme &&
        parsed.host == base.host &&
        parsed.port != base.port) {
      return parsed.replace(port: base.port).toString();
    }
    return u;
  }

  /// Map Django room JSON to home-screen card format.
  static Map<String, dynamic> mapRoomForUi(Map<String, dynamic> r) {
    final status = r['availability_status']?.toString() ?? 'available';
    final available =
        r['is_available'] == true && status == 'available';
    return {
      'id': r['id'],
      'name': r['name'] ?? '',
      'building': r['room_number']?.toString() ?? '',
      'capacity': r['capacity'] ?? 0,
      'available': available,
      'image': resolveImageUrl(r['image']?.toString()),
      'type': r['room_type']?.toString() ?? '',
      'description': r['description']?.toString() ?? '',
      'equipment': r['equipment']?.toString() ?? '',
    };
  }

  /// Map Django booking JSON to history-screen format.
  static Map<String, dynamic> mapBookingForHistory(Map<String, dynamic> b) {
    final start = b['start_time']?.toString() ?? '';
    final end = b['end_time']?.toString() ?? '';
    final rawStatus = b['status']?.toString().toLowerCase() ?? '';
    String status = 'Pending';
    if (rawStatus == 'confirmed') {
      status = 'Confirmed';
    } else if (rawStatus == 'cancelled') {
      status = 'Cancelled';
    }
    return {
      'id': b['id'],
      'roomName': b['room_name'] ?? 'Room',
      'status': status,
      'building': b['room_number']?.toString() ?? '',
      'date': start.length >= 10 ? start.substring(0, 10) : start,
      'time': '$start - $end',
      'purpose': b['purpose'] ?? '',
      'capacity': '${b['attendees'] ?? 0} people',
      'startTime': start,
      'endTime': end,
      'duration': '${b['duration_hours'] ?? ''} hours',
      'bookedBy': ApiService.currentUser?['first_name'] ?? 'You',
      'email': userEmail ?? '',
      'bookingId': '#${b['id']}',
      'createdAt': b['created_at']?.toString() ?? '',
      'participants': '${b['attendees'] ?? 0} people',
      'hasStarted': false,
      'can_cancel': b['can_cancel'] == true,
    };
  }

  // ─── AUTH ──────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> login(
      String email, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse(AppConstants.loginUrl),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode({'email': email, 'password': password}),
          )
          .timeout(const Duration(seconds: 15));

      _saveSession(response);
      final data = _decodeBody(response);

      if (response.statusCode == 200 && data['success'] == true) {
        authToken = data['token']?.toString();
        currentUser = data['user'] is Map
            ? Map<String, dynamic>.from(data['user'] as Map)
            : null;
        return {'success': true, 'user': currentUser};
      }
      return {
        'success': false,
        'error': data['error']?.toString() ??
            data['detail']?.toString() ??
            'Login failed. Check credentials.',
      };
    } catch (e) {
      return {
        'success': false,
        'error':
            'Cannot connect to server at ${AppConstants.baseUrl}\n'
            'Start Django: python manage.py runserver ${AppConstants.serverPort}\n$e',
      };
    }
  }

  static Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
  }) async {
    try {
      final response = await http
          .post(
            Uri.parse(AppConstants.registerUrl),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode({
              'email': email,
              'password': password,
              'first_name': firstName,
              'last_name': lastName,
            }),
          )
          .timeout(const Duration(seconds: 15));

      final data = _decodeBody(response);
      if ((response.statusCode == 200 || response.statusCode == 201) &&
          data['success'] == true) {
        return {'success': true, 'message': data['message']?.toString()};
      }
      return {
        'success': false,
        'error': data['error']?.toString() ?? 'Registration failed.',
      };
    } catch (e) {
      return {'success': false, 'error': 'Connection error: $e'};
    }
  }

  static Future<bool> logout() async {
    try {
      await http
          .post(Uri.parse(AppConstants.logoutUrl), headers: _headers)
          .timeout(const Duration(seconds: 10));
    } catch (_) {}
    _sessionCookie = null;
    _csrfToken = null;
    authToken = null;
    currentUser = null;
    return true;
  }

  // ─── ROOMS ─────────────────────────────────────────────────────────────────

  static Future<List<Map<String, dynamic>>> getRooms({
    String? roomType,
    bool availableOnly = false,
  }) async {
    try {
      final params = <String, String>{
        'available_only': availableOnly.toString(),
      };
      if (roomType != null && roomType.isNotEmpty) {
        params['room_type'] = roomType;
      }
      final uri = Uri.parse(AppConstants.roomsUrl).replace(
        queryParameters: params,
      );
      final response = await http
          .get(uri, headers: _headers)
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = _decodeBody(response);
        if (data['rooms'] is List) {
          return List<Map<String, dynamic>>.from(data['rooms'] as List)
              .map((r) => Map<String, dynamic>.from(r as Map))
              .toList();
        }
      }
    } catch (_) {}
    return [];
  }

  static List<Map<String, dynamic>> filterByCapacity(
    List<Map<String, dynamic>> rooms,
    String? capacityRange,
  ) {
    if (capacityRange == null || capacityRange.isEmpty) return rooms;
    return rooms.where((r) {
      final c = (r['capacity'] as num?)?.toInt() ?? 0;
      switch (capacityRange) {
        case '1-10':
          return c >= 1 && c <= 10;
        case '11-30':
          return c >= 11 && c <= 30;
        case '31-50':
          return c >= 31 && c <= 50;
        case '50+':
          return c > 50;
        default:
          return true;
      }
    }).toList();
  }

  // ─── BOOKINGS ──────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getMyBookings() async {
    final email = userEmail;
    if (email == null || email.isEmpty) {
      return {'success': false, 'error': 'Not logged in'};
    }
    try {
      final uri = Uri.parse(AppConstants.bookingsUrl).replace(
        queryParameters: {'user_email': email},
      );
      final response = await http
          .get(uri, headers: _headers)
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        return _decodeBody(response);
      }
    } catch (e) {
      return {'success': false, 'error': '$e'};
    }
    return {'success': false, 'error': 'Failed to load bookings'};
  }

  static Future<Map<String, dynamic>> createBooking({
    required int roomId,
    required String date,
    required String startTime,
    required String endTime,
    required String purpose,
    int attendees = 1,
    String notes = '',
    bool agreedToPolicy = true,
  }) async {
    final email = userEmail;
    if (email == null) {
      return {'success': false, 'error': 'Not logged in'};
    }
    try {
      final response = await http
          .post(
            Uri.parse(AppConstants.createBookingUrl),
            headers: _headers,
            body: jsonEncode({
              'user_email': email,
              'room_id': roomId,
              'date': date,
              'start_time': startTime,
              'end_time': endTime,
              'purpose': purpose,
              'attendees': attendees,
              'notes': notes,
              'agreed_to_room_policy': agreedToPolicy,
            }),
          )
          .timeout(const Duration(seconds: 15));

      final data = _decodeBody(response);
      if (response.statusCode == 200 || response.statusCode == 201) {
        if (data['success'] == true) {
          return {'success': true, 'booking': data['booking']};
        }
      }
      return {
        'success': false,
        'error': data['error']?.toString() ?? 'Booking failed.',
      };
    } catch (e) {
      return {'success': false, 'error': 'Connection error: $e'};
    }
  }

  static Future<Map<String, dynamic>> cancelBooking(int bookingId) async {
    final email = userEmail;
    if (email == null) {
      return {'success': false, 'error': 'Not logged in'};
    }
    try {
      final response = await http
          .post(
            Uri.parse(AppConstants.cancelBookingUrl),
            headers: _headers,
            body: jsonEncode({
              'booking_id': bookingId,
              'user_email': email,
            }),
          )
          .timeout(const Duration(seconds: 10));

      final data = _decodeBody(response);
      if (response.statusCode == 200 && data['success'] == true) {
        return {'success': true};
      }
      return {
        'success': false,
        'error': data['error']?.toString() ?? 'Cancel failed.',
      };
    } catch (e) {
      return {'success': false, 'error': 'Connection error: $e'};
    }
  }

  // ─── CHATBOT ───────────────────────────────────────────────────────────────

  static Future<String> chatWithBot(String message) async {
    try {
      final response = await http
          .post(
            Uri.parse(AppConstants.chatbotUrl),
            headers: _headers,
            body: jsonEncode({'message': message}),
          )
          .timeout(const Duration(seconds: 45));

      if (response.statusCode == 200) {
        final data = _decodeBody(response);
        return data['reply_text']?.toString() ??
            data['response']?.toString() ??
            data['message']?.toString() ??
            'No response from AI.';
      }
      final data = _decodeBody(response);
      return data['reply_text']?.toString() ??
          data['error']?.toString() ??
          'Chatbot error (${response.statusCode}).';
    } catch (e) {
      return 'Error connecting to chatbot: $e';
    }
  }
}
