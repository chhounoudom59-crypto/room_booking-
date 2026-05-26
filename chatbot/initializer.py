# chatbot/initializer.py

import logging

logger = logging.getLogger(__name__)


def create_chat_agent():
    """
    Build and return ChatAgent instance.
    This keeps apps.py clean and avoids Django startup issues.
    """

    logger.info("Creating ChatAgent...")

    # --- Heavy imports moved here (important) ---
    from django.conf import settings

    from ai.booking_automation import BookingAutomation
    from ai.kernel_config import create_kernel
    from ai.plugins.room_booking_plugin import RoomBookingPlugin
    from booking.models import Booking, BookingRule, Room

    # --- Init AI components ---
    booking_automation = BookingAutomation(Room, Booking, BookingRule)

    provider = getattr(settings, "LLM_PROVIDER", "ollama")
    kernel = create_kernel(provider=provider)
    logger.info("Chat kernel provider: %s", provider)

    room_plugin = RoomBookingPlugin(Room, Booking, booking_automation)
    kernel.add_plugin(room_plugin, plugin_name="RoomBooking")

    # --- Import your ChatAgent class safely ---
    from chatbot.agent import ChatAgent  # (we will extract it next step)

    agent = ChatAgent(kernel, booking_automation, room_plugin)

    logger.info("ChatAgent created successfully")

    return agent
