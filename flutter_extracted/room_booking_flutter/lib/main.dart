import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const IntelligentUniversityRoomBookingSystem());
}

class IntelligentUniversityRoomBookingSystem extends StatelessWidget {
  const IntelligentUniversityRoomBookingSystem({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: LoginScreen(),
    );
  }
}

