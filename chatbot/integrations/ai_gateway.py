"""
AI Gateway (Production-safe dependency injector)

Only responsibility:
- initialize AI systems once
- provide access to them safely
"""

import logging

logger = logging.getLogger(__name__)

_agentic_rag = None
_booking_automation = None
_vector_store = None


def initialize_ai_systems(rag_system, booking_system, vector_store=None):
    """
    Call this ONCE during Django startup (apps.py or ready()).
    """
    global _agentic_rag, _booking_automation, _vector_store

    _agentic_rag = rag_system
    _booking_automation = booking_system
    _vector_store = vector_store

    logger.info("AI systems initialized successfully")


def get_rag_system():
    return _agentic_rag, _booking_automation


def ensure_ai_ready():
    """
    Initialize AI on first chat request if startup init was skipped or failed.
    (e.g. AI_ENABLED was off when the server started, then enabled in .env)
    """
    global _agentic_rag, _booking_automation

    if _agentic_rag is not None and _booking_automation is not None:
        return _agentic_rag, _booking_automation

    from django.conf import settings

    if not getattr(settings, "AI_ENABLED", False):
        logger.warning("AI_ENABLED is False — chatbot AI will not run.")
        return None, None

    try:
        logger.info("Lazy-initializing chatbot AI (first request)...")
        from chatbot.initializer import create_chat_agent

        create_chat_agent()
        logger.info("Lazy AI initialization complete.")
    except Exception as e:
        logger.exception("Lazy AI initialization failed: %s", e)

    return _agentic_rag, _booking_automation


def get_vector_store():
    return _vector_store


def is_ready():
    return _agentic_rag is not None and _booking_automation is not None
