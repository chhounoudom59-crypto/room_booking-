import 'package:flutter/material.dart';
import '../api_service.dart';
import '../widgets/app_page_shell.dart';
import 'booking_screen.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  // Color palette
  static const Color primaryColor = Color(0xFF5B4B8A);
  static const Color secondaryColor = Color(0xFF4A90E2);
  static const Color successColor = Color(0xFF4CAF50);
  static const Color backgroundColor = Color(0xFFF5F5F5);
  static const Color cardBackground = Colors.white;
  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color borderColor = Color(0xFFE5E7EB);
  static const Color dividerColor = Color(0xFFEEEEEE);

  List<Map<String, dynamic>> _upcomingBookings = [];
  List<Map<String, dynamic>> _bookingHistory = [];
  bool _loading = true;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _loadBookings();
  }

  Future<void> _loadBookings() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });
    final data = await ApiService.getMyBookings();
    if (!mounted) return;
    if (data['success'] == true) {
      final upcoming = (data['upcoming_bookings'] as List? ?? [])
          .map((b) => ApiService.mapBookingForHistory(
              Map<String, dynamic>.from(b as Map)))
          .toList();
      final past = (data['past_bookings'] as List? ?? [])
          .map((b) => ApiService.mapBookingForHistory(
              Map<String, dynamic>.from(b as Map)))
          .toList();
      setState(() {
        _upcomingBookings = upcoming;
        _bookingHistory = past;
        _loading = false;
      });
    } else {
      setState(() {
        _loadError = data['error']?.toString() ?? 'Failed to load bookings';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppPageShell(
      title: "My Bookings",
      child: Container(
        color: backgroundColor,
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header Section
                      _buildHeaderSection(),
                      const SizedBox(height: 24),
                      if (_loading)
                        const Center(
                          child: Padding(
                            padding: EdgeInsets.all(32),
                            child: CircularProgressIndicator(
                              color: primaryColor,
                            ),
                          ),
                        )
                      else if (_loadError != null)
                        Padding(
                          padding: const EdgeInsets.all(16),
                          child: Text(
                            _loadError!,
                            style: const TextStyle(color: textSecondary),
                          ),
                        )
                      else ...[
                      // Summary Cards Row
                      _buildSummaryCardsRow(),
                      const SizedBox(height: 32),

                      // Upcoming Bookings Section
                      _buildUpcomingBookingsSection(),
                      const SizedBox(height: 32),

                      // Booking History Section
                      _buildBookingHistorySection(),
                      const SizedBox(height: 24),
                      ],
                    ],
                  ),
                ),
              ),
            ),

            // Bottom Action Buttons
            _buildBottomActionButtons(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'My Bookings',
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
            color: textPrimary,
            letterSpacing: -0.5,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'View and manage your room bookings',
          style: TextStyle(
            fontSize: 15,
            color: textSecondary,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryCardsRow() {
    final int totalBookings = _upcomingBookings.length + _bookingHistory.length;
    final int confirmedCount = _bookingHistory
        .where((b) => b['status'] == 'Confirmed')
        .length + _upcomingBookings.length;
    final int cancelledCount = _bookingHistory
        .where((b) => b['status'] == 'Cancelled')
        .length;

    return Row(
      children: [
        Expanded(
          child: _buildSummaryCard(
            icon: Icons.calendar_today_outlined,
            label: 'Total Bookings',
            count: totalBookings.toString(),
            iconColor: primaryColor,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildSummaryCard(
            icon: Icons.check_circle_outline,
            label: 'Confirmed',
            count: confirmedCount.toString(),
            iconColor: successColor,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildSummaryCard(
            icon: Icons.cancel_outlined,
            label: 'Cancelled',
            count: cancelledCount.toString(),
            iconColor: textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryCard({
    required IconData icon,
    required String label,
    required String count,
    required Color iconColor,
  }) {
    return Container(
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
        children: [
          Icon(
            icon,
            size: 24,
            color: iconColor,
          ),
          const SizedBox(height: 12),
          Text(
            count,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildUpcomingBookingsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Upcoming Bookings',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: textPrimary,
          ),
        ),
        const SizedBox(height: 16),
        if (_upcomingBookings.isEmpty)
          _buildEmptyUpcomingCard()
        else
          ..._upcomingBookings.map((booking) => _buildBookingCard(booking)),
      ],
    );
  }

  Widget _buildEmptyUpcomingCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: cardBackground,
        borderRadius: BorderRadius.circular(16),
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
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: backgroundColor,
              borderRadius: BorderRadius.circular(32),
            ),
            child: Icon(
              Icons.calendar_month_outlined,
              size: 32,
              color: textSecondary.withValues(alpha: 0.6),
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'No Upcoming Bookings',
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w600,
              color: textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'You don\'t have any upcoming room bookings.\nBook a room to get started.',
            style: TextStyle(
              fontSize: 14,
              color: textSecondary,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          _buildPrimaryButton(
            label: 'Book a Room',
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (context) => const BookingScreen(),
                ),
              );
            },
            width: 160,
          ),
        ],
      ),
    );
  }

  Widget _buildBookingHistorySection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Booking History',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: textPrimary,
          ),
        ),
        const SizedBox(height: 16),
        ..._bookingHistory.map((booking) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: _buildBookingCard(booking),
        )),
      ],
    );
  }

  Widget _buildBookingCard(Map<String, dynamic> booking) {
    final bool isConfirmed = booking['status'] == 'Confirmed';

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: cardBackground,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Room name and status row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    booking['roomName'],
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: textPrimary,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                _buildStatusBadge(booking['status'], isConfirmed),
              ],
            ),
            const SizedBox(height: 12),

            // Divider
            Container(
              height: 1,
              color: dividerColor,
            ),
            const SizedBox(height: 12),

            // Booking details
            _buildDetailRow(Icons.location_on_outlined, booking['building']),
            const SizedBox(height: 8),
            _buildDetailRow(Icons.calendar_today_outlined, booking['date']),
            const SizedBox(height: 8),
            _buildDetailRow(Icons.access_time_outlined, booking['time']),
            const SizedBox(height: 8),
            _buildDetailRow(Icons.assignment_outlined, booking['purpose']),
            const SizedBox(height: 16),

            // View Details button
            Align(
              alignment: Alignment.centerRight,
              child: _buildOutlinedButton(
                label: 'View Details',
                onPressed: () {
                  _showBookingDetailDialog(booking);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showBookingDetailDialog(Map<String, dynamic> booking) {
    final bool hasStarted = booking['hasStarted'] ?? false;

    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: const EdgeInsets.all(16),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
          decoration: BoxDecoration(
            color: cardBackground,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.15),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Decorative top gradient border
              Container(
                height: 4,
                decoration: BoxDecoration(
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                  gradient: LinearGradient(
                    colors: [
                      primaryColor.withValues(alpha: 0.6),
                      secondaryColor.withValues(alpha: 0.6),
                    ],
                  ),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 24, 24, 16),
                child: Column(
                  children: [
                    Text(
                      'Booking Detail',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: textPrimary,
                        fontFamily: 'Georgia',
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'View and manage your booking information',
                      style: TextStyle(
                        fontSize: 13,
                        color: textSecondary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),

              // Scrollable content
              Flexible(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Column(
                    children: [
                      // Booking Information Section
                      _buildInfoSection(
                        icon: Icons.calendar_today_outlined,
                        title: 'Booking Information',
                        rows: [
                          _InfoRow('Title', 'Room Booking'),
                          _InfoRow('Purpose', booking['purpose'] ?? 'N/A'),
                          _InfoRow('Participants', booking['participants'] ?? '1 people'),
                        ],
                      ),
                      const SizedBox(height: 20),

                      // Location Details Section
                      _buildInfoSection(
                        icon: Icons.location_on_outlined,
                        title: 'Location Details',
                        rows: [
                          _InfoRow('Room', booking['roomName'] ?? 'N/A'),
                          _InfoRow('Building Name', booking['building'] ?? 'N/A'),
                          _InfoRow('Capacity', booking['capacity'] ?? 'N/A'),
                        ],
                      ),
                      const SizedBox(height: 20),

                      // Time & Date Section
                      _buildInfoSection(
                        icon: Icons.access_time_outlined,
                        title: 'Time & Date',
                        rows: [
                          _InfoRow('Date', booking['date'] ?? 'N/A'),
                          _InfoRow('Start Time', booking['startTime'] ?? 'N/A'),
                          _InfoRow('End Time', booking['endTime'] ?? 'N/A'),
                          _InfoRow('Duration', booking['duration'] ?? 'N/A'),
                        ],
                      ),
                      const SizedBox(height: 20),

                      // Booking Details Section
                      _buildInfoSection(
                        icon: Icons.person_outline,
                        title: 'Booking Details',
                        rows: [
                          _InfoRow('Booked By', booking['bookedBy'] ?? 'N/A'),
                          _InfoRow('Email', booking['email'] ?? 'N/A'),
                          _InfoRow('Booking ID', booking['bookingId'] ?? 'N/A'),
                          _InfoRow('Created', booking['createdAt'] ?? 'N/A'),
                        ],
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),

              // Action Footer
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFFFAFAFA),
                  borderRadius: const BorderRadius.vertical(bottom: Radius.circular(16)),
                  border: Border(
                    top: BorderSide(
                      color: borderColor,
                      width: 1,
                    ),
                  ),
                ),
                child: Column(
                  children: [
                    // Action Buttons Row
                    Row(
                      children: [
                        // Back to Bookings Button
                        Expanded(
                          flex: 3,
                          child: _DialogButton(
                            label: 'Back to Bookings',
                            icon: Icons.arrow_back,
                            isPrimary: true,
                            onPressed: () => Navigator.of(context).pop(),
                          ),
                        ),
                        const SizedBox(width: 12),
                        // Status Button
                        Expanded(
                          flex: 2,
                          child: _DialogButton(
                            label: hasStarted ? 'Booking Started' : 'Pending',
                            icon: hasStarted ? Icons.play_arrow : Icons.schedule,
                            isPrimary: false,
                            isDisabled: true,
                            onPressed: null,
                          ),
                        ),
                      ],
                    ),
                    if (hasStarted) ...[
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.play_arrow,
                            size: 14,
                            color: textSecondary,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'Cannot cancel - Booking has already started.',
                            style: TextStyle(
                              fontSize: 12,
                              fontStyle: FontStyle.italic,
                              color: textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoSection({
    required IconData icon,
    required String title,
    required List<_InfoRow> rows,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFAFAFA),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Section Header
          Row(
            children: [
              Icon(
                icon,
                size: 18,
                color: primaryColor,
              ),
              const SizedBox(width: 8),
              Text(
                title,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: textPrimary,
                  fontFamily: 'Georgia',
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          // Info Rows
          ...rows.asMap().entries.map((entry) {
            final index = entry.key;
            final row = entry.value;
            final isLast = index == rows.length - 1;
            return Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      row.label,
                      style: TextStyle(
                        fontSize: 13,
                        color: textSecondary,
                      ),
                    ),
                    Flexible(
                      child: Text(
                        row.value,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: textPrimary,
                        ),
                        textAlign: TextAlign.right,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                if (!isLast) ...[
                  const SizedBox(height: 10),
                  Container(
                    height: 1,
                    color: borderColor,
                  ),
                  const SizedBox(height: 10),
                ],
              ],
            );
          }),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status, bool isConfirmed) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: isConfirmed
            ? successColor.withValues(alpha: 0.1)
            : textSecondary.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        status,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: isConfirmed ? successColor : textSecondary,
        ),
      ),
    );
  }

  Widget _buildDetailRow(IconData icon, String text) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: textSecondary,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              fontSize: 14,
              color: textSecondary,
              height: 1.3,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBottomActionButtons() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBackground,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            Expanded(
              child: _buildOutlinedButton(
                label: 'Back',
                onPressed: () {
                  Navigator.pop(context);
                },
                isFullWidth: true,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildPrimaryButton(
                label: 'New Booking',
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => const BookingScreen(),
                    ),
                  );
                },
                isFullWidth: true,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPrimaryButton({
    required String label,
    required VoidCallback onPressed,
    double? width,
    bool isFullWidth = false,
  }) {
    return _AnimatedButton(
      onPressed: onPressed,
      child: Container(
        width: isFullWidth ? double.infinity : width,
        height: 48,
        decoration: BoxDecoration(
          color: primaryColor,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: primaryColor.withValues(alpha: 0.25),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Center(
          child: Text(
            label,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildOutlinedButton({
    required String label,
    required VoidCallback onPressed,
    bool isFullWidth = false,
  }) {
    return _AnimatedButton(
      onPressed: onPressed,
      child: Container(
        width: isFullWidth ? double.infinity : null,
        height: 48,
        padding: isFullWidth ? null : const EdgeInsets.symmetric(horizontal: 20),
        decoration: BoxDecoration(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: primaryColor,
            width: 1.5,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: primaryColor,
            ),
          ),
        ),
      ),
    );
  }
}

class _InfoRow {
  final String label;
  final String value;

  _InfoRow(this.label, this.value);
}

class _DialogButton extends StatefulWidget {
  final String label;
  final IconData icon;
  final bool isPrimary;
  final bool isDisabled;
  final VoidCallback? onPressed;

  const _DialogButton({
    required this.label,
    required this.icon,
    this.isPrimary = false,
    this.isDisabled = false,
    this.onPressed,
  });

  @override
  State<_DialogButton> createState() => _DialogButtonState();
}

class _DialogButtonState extends State<_DialogButton> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    const Color primaryColor = Color(0xFF374151);
    const Color disabledColor = Color(0xFFE5E7EB);
    const Color disabledTextColor = Color(0xFF9CA3AF);

    return GestureDetector(
      onTapDown: widget.isDisabled ? null : (_) => setState(() => _isPressed = true),
      onTapUp: widget.isDisabled ? null : (_) => setState(() => _isPressed = false),
      onTapCancel: widget.isDisabled ? null : () => setState(() => _isPressed = false),
      onTap: widget.isDisabled ? null : widget.onPressed,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeInOut,
        transform: Matrix4.diagonal3Values(_isPressed ? 0.97 : 1.0, _isPressed ? 0.97 : 1.0, 1),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
        decoration: BoxDecoration(
          color: widget.isDisabled
              ? disabledColor
              : (widget.isPrimary
              ? (_isPressed ? const Color(0xFF4B5563) : primaryColor)
              : Colors.white),
          borderRadius: BorderRadius.circular(10),
          border: widget.isPrimary || widget.isDisabled
              ? null
              : Border.all(color: const Color(0xFFD1D5DB)),
          boxShadow: widget.isDisabled
              ? []
              : [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              widget.icon,
              size: 16,
              color: widget.isDisabled
                  ? disabledTextColor
                  : (widget.isPrimary ? Colors.white : primaryColor),
            ),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                widget.label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: widget.isDisabled
                      ? disabledTextColor
                      : (widget.isPrimary ? Colors.white : primaryColor),
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AnimatedButton extends StatefulWidget {
  final Widget child;
  final VoidCallback onPressed;

  const _AnimatedButton({
    required this.child,
    required this.onPressed,
  });

  @override
  State<_AnimatedButton> createState() => _AnimatedButtonState();
}

class _AnimatedButtonState extends State<_AnimatedButton>
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
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.96).animate(
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
            child: widget.child,
          );
        },
      ),
    );
  }
}
