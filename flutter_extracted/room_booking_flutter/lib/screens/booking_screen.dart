import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../api_service.dart';
import '../widgets/app_page_shell.dart';

class BookingScreen extends StatefulWidget {
  final String? preSelectedRoom;
  final int? preSelectedRoomId;

  const BookingScreen({super.key, this.preSelectedRoom, this.preSelectedRoomId});

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  // Color system
  static const Color primaryColor = Color(0xFF5B4B8A);
  static const Color secondaryColor = Color(0xFF4A90E2);
  static const Color backgroundColor = Color(0xFFF8F9FA);
  static const Color cardBackground = Colors.white;
  static const Color borderColor = Color(0xFFE5E7EB);
  static const Color textPrimary = Color(0xFF1F2937);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color textMuted = Color(0xFF9CA3AF);

  // Form state
  String? selectedRoom;
  DateTime? selectedDate;
  TimeOfDay? startTime;
  TimeOfDay? endTime;
  String? selectedPurpose;
  final TextEditingController attendeesController = TextEditingController();
  final TextEditingController notesController = TextEditingController();

  List<Map<String, dynamic>> _apiRooms = [];
  bool _loadingRooms = true;
  int? _selectedRoomId;

  final List<String> purposes = [
    'Meeting',
    'Presentation',
    'Training',
    'Interview',
    'Workshop',
    'Other',
  ];

  @override
  void initState() {
    super.initState();
    _loadRooms();
  }

  Future<void> _loadRooms() async {
    final raw = await ApiService.getRooms(availableOnly: false);
    if (!mounted) return;
    String? name = widget.preSelectedRoom;
    int? id = widget.preSelectedRoomId;
    for (final r in raw) {
      if (id != null && r['id'] == id) {
        name = r['name']?.toString();
        break;
      }
      if (name != null && r['name'] == name) {
        id = r['id'] as int?;
        break;
      }
    }
    setState(() {
      _apiRooms = raw;
      _loadingRooms = false;
      _selectedRoomId = id;
      selectedRoom = name;
    });
  }

  List<String> get _roomNames =>
      _apiRooms.map((r) => r['name']?.toString() ?? '').where((n) => n.isNotEmpty).toList();

  @override
  void dispose() {
    attendeesController.dispose();
    notesController.dispose();
    super.dispose();
  }

