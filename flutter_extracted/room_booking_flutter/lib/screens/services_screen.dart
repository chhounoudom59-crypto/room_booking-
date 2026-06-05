import 'package:flutter/material.dart';
import '../widgets/app_page_shell.dart';

class ServicesScreen extends StatelessWidget {
  const ServicesScreen({super.key});

  // Color constants matching the app's design system
  static const Color _primaryColor = Color(0xFF5B4B8A);
  static const Color _secondaryColor = Color(0xFF4A90E2);
  static const Color _backgroundColor = Color(0xFFF8F9FA);
  static const Color _cardColor = Colors.white;
  static const Color _textPrimary = Color(0xFF1F2937);
  static const Color _textSecondary = Color(0xFF6B7280);
  static const Color _borderColor = Color(0xFFE5E7EB);

  @override
  Widget build(BuildContext context) {
    return AppPageShell(
      title: "Services",
      child: Container(
        color: _backgroundColor,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              _buildServiceSupportBanner(),
              const SizedBox(height: 24),

              // Quick Help Section
              _buildSectionTitle(Icons.help_outline, "Quick Help"),
              const SizedBox(height: 16),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildQuickHelpCard(
                      "How to Book\na Room",
                      Icons.bed_outlined,
                      "Step-by-step guide to booking your perfect room.",
                    ),
                    _buildQuickHelpCard(
                      "Manage\nBookings",
                      Icons.calendar_month,
                      "View, modify, or cancel your existing bookings.",
                    ),
                    _buildQuickHelpCard(
                      "Account\nSettings",
                      Icons.person_outline,
                      "Update your profile and preferences.",
                    ),
                    _buildQuickHelpCard(
                      "Contact\nSupport",
                      Icons.phone_in_talk,
                      "Get help from our support team.",
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // FAQ Section
              _buildSectionTitle(
                Icons.question_answer_outlined,
                "Frequently Asked Questions",
              ),
              const SizedBox(height: 16),
              _buildFAQTile("How do I book a room?", false),
              _buildFAQTile("Can I cancel or modify my booking?", true),
              _buildFAQTile("What are the room booking policies?", false),

              const SizedBox(height: 32),

              // Room Booking Guide
              _buildSectionTitle(Icons.school_outlined, "Room Booking Guide"),
              const SizedBox(height: 16),
              _buildBookingSteps(),

              const SizedBox(height: 32),

              // Contact Form
              _buildContactForm(),

              const SizedBox(height: 32),
              _buildContactInfoSection(),
              const SizedBox(height: 20),
              _buildSupportHoursSection(),
              const SizedBox(height: 20),
              _buildLegalPolicySection(),
              const SizedBox(height: 20),
              _buildFollowUsSection(),
              const SizedBox(height: 20),
              _buildQuickLinksSection(),

              const SizedBox(height: 32),
              _buildFooter(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  // Banner
  Widget _buildServiceSupportBanner() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            _primaryColor,
            _primaryColor.withValues(alpha: 0.8),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: _primaryColor.withValues(alpha: 0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.headset_mic_outlined,
              color: Colors.white,
              size: 32,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            "Service & Support",
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "We're here to help you with all your room booking needs",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.9),
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(IconData icon, String title) {
    return Row(
      children: [
        Icon(icon, color: _primaryColor, size: 20),
        const SizedBox(width: 10),
        Text(
          title,
          style: const TextStyle(
            color: _textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  // Quick Help Cards
  Widget _buildQuickHelpCard(String title, IconData icon, String desc) {
    return Container(
      width: 150,
      height: 200,
      margin: const EdgeInsets.only(right: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _primaryColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: _primaryColor, size: 28),
          ),
          const SizedBox(height: 12),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: _textPrimary,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: Text(
              desc,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: _textSecondary,
                fontSize: 11,
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "Learn More",
            style: TextStyle(
              color: _secondaryColor,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // FAQ Section
  Widget _buildFAQTile(String question, bool isExpanded) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: _cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Theme(
        data: ThemeData().copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          initiallyExpanded: isExpanded,
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          title: Text(
            question,
            style: const TextStyle(
              color: _textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          iconColor: _primaryColor,
          collapsedIconColor: _textSecondary,
          children: [
            Text(
              "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
              style: TextStyle(
                color: _textSecondary,
                fontSize: 13,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Booking Steps
  Widget _buildBookingSteps() {
    return Row(
      children: [
        _stepBox("1", "Choose Your Room"),
        const SizedBox(width: 12),
        _stepBox("2", "Select Date & Time"),
        const SizedBox(width: 12),
        _stepBox("3", "Fill Details"),
      ],
    );
  }

  Widget _stepBox(String num, String text) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: _cardColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: _borderColor),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: _primaryColor,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Center(
                child: Text(
                  num,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: _textPrimary,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Contact Form
  Widget _buildContactForm() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.send_outlined, color: _primaryColor, size: 20),
              const SizedBox(width: 10),
              const Text(
                "Send us a Message",
                style: TextStyle(
                  color: _textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _formField("Name"),
          const SizedBox(height: 12),
          _formField("Email address"),
          const SizedBox(height: 12),
          _formField("Subject"),
          const SizedBox(height: 12),
          _formField("Message", maxLines: 4),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              onPressed: () {},
              style: ElevatedButton.styleFrom(
                backgroundColor: _primaryColor,
                foregroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                "Send Message",
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _formField(String hint, {int maxLines = 1}) {
    return TextField(
      maxLines: maxLines,
      style: const TextStyle(color: _textPrimary, fontSize: 14),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: _textSecondary, fontSize: 14),
        filled: true,
        fillColor: _backgroundColor,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: _borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: _borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: _primaryColor, width: 1.5),
        ),
      ),
    );
  }

  // Contact Info Section
  Widget _buildContactInfoSection() {
    return _buildSectionContainer(
      title: "Contact Information",
      icon: Icons.contact_page_outlined,
      children: [
        _buildDetailRow(Icons.phone, "Phone Number: +855 072 274 4936"),
        _buildDetailRow(
          Icons.email_outlined,
          "Email Address: roombooking@rupp.edu.kh",
        ),
        _buildDetailRow(
          Icons.location_on_outlined,
          "Office Location: DSE Support Office, Building STEM, Room 306",
        ),
      ],
    );
  }

  Widget _buildSupportHoursSection() {
    return _buildSectionContainer(
      title: "Support Hours",
      icon: Icons.access_time,
      children: [
        const Text(
          "Regular Support: Monday - Friday, 8:00 AM - 5:00 PM\n"
              "Weekend Support: Saturday, 9:00 AM - 2:00 PM\n"
              "Emergency Support: 24/7 for urgent issues",
          style: TextStyle(
            color: _textSecondary,
            fontSize: 13,
            height: 1.6,
          ),
        ),
      ],
    );
  }

  Widget _buildLegalPolicySection() {
    return _buildSectionContainer(
      title: "Legal & Policy",
      icon: Icons.description_outlined,
      children: [
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            _buildPolicyChip("Privacy Policy", Icons.shield_outlined),
            _buildPolicyChip("Terms of Use", Icons.assignment_outlined),
            _buildPolicyChip("Cookie Policy", Icons.cookie_outlined),
          ],
        ),
      ],
    );
  }

  Widget _buildFollowUsSection() {
    return _buildSectionContainer(
      title: "Follow Us",
      icon: Icons.rss_feed,
      children: [
        Row(
          children: [
            Expanded(
              child: _buildSocialButton(
                "Facebook",
                const Color(0xFF3B5998),
                Icons.facebook,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildSocialButton(
                "Telegram",
                const Color(0xFF0088CC),
                Icons.telegram,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            _buildSmallSocialChip("TikTok", _textPrimary),
            const SizedBox(width: 8),
            _buildSmallSocialChip("X", _textPrimary),
            const SizedBox(width: 8),
            _buildSmallSocialChip("Instagram", const Color(0xFFE1306C)),
          ],
        ),
      ],
    );
  }

  Widget _buildQuickLinksSection() {
    return _buildSectionContainer(
      title: "Quick Links",
      icon: Icons.list,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                children: [
                  _buildQuickLink(Icons.home, "Home"),
                  _buildQuickLink(Icons.group, "About Us"),
                  _buildQuickLink(Icons.calendar_today, "Room Booking"),
                ],
              ),
            ),
            Expanded(
              child: Column(
                children: [
                  _buildQuickLink(Icons.format_list_bulleted, "My Bookings"),
                  _buildQuickLink(Icons.help_outline, "Help / FAQ"),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  // Generic Helpers
  Widget _buildSectionContainer({
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: _primaryColor, size: 20),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(
                  color: _textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Divider(color: _borderColor, height: 1),
          const SizedBox(height: 16),
          ...children,
        ],
      ),
    );
  }

  Widget _buildDetailRow(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: _primaryColor, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: _textSecondary,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPolicyChip(String label, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: _primaryColor.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _primaryColor.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: _primaryColor),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: _primaryColor,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSocialButton(String label, Color color, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: Colors.white, size: 20),
          const SizedBox(width: 8),
          Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSmallSocialChip(String label, Color color) {
    return Expanded(
      child: Container(
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withValues(alpha: 0.2)),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _buildQuickLink(IconData icon, String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Icon(icon, color: _primaryColor, size: 18),
          const SizedBox(width: 10),
          Text(
            label,
            style: const TextStyle(
              color: _textPrimary,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFooter() {
    return Center(
      child: Column(
        children: [
          Divider(color: _borderColor, height: 1),
          const SizedBox(height: 20),
          Text(
            "All Rights Reserved, Copyright 2025\nRoyal University of Phnom Penh (RUPP)",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: _textSecondary,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "Russian Federation Boulevard, Toul Kork,\nPhnom Penh, Cambodia\nTel: 855-072 21 936",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: _textSecondary.withValues(alpha: 0.7),
              fontSize: 11,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "Designed by: DSE TEAM",
            style: TextStyle(
              color: _primaryColor,
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}