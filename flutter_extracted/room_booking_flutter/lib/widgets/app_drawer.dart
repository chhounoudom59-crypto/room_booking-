import 'package:flutter/material.dart';
import '../api_service.dart';
import '../screens/home_screen.dart';
import '../screens/login_screen.dart';
import '../screens/booking_screen.dart';
import '../screens/history_screen.dart';
import '../screens/settings_screen.dart';
import '../screens/about_us_screen.dart';
import '../screens/services_screen.dart';
import '../screens/chatbot_screen.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  // ✅ Navigation function
  void _openScreen(BuildContext context, Widget screen) {
    Navigator.pop(context); // close drawer
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => screen),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Drawer(
      backgroundColor: const Color(0xFFF8F9FE),
      child: Column(
        children: [
          // --- Custom Header ---
          Stack(
            children: [
              Container(
                height: 200,
                decoration: const BoxDecoration(
                  image: DecorationImage(
                    image: NetworkImage(
                        'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSuLiRkLoAmr68MxBEBSI64rONsm-Wi8YsgYg&s'),
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              Container(
                height: 200,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      Colors.black.withValues(alpha: 0.7)
                    ],
                  ),
                ),
              ),
              Positioned(
                bottom: 20,
                left: 20,
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 30,
                      backgroundColor: const Color(0xFF6B5B95),
                      child: Text(
                        _drawerUserName().isNotEmpty
                            ? _drawerUserName()[0].toUpperCase()
                            : 'U',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 20,
                        ),
                      ),
                    ),
                    const SizedBox(width: 15),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _drawerUserName(),
                          style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 18),
                        ),
                        Text(
                          ApiService.userEmail ?? 'Not signed in',
                          style: const TextStyle(
                              color: Colors.white70, fontSize: 14),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),

          // --- Menu Items ---
          Expanded(
            child: ListView(
              padding:
              const EdgeInsets.symmetric(horizontal: 15, vertical: 20),
              children: [
                _buildDrawerItem(
                  Icons.home_rounded,
                  'Home',
                      () => _openScreen(context, const HomeScreen()),
                ),
                _buildDrawerItem(
                  Icons.bookmark_rounded,
                  'Booking',
                      () => _openScreen(context, const BookingScreen()),
                ),
                _buildDrawerItem(
                  Icons.history_rounded,
                  'History',
                      () => _openScreen(context, const HistoryScreen()),
                ),
                _buildDrawerItem(
                  Icons.smart_toy_rounded,
                  'AI Assistant',
                      () => _openScreen(context, const ChatbotScreen()),
                ),

                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 10),
                  child: Divider(thickness: 1, color: Colors.black12),
                ),

                _buildDrawerItem(
                  Icons.settings_suggest_rounded,
                  'Settings',
                      () => _openScreen(context, const SettingsScreen()),
                ),
                _buildDrawerItem(
                  Icons.info_outline_rounded,
                  'About Us',
                      () => _openScreen(context, const AboutUsScreen()),
                ),
                _buildDrawerItem(
                  Icons.miscellaneous_services_rounded,
                  'Services',
                      () => _openScreen(context, const ServicesScreen()),
                ),
              ],
            ),
          ),

          // --- Logout ---
          Padding(
            padding: const EdgeInsets.all(20.0),
            child: OutlinedButton(
              onPressed: () async {
                Navigator.pop(context);
                await ApiService.logout();
                if (context.mounted) {
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(builder: (_) => const LoginScreen()),
                    (_) => false,
                  );
                }
              },
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(double.infinity, 45),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(25)),
              ),
              child: const Text("Logout"),
            ),
          ),
        ],
      ),
    );
  }

  String _drawerUserName() {
    final u = ApiService.currentUser;
    if (u == null) return 'RUPP User';
    final first = u['first_name']?.toString() ?? '';
    final last = u['last_name']?.toString() ?? '';
    final name = '$first $last'.trim();
    return name.isEmpty ? 'RUPP User' : name;
  }

  Widget _buildDrawerItem(
      IconData icon, String title, VoidCallback onTap) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            spreadRadius: 2,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ListTile(
        leading: Icon(icon, color: Colors.blueAccent),
        title: Text(
          title,
          style: const TextStyle(
              fontWeight: FontWeight.w500, color: Colors.black87),
        ),
        onTap: onTap,
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}