  Future<void> _selectDate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: selectedDate ?? DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: primaryColor,
              onPrimary: Colors.white,
              surface: cardBackground,
              onSurface: textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        selectedDate = picked;
      });
    }
  }

  Future<void> _selectTime(bool isStartTime) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: isStartTime
          ? (startTime ?? TimeOfDay.now())
          : (endTime ?? TimeOfDay.now()),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: primaryColor,
              onPrimary: Colors.white,
              surface: cardBackground,
              onSurface: textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        if (isStartTime) {
          startTime = picked;
        } else {
          endTime = picked;
        }
      });
    }
  }

  String _formatDate(DateTime? date) {
    if (date == null) return '';
    return '${date.month.toString().padLeft(2, '0')}/${date.day.toString().padLeft(2, '0')}/${date.year}';
  }

  String _formatTime(TimeOfDay? time) {
    if (time == null) return '';
    final hour = time.hourOfPeriod == 0 ? 12 : time.hourOfPeriod;
    final period = time.period == DayPeriod.am ? 'AM' : 'PM';
    return '${hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')} $period';
  }

  Future<void> _submitBooking() async {
    if (_selectedRoomId == null || selectedRoom == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a room.')),
      );
      return;
    }
    if (selectedDate == null || startTime == null || endTime == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select date and time.')),
      );
      return;
    }
    if (selectedPurpose == null || selectedPurpose!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a purpose.')),
      );
      return;
    }

    final date =
        '${selectedDate!.year}-${selectedDate!.month.toString().padLeft(2, '0')}-${selectedDate!.day.toString().padLeft(2, '0')}';
    final start =
        '${startTime!.hour.toString().padLeft(2, '0')}:${startTime!.minute.toString().padLeft(2, '0')}';
    final end =
        '${endTime!.hour.toString().padLeft(2, '0')}:${endTime!.minute.toString().padLeft(2, '0')}';
    final attendees = int.tryParse(attendeesController.text.trim()) ?? 1;

    final result = await ApiService.createBooking(
      roomId: _selectedRoomId!,
      date: date,
      startTime: start,
      endTime: end,
      purpose: selectedPurpose!,
      attendees: attendees,
      notes: notesController.text.trim(),
    );

    if (!mounted) return;
    if (result['success'] == true) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['booking']?['room_name'] != null
              ? 'Booked ${result['booking']['room_name']}'
              : 'Booking submitted successfully'),
          backgroundColor: primaryColor,
        ),
      );
      Navigator.of(context).pop();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['error']?.toString() ?? 'Booking failed'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppPageShell(
      title: "Booking",
      child: Container(
        color: backgroundColor,
        child: Stack(
          children: [
            // Main scrollable content
            SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Room Selection Card
                  _buildSectionCard(
                    children: [
                      _buildSectionLabel('Room'),
                      const SizedBox(height: 8),
                      _loadingRooms
                          ? const Center(child: CircularProgressIndicator())
                          : _buildDropdownField(
                              value: selectedRoom,
                              hint: 'Select Room',
                              items: _roomNames,
                              onChanged: (value) {
                                int? id;
                                for (final r in _apiRooms) {
                                  if (r['name'] == value) {
                                    id = r['id'] as int?;
                                    break;
                                  }
                                }
                                setState(() {
                                  selectedRoom = value;
                                  _selectedRoomId = id;
                                });
                              },
                            ),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // Date Selection Card
                  _buildSectionCard(
                    children: [
                      _buildSectionLabel('Date'),
                      const SizedBox(height: 8),
                      _buildDateField(),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // Time Selection Card
                  _buildSectionCard(
                    children: [
                      _buildSectionLabel('Time'),
                      const SizedBox(height: 8),
                      _buildTimeField(
                        label: 'Start Time',
                        time: startTime,
                        onTap: () => _selectTime(true),
                      ),
                      const SizedBox(height: 12),
                      _buildTimeField(
                        label: 'End Time',
                        time: endTime,
                        onTap: () => _selectTime(false),
                      ),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // Purpose Selection Card
                  _buildSectionCard(
                    children: [
                      _buildSectionLabel('Purpose'),
                      const SizedBox(height: 8),
                      _buildDropdownField(
                        value: selectedPurpose,
                        hint: 'Select booking purpose',
                        items: purposes,
                        onChanged: (value) {
                          setState(() {
                            selectedPurpose = value;
                          });
                        },
                      ),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // Attendees Card
                  _buildSectionCard(
                    children: [
                      _buildSectionLabel('Number of Attendees'),
                      const SizedBox(height: 8),
                      _buildTextField(
                        controller: attendeesController,
                        hint: 'Enter number of attendees',
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.digitsOnly,
                        ],
                      ),
                    ],
                  ),

                  const SizedBox(height: 16),

                  // Additional Notes Card
                  _buildSectionCard(
                    children: [
                      _buildSectionLabel('Additional Notes'),
                      const SizedBox(height: 8),
                      _buildTextAreaField(
                        controller: notesController,
                        hint: 'Any special requirements or notes...',
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Floating Action Button
            Positioned(
              right: 16,
              bottom: 88,
              child: _buildFloatingActionButton(),
            ),

            // Sticky Bottom Button
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: _buildBottomButton(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionCard({required List<Widget> children}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBackground,
        borderRadius: BorderRadius.circular(12),
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
        children: children,
      ),
    );
  }

  Widget _buildSectionLabel(String label) {
    return Text(
      label,
      style: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w500,
        color: textPrimary,
        letterSpacing: -0.2,
      ),
    );
  }

  Widget _buildDropdownField({
    required String? value,
    required String hint,
    required List<String> items,
    required ValueChanged<String?> onChanged,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: cardBackground,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor, width: 1),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          hint: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              hint,
              style: const TextStyle(
                color: textMuted,
                fontSize: 15,
              ),
            ),
          ),
          isExpanded: true,
          icon: const Padding(
            padding: EdgeInsets.only(right: 12),
            child: Icon(
              Icons.keyboard_arrow_down_rounded,
              color: textSecondary,
            ),
          ),
          borderRadius: BorderRadius.circular(12),
          padding: const EdgeInsets.symmetric(horizontal: 4),
          items: items.map((String item) {
            return DropdownMenuItem<String>(
              value: item,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  item,
                  style: const TextStyle(
                    color: textPrimary,
                    fontSize: 15,
                  ),
                ),
              ),
            );
          }).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }

  Widget _buildDateField() {
    return GestureDetector(
      onTap: _selectDate,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: cardBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor, width: 1),
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                selectedDate != null
                    ? _formatDate(selectedDate)
                    : 'mm/dd/yyyy',
                style: TextStyle(
                  color: selectedDate != null ? textPrimary : textMuted,
                  fontSize: 15,
                ),
              ),
            ),
            const Icon(
              Icons.calendar_today_outlined,
              color: textSecondary,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeField({
    required String label,
    required TimeOfDay? time,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: cardBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor, width: 1),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      color: textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    time != null ? _formatTime(time) : 'Select time',
                    style: TextStyle(
                      color: time != null ? textPrimary : textMuted,
                      fontSize: 15,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.access_time_rounded,
              color: textSecondary,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String hint,
    TextInputType? keyboardType,
    List<TextInputFormatter>? inputFormatters,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      inputFormatters: inputFormatters,
      style: const TextStyle(
        color: textPrimary,
        fontSize: 15,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(
          color: textMuted,
          fontSize: 15,
        ),
        filled: true,
        fillColor: cardBackground,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderColor, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderColor, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: secondaryColor, width: 1.5),
        ),
      ),
    );
  }

  Widget _buildTextAreaField({
    required TextEditingController controller,
    required String hint,
  }) {
    return TextField(
      controller: controller,
      maxLines: 4,
      style: const TextStyle(
        color: textPrimary,
        fontSize: 15,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(
          color: textMuted,
          fontSize: 15,
        ),
        filled: true,
        fillColor: cardBackground,
        contentPadding: const EdgeInsets.all(16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderColor, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderColor, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: secondaryColor, width: 1.5),
        ),
      ),
    );
  }

  Widget _buildFloatingActionButton() {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          // Open support/chat
        },
        borderRadius: BorderRadius.circular(28),
        child: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: secondaryColor.withValues(alpha: 0.9),
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: secondaryColor.withValues(alpha: 0.3),
                blurRadius: 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: const Icon(
            Icons.support_agent_rounded,
            color: Colors.white,
            size: 22,
          ),
        ),
      ),
    );
  }

  Widget _buildBottomButton() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBackground,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 10,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: _PressableButton(
          onPressed: _submitBooking,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: primaryColor,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: primaryColor.withValues(alpha: 0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Text(
              'Book Now',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.3,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// Custom pressable button with scale animation
class _PressableButton extends StatefulWidget {
  final Widget child;
  final VoidCallback onPressed;

  const _PressableButton({
    required this.child,
    required this.onPressed,
  });

  @override
  State<_PressableButton> createState() => _PressableButtonState();
}

class _PressableButtonState extends State<_PressableButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 150),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.97).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) {
        _controller.reverse();
        widget.onPressed();
      },
      onTapCancel: () => _controller.reverse(),
      child: AnimatedBuilder(
        animation: _scaleAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: child,
          );
        },
        child: widget.child,
      ),
    );
  }
}
