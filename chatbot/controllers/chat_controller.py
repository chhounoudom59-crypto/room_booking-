import logging
import uuid

from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from chatbot.integrations.ai_gateway import ensure_ai_ready, get_rag_system
from chatbot.services.booking_service import (
    auto_book,
    build_booking_criteria,
    find_best_rooms,
)
from chatbot.services.response_service import build_chat_response
from chatbot.services.session_service import (
    clear_booking_preview,
    clear_session_context,
    get_booking_preview,
    get_session_context,
    save_session_context,
    set_booking_preview,
)
from chatbot.utils.validators import (
    optional_string,
    parse_json_body,
    require_string_field,
    validate_booking_entities,
)

logger = logging.getLogger(__name__)


# =========================
# BASIC ENDPOINTS
# =========================

@require_http_methods(["GET"])
def chatbot_index(request):
    return JsonResponse({
        "service": "chatbot",
        "status": "ok",
        "message": "Use /chatbot/chat/ for chat requests.",
    })


@require_http_methods(["GET"])
def health_check(request):
    rag_system, _ = ensure_ai_ready()
    return JsonResponse({
        "status": "ok",
        "rag_initialized": rag_system is not None
    })


# =========================
# CLEAR SESSION
# =========================

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def clear_session(request):
    if request.method == "OPTIONS":
        return JsonResponse({"status": "ok"})

    try:
        ok, body, err, status = parse_json_body(request)
        if not ok:
            return JsonResponse({"error": err}, status=status)

        ok, session_id, err, status = require_string_field(body, "session_id")
        if not ok:
            return JsonResponse({"error": err}, status=status)

        clear_session_context(session_id)
        clear_booking_preview(session_id)

        return JsonResponse({"status": "cleared", "session_id": session_id})

    except Exception as e:
        logger.exception(e)
        return JsonResponse({"error": "failed_to_clear_session"}, status=500)


# =========================
# CHAT ENDPOINT
# =========================

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
async def chat_endpoint(request):

    if request.method == "OPTIONS":
        return JsonResponse({"status": "ok"})

    try:
        ok, body, err, status = parse_json_body(request)
        if not ok:
            return JsonResponse({"error": err, "reply_text": "Invalid request format."}, status=status)

        user_message = optional_string(body, "message")
        session_id = optional_string(body, "session_id") or str(uuid.uuid4())

        session_ctx = get_session_context(session_id)

        if not user_message:
            return JsonResponse({
                "reply_text": "How can I help you with booking?",
                "session_id": session_id
            })

        rag_system, booking_automation = ensure_ai_ready()

        if not rag_system:
            fallback = (
                "The AI assistant could not start. Check:\n"
                "1) .env has AI_ENABLED=True\n"
                "2) Restart Django: python manage.py runserver 8001\n"
                "3) Optional: run Ollama (ollama serve) for smarter replies\n"
                "You can still book rooms from the Book page."
            )
            return JsonResponse({
                "reply_text": fallback,
                "session_id": session_id,
                "rag_mode": "offline",
            })

        # =========================
        # RAG PROCESSING
        # =========================

        rag_result = await sync_to_async(rag_system.process_query)(
            query=user_message,
            context=session_ctx,
            top_k=5,
            use_self_rag=True,
        )

        response_text = rag_result["response_text"]
        entities = rag_result["entities"]
        intent = rag_result["intent"]
        reflection_scores = rag_result.get("reflection_scores", {})

        if entities:
            session_ctx.update(entities)
            save_session_context(session_id, session_ctx)

        primary_intent = intent.get("primary") if isinstance(intent, dict) else intent

        response_html = None
        actions = []
        rooms_payload = None
        criteria = None

        # =========================
        # BOOKING FLOW (JSON ONLY)
        # =========================

        if primary_intent == "booking" and validate_booking_entities(entities):
            criteria = build_booking_criteria(entities, user_message)

            rooms = await find_best_rooms(
                booking_automation,
                criteria,
                limit=3
            )

            if rooms:
                best_room = rooms[0]["room"]

                set_booking_preview(session_id, {
                    "criteria": criteria,
                    "best_room_id": best_room.id,
                })

                rooms_payload = [
                    {
                        "id": r["room"].id,
                        "name": r["room"].name,
                        "room_number": r["room"].room_number,
                        "capacity": r["room"].capacity,
                        "score": r["score"],
                    }
                    for r in rooms
                ]

                response_text = "I found available rooms for your booking."

                actions = [{
                    "type": "confirm_booking",
                    "label": "Confirm Booking"
                }]

            else:
                response_text = (
                    "No available rooms found. Try another time slot."
                )

        # =========================
        # RESPONSE
        # =========================

        structured = build_chat_response(
            response_text=response_text,
            response_html=response_html,
            actions=actions,
            entities=entities,
            primary_intent=primary_intent,
            reflection_scores=reflection_scores,
            session_id=session_id,
            rag_result=rag_result,
            retrieved_docs=rag_result.get("retrieved_docs", []),
        )

        # attach frontend-friendly data
        structured["rooms"] = rooms_payload
        structured["booking_criteria"] = criteria

        return JsonResponse(structured)

    except Exception as e:
        logger.exception(e)
        err_msg = str(e)
        if "Hugging Face" in err_msg or "API" in err_msg:
            hint = err_msg
        else:
            hint = "Something went wrong. Please try again or restart the server."
        return JsonResponse({
            "error": "internal_error",
            "reply_text": hint,
        }, status=500)


# =========================
# CONFIRM BOOKING
# =========================

@csrf_exempt
@require_http_methods(["POST"])
async def confirm_booking(request):
    ok, body, err, status = parse_json_body(request)
    if not ok:
        return JsonResponse({"error": err}, status=status)

    ok, session_id, err, status = require_string_field(body, "session_id")
    if not ok:
        return JsonResponse({"error": err}, status=status)

    preview = get_booking_preview(session_id)

    if not preview:
        return JsonResponse({"reply_text": "No booking found."}, status=400)

    criteria = preview["criteria"]

    _, booking_automation = ensure_ai_ready()

    user = request.user if request.user.is_authenticated else None
    if user is None:
        email = optional_string(body, "email") or optional_string(body, "user_email")
        if email:
            from accounts.models import User
            user = User.objects.filter(email=email).first()
    if user is None:
        return JsonResponse({
            "reply_text": "Please log in on the website before confirming a booking.",
        }, status=401)

    result = await auto_book(
        booking_automation,
        user,
        criteria
    )

    clear_booking_preview(session_id)

    return JsonResponse({
        "reply_text": result.get("user_message", "Booking confirmed"),
        "result": result,
        "session_id": session_id
    })
