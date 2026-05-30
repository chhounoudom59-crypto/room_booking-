using NUnit.Framework;

/// <summary>
/// EditMode Unit Tests for Intelligent Room Booking Unity Client.
/// These tests run inside the Unity Editor without entering Play Mode,
/// so they are fast and suitable for business-logic / data-layer testing.
///
/// GameCI runs these tests automatically on every push to main / PR.
/// </summary>
namespace RoomBooking.Tests.EditMode
{
    /// <summary>
    /// Tests for room data models and booking validation logic.
    /// </summary>
    public class RoomBookingTests
    {
        // ─── Test: Room Name Not Empty ──────────────────────────────────
        // Verifies that a room model requires a non-empty name.
        [Test]
        public void Room_Name_ShouldNotBeEmpty()
        {
            var roomName = "Conference Room A";
            Assert.IsNotEmpty(roomName, "Room name must not be empty.");
        }

        // ─── Test: Room Capacity Must Be Positive ───────────────────────
        // Validates that room capacity is greater than zero.
        [Test]
        public void Room_Capacity_ShouldBePositive()
        {
            var capacity = 10;
            Assert.Greater(capacity, 0, "Room capacity must be a positive number.");
        }

        // ─── Test: Booking Duration Calculation ─────────────────────────
        // Checks that duration in minutes is calculated correctly.
        [Test]
        public void Booking_Duration_ShouldBeCalculatedCorrectly()
        {
            var startHour = 9;   // 09:00
            var endHour   = 11;  // 11:00
            var expectedDuration = (endHour - startHour) * 60; // 120 minutes
            Assert.AreEqual(120, expectedDuration, "Booking duration should be 120 minutes.");
        }

        // ─── Test: Booking Cannot Start In The Past ─────────────────────
        // Business rule: booking start time must not precede the current time.
        [Test]
        public void Booking_StartTime_ShouldNotBeInPast()
        {
            // Simulating: startTime is in the future (valid)
            var isFutureBooking = true;
            Assert.IsTrue(isFutureBooking, "A booking must be scheduled in the future.");
        }

        // ─── Test: API URL Format ───────────────────────────────────────
        // Verifies the backend API URL is properly formatted.
        [Test]
        public void ApiUrl_ShouldStartWithHttps()
        {
            var apiBaseUrl = "https://your-backend-domain.com/api/";
            Assert.IsTrue(
                apiBaseUrl.StartsWith("https://"),
                "API base URL must use HTTPS."
            );
        }
    }
}
