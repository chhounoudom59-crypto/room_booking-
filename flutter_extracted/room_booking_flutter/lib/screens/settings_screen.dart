import 'package:flutter/material.dart';
import '../widgets/app_page_shell.dart';
import 'login_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  // Color constants matching app theme
  static const Color _primaryColor = Color(0xFF5B4B8A);
  static const Color _backgroundColor = Color(0xFFF5F5F7);
  static const Color _cardColor = Colors.white;
  static const Color _textPrimary = Color(0xFF1A1A2E);
  static const Color _textSecondary = Color(0xFF6B7280);
  static const Color _borderColor = Color(0xFFE5E7EB);

  // Profile data
  String _fullName = "Thun Samaol";
  String _email = "thun.samol.3623@rupp.edu.kh";
  String _studentId = "12334";
  String _phone = "000-000-0000";
  String _faculty = "Not provided";
  String _department = "Not provided";

  // Edit mode state
  bool _isEditing = false;
  bool _isSaving = false;

  // Text editing controllers
  late TextEditingController _nameController;
  late TextEditingController _emailController;
  late TextEditingController _studentIdController;
  late TextEditingController _phoneController;
  late TextEditingController _facultyController;
  late TextEditingController _departmentController;

  @override
  void initState() {
    super.initState();
    _initControllers();
  }

  void _initControllers() {
    _nameController = TextEditingController(text: _fullName);
    _emailController = TextEditingController(text: _email);
    _studentIdController = TextEditingController(text: _studentId);
    _phoneController = TextEditingController(text: _phone);
    _facultyController = TextEditingController(text: _faculty);
    _departmentController = TextEditingController(text: _department);
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _studentIdController.dispose();
    _phoneController.dispose();
    _facultyController.dispose();
    _departmentController.dispose();
    super.dispose();
  }

  void _toggleEditMode() {
    setState(() {
      if (_isEditing) {
        // Cancel editing - reset controllers to original values
        _nameController.text = _fullName;
        _emailController.text = _email;
        _studentIdController.text = _studentId;
        _phoneController.text = _phone;
        _facultyController.text = _faculty;
        _departmentController.text = _department;
      }
      _isEditing = !_isEditing;
    });
  }

  Future<void> _saveProfile() async {
    setState(() {
      _isSaving = true;
    });

    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 800));

    setState(() {
      // Update profile data
      _fullName = _nameController.text;
      _email = _emailController.text;
      _studentId = _studentIdController.text;
      _phone = _phoneController.text;
      _faculty = _facultyController.text;
      _department = _departmentController.text;
      _isEditing = false;
      _isSaving = false;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Row(
            children: [
              Icon(Icons.check_circle, color: Colors.white, size: 20),
              SizedBox(width: 12),
              Text('Profile updated successfully'),
            ],
          ),
          backgroundColor: const Color(0xFF22C55E),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          margin: const EdgeInsets.all(16),
        ),
      );
    }
  }

  void _handleLogout() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: const Text(
          'Log Out',
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: Color(0xFF1A1A2E),
          ),
        ),
        content: const Text(
          'Are you sure you want to log out of your account?',
          style: TextStyle(color: Color(0xFF6B7280)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text(
              'Cancel',
              style: TextStyle(color: Color(0xFF6B7280)),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                    (route) => false,
              );
            },
            child: Text(
              'Log Out',
              style: TextStyle(color: Colors.red.shade400),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AppPageShell(
      title: "Settings",
      child: Container(
        color: _backgroundColor,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            children: [
              // Profile Header
              _buildProfileHeader(),
              const SizedBox(height: 24),

              // Booking & Member Status Row
              Row(
                children: [
                  Expanded(child: _buildStatCard(Icons.calendar_today_outlined, "Bookings", "0")),
                  const SizedBox(width: 12),
                  Expanded(child: _buildStatCard(Icons.event_note_outlined, "Member since", "Oct 2025")),
                ],
              ),
              const SizedBox(height: 24),

              // Personal Information Section
              _buildSection(
                title: "Personal Information",
                icon: Icons.person_outline,
                children: _isEditing
                    ? [
                  _buildEditableField("Full Name", _nameController, Icons.person_outline),
                  _buildEditableField("Email", _emailController, Icons.email_outlined),
                  _buildEditableField("Student ID", _studentIdController, Icons.badge_outlined),
                  _buildEditableField("Phone", _phoneController, Icons.phone_outlined),
                  const SizedBox(height: 8),
                  _buildEditableFacultyRow(),
                ]
                    : [
                  _buildInfoField("Full Name", _fullName),
                  _buildInfoField("Email", _email),
                  _buildInfoField("Student ID", _studentId),
                  _buildInfoField("Phone", _phone),
                  const SizedBox(height: 8),
                  _buildFacultyRow(),
                ],
              ),
              const SizedBox(height: 16),

              // Account Security Section
              _buildSection(
                title: "Account Security",
                icon: Icons.security_outlined,
                children: [
                  _buildInfoField("Last Login", "Nov 20, 2025 08:13"),
                  _buildInfoField("Account Created", "Oct 23, 2025"),
                ],
              ),
              const SizedBox(height: 32),

              // Action Buttons
              if (_isEditing) ...[
                _buildSaveButton(),
                const SizedBox(height: 12),
                _buildCancelButton(),
              ] else ...[
                _buildEditProfileButton(),
                const SizedBox(height: 16),
                _buildLogoutButton(),
              ],
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileHeader() {
    return Column(
      children: [
        // Profile Avatar with subtle shadow
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: _primaryColor, width: 2),
            boxShadow: [
              BoxShadow(
                color: _primaryColor.withValues(alpha: 0.2),
                blurRadius: 20,
                spreadRadius: 2,
              ),
            ],
          ),
          child: CircleAvatar(
            radius: 50,
            backgroundColor: _backgroundColor,
            child: ClipOval(
              child: Image.network(
                'https://img.freepik.com/free-photo/handsome-bearded-guy-posing-against-white-wall_273609-20597.jpg?semt=ais_hybrid&w=740&q=80',
                width: 100,
                height: 100,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return Container(
                    width: 100,
                    height: 100,
                    color: _primaryColor.withValues(alpha: 0.1),
                    child: const Icon(
                      Icons.person,
                      size: 50,
                      color: _primaryColor,
                    ),
                  );
                },
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          _fullName,
          style: const TextStyle(
            color: _textPrimary,
            fontSize: 22,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          _isEditing ? "Edit your profile information" : "Manage your profile and account preferences",
          style: const TextStyle(
            color: _textSecondary,
            fontSize: 14,
          ),
        ),
        if (_isEditing) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _primaryColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.edit, size: 14, color: _primaryColor),
                SizedBox(width: 6),
                Text(
                  "Editing Mode",
                  style: TextStyle(
                    color: _primaryColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildStatCard(IconData icon, String label, String value) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: _primaryColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: _primaryColor, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: _textSecondary,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    color: _textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection({
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Container(
      width: double.infinity,
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
          ...children,
        ],
      ),
    );
  }

  Widget _buildInfoField(String label, String value) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: _backgroundColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _borderColor),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: _textSecondary,
              fontSize: 13,
            ),
          ),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(
                color: _textPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.right,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEditableField(String label, TextEditingController controller, IconData icon) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 4, bottom: 6),
            child: Text(
              label,
              style: const TextStyle(
                color: _textSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          TextFormField(
            controller: controller,
            style: const TextStyle(
              color: _textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: _textSecondary, size: 20),
              filled: true,
              fillColor: Colors.white,
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: _borderColor),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: _borderColor),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: _primaryColor, width: 2),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFacultyRow() {
    return Row(
      children: [
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _backgroundColor,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: _borderColor),
            ),
            child: Row(
              children: [
                const Icon(Icons.badge_outlined, size: 16, color: _textSecondary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    "Faculty: $_faculty",
                    style: const TextStyle(color: _textSecondary, fontSize: 12),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _backgroundColor,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: _borderColor),
            ),
            child: Row(
              children: [
                const Icon(Icons.school_outlined, size: 16, color: _textSecondary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    "Dept: $_department",
                    style: const TextStyle(color: _textSecondary, fontSize: 12),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildEditableFacultyRow() {
    return Column(
      children: [
        _buildEditableField("Faculty", _facultyController, Icons.badge_outlined),
        _buildEditableField("Department", _departmentController, Icons.school_outlined),
      ],
    );
  }

  Widget _buildEditProfileButton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton.icon(
        onPressed: _toggleEditMode,
        icon: const Icon(Icons.edit_outlined, color: Colors.white, size: 20),
        label: const Text(
          "Edit Profile",
          style: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: _primaryColor,
          elevation: 0,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  Widget _buildSaveButton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton.icon(
        onPressed: _isSaving ? null : _saveProfile,
        icon: _isSaving
            ? const SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            color: Colors.white,
          ),
        )
            : const Icon(Icons.check, color: Colors.white, size: 20),
        label: Text(
          _isSaving ? "Saving..." : "Save Changes",
          style: const TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF22C55E),
          elevation: 0,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  Widget _buildCancelButton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: OutlinedButton.icon(
        onPressed: _isSaving ? null : _toggleEditMode,
        icon: Icon(Icons.close, color: _isSaving ? _textSecondary : _textPrimary, size: 20),
        label: Text(
          "Cancel",
          style: TextStyle(
            color: _isSaving ? _textSecondary : _textPrimary,
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: _isSaving ? _borderColor : _textSecondary),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  Widget _buildLogoutButton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: OutlinedButton.icon(
        onPressed: _handleLogout,
        icon: Icon(Icons.logout, color: Colors.red.shade400, size: 20),
        label: Text(
          "Log out",
          style: TextStyle(
            color: Colors.red.shade400,
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
        ),
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: Colors.red.shade300),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }
}
