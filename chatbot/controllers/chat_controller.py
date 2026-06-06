import logging
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from asgiref.sync import sync_to_async

from chatbot.integrations.ai_gateway import get_rag_system
from ai.health_monitor import get_health_monitor
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
    rag_system, _ = get_rag_system()
    
    return JsonResponse({
        "status": "ok",
        "rag_initialized": rag_system is not None,
        "llm_provider": "groq"
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

        # Resolve lazy user object to avoid async context errors
        def resolve_user(u):
            if u and u.is_authenticated:
                # Force evaluation
                _ = u.id
                return u
            return None
        concrete_user = await sync_to_async(resolve_user)(request.user)

        user_message = optional_string(body, "message")
        session_id = optional_string(body, "session_id") or str(uuid.uuid4())

        session_ctx = await sync_to_async(get_session_context)(session_id)

        if not user_message:
            return JsonResponse({
                "reply_text": "How can I help you with booking?",
                "session_id": session_id
            })

        # =========================
        # GET RAG SYSTEM (for query processing and routing)
        # =========================
        rag_system, booking_automation = get_rag_system()

        if not rag_system:
            logger.error(
                "❌ RAG System not initialized!\n"
                "   Possible causes:\n"
                "   1. Groq API key not set in .env (GROQ_API_KEY)\n"
                "   2. Failed to initialize ChatAgent during Django startup\n"
                "   3. Import error in chatbot or AI modules\n"
                "   Check server logs for full error details."
            )
            return JsonResponse({
                "error": "rag_not_initialized",
                "reply_text": "⚠️ AI system not ready. Check that Groq API key is set in .env file. Restart the server."
            }, status=503)

        # =========================
        # EARLY INTENT CLASSIFICATION (LLM only, decides routing)
        # For database queries, route directly to tools instead of running full RAG
        # =========================
        early_intent = await sync_to_async(rag_system.query_processor.process_query)(
            user_message, 
            session_ctx
        )
        
        primary_intent = early_intent.get("intent", {}).get("primary")
        entities = early_intent.get("entities", {})
        intent_confidence = early_intent.get("intent", {}).get("confidence", 0.5)
        
        logger.info(f"Intent classification: {primary_intent} (confidence: {intent_confidence})")

        # Accumulate and persist entities in the session context
        if entities:
            cleaned_entities = {k: v for k, v in entities.items() if v is not None}
            if cleaned_entities:
                session_ctx.update(cleaned_entities)
                await sync_to_async(save_session_context)(session_id, session_ctx)

        # Build accumulated_entities dictionary from session_ctx
        accumulated_entities = {
            "room_number": session_ctx.get("room_number"),
            "room_type": session_ctx.get("room_type"),
            "capacity": session_ctx.get("capacity"),
            "attendees": session_ctx.get("attendees"),
            "date": session_ctx.get("date"),
            "start_time": session_ctx.get("start_time"),
            "end_time": session_ctx.get("end_time"),
            "purpose": session_ctx.get("purpose"),
            "equipment": session_ctx.get("equipment", []),
        }
        accumulated_entities = {k: v for k, v in accumulated_entities.items() if v is not None}

        # =========================
        # DATABASE QUERY SHORTCUT OR FULL RAG PROCESSING
        # =========================
        DATABASE_INTENTS = ["availability", "user_profile", "user_history", "booking", "modification", "cancellation"]
        is_database_shortcut = primary_intent in DATABASE_INTENTS and intent_confidence > 0.7

        # =========================
        # SMART BOOKING CONTINUATION DETECTION
        # When mid-booking, only continue the booking flow if the user's
        # current message actually provides booking-relevant information.
        # Side questions like "how many classrooms" should be answered
        # naturally — the booking state is preserved for the next message.
        # =========================
        booking_in_progress = session_ctx.get("booking_in_progress", False)
        if booking_in_progress:
            # Check if new entities contain booking-relevant fields
            booking_entity_keys = {'date', 'start_time', 'end_time', 'room_type', 'capacity', 'room_number', 'attendees'}
            new_booking_entities = {k: v for k, v in entities.items()
                                    if k in booking_entity_keys and v is not None}

            # Check for time/date keywords in message (e.g. "tomorrow", "9am", "monday")
            time_keywords = ['today', 'tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday',
                             'friday', 'saturday', 'sunday', 'am', 'pm', 'morning', 'afternoon',
                             'evening', 'noon', 'o\'clock', 'next week', 'this week']
            booking_action_words = ['book', 'reserve', 'yes', 'confirm', 'proceed', 'go ahead',
                                    'ok', 'okay', 'sure', 'alright', 'sounds good']
            msg_lower = user_message.lower()
            has_time_keyword = any(kw in msg_lower for kw in time_keywords)
            has_booking_keyword = any(kw in msg_lower for kw in booking_action_words)

            should_continue_booking = (
                bool(new_booking_entities) or
                has_time_keyword or
                has_booking_keyword or
                primary_intent == "booking"
            )

            if should_continue_booking and primary_intent not in ("cancellation", "modification", "user_profile", "user_history"):
                logger.info(f"Booking continuation: forcing 'booking' (was: {primary_intent}, new_entities: {list(new_booking_entities.keys())})")
                primary_intent = "booking"
                is_database_shortcut = True
            else:
                # User asked a side question — answer it normally, keep booking state
                logger.info(f"Booking paused for side question (intent: {primary_intent}). booking_in_progress preserved.")

        response_text = ""
        rooms_payload = None
        actions = []
        criteria = None
        preview = None
        success = False
        rag_result = {}
        reflection_scores = {}
        response_html = None

        if is_database_shortcut:
            logger.info(f"✓ Routing to tool calling (bypassing RAG): {primary_intent}")
            from chatbot.services.orchestrator import (
                handle_availability_query,
                handle_user_profile,
                handle_user_history,
                handle_modify_booking,
                handle_prepare_booking,
            )

            try:
                if primary_intent == "availability":
                    availability_result = await handle_availability_query(accumulated_entities, user_message)
                    response_text = availability_result.get("response_text", "Searching for rooms...")
                    success = availability_result.get("success", False)
                    if availability_result.get("rooms"):
                        rooms_payload = [
                            {
                                "id": r['room'].id,
                                "name": r['room'].name,
                                "room_number": r['room'].room_number,
                                "capacity": r['room'].capacity,
                                "room_type": getattr(r['room'], 'room_type', 'other'),
                                "equipment": [item.strip() for item in r['room'].equipment.replace(',', ' ').split() if item.strip()] if r['room'].equipment else [],
                                "description": r['room'].description,
                                "available_until": r.get('available_until', 'End of day')
                            }
                            for r in availability_result.get("rooms", [])
                        ]
                        # Always offer booking action when rooms are shown
                        actions = [{"type": "book_room", "label": "Book a Room"}]

                elif primary_intent == "user_profile":
                    profile_result = await handle_user_profile(concrete_user)
                    response_text = profile_result.get("response_text", profile_result.get("message", "Could not get profile"))
                    success = profile_result.get("success", False)

                elif primary_intent == "user_history":
                    history_result = await handle_user_history(concrete_user)
                    response_text = history_result.get("response_text", history_result.get("message", "Could not get history"))
                    success = history_result.get("success", False)

                elif primary_intent == "booking":
                    booking_result = await handle_prepare_booking(accumulated_entities, user_message)
                    success = booking_result.get("success", False)
                    response_text = booking_result.get("message", "Booking preparation failed")
                    preview = booking_result.get("preview")
                    actions = booking_result.get("actions", [])
                    criteria = booking_result.get("criteria")

                    if success and preview:
                        # Room found — clear booking flow flag
                        session_ctx.pop("booking_in_progress", None)
                        await sync_to_async(save_session_context)(session_id, session_ctx)
                        await sync_to_async(set_booking_preview)(session_id, {
                            "criteria": criteria,
                            "room_id": preview['room']['id'],
                            "room_name": preview['room']['name'],
                            "room_number": preview['room']['room_number'],
                            "room_capacity": preview['room']['capacity'],
                            "equipment": preview['room'].get('equipment', []),
                        })
                    else:
                        # Still waiting for more info — keep booking in progress
                        session_ctx["booking_in_progress"] = True
                        await sync_to_async(save_session_context)(session_id, session_ctx)
                        actions = []
                        preview = None

                elif primary_intent == "modification":
                    mod_result = await handle_modify_booking(concrete_user, accumulated_entities, session_ctx)
                    response_text = mod_result.get("response_text", mod_result.get("message", "Modification failed"))
                    success = mod_result.get("success", False)
                    actions = mod_result.get("actions", [])
                    await sync_to_async(save_session_context)(session_id, session_ctx)

                elif primary_intent == "cancellation":
                    from chatbot.services.orchestrator import handle_cancel_booking
                    cancel_result = await handle_cancel_booking(concrete_user, session_ctx)
                    response_text = cancel_result.get("message", "Cancellation failed")
                    success = cancel_result.get("success", False)
                    actions = cancel_result.get("actions", [])
                    await sync_to_async(save_session_context)(session_id, session_ctx)

            except Exception as e:
                logger.exception(f"Tool calling failed for intent {primary_intent}: {e}")
                is_database_shortcut = False # Fall through to RAG on failure

        if not is_database_shortcut:
            # =========================
            # FULL RAG PROCESSING (For document/information queries or fallback)
            # =========================
            rag_result = await sync_to_async(rag_system.process_query)(
                query=user_message,
                context=session_ctx,
                top_k=5,
            )

            response_text = rag_result["response_text"]
            entities = rag_result["entities"]
            intent = rag_result["intent"]
            primary_intent = intent.get("primary") if isinstance(intent, dict) else intent
            reflection_scores = {}

            if entities:
                session_ctx.update({k: v for k, v in entities.items() if v is not None})
                await sync_to_async(save_session_context)(session_id, session_ctx)
                accumulated_entities.update({k: v for k, v in entities.items() if v is not None})

            # =========================
            # INTENT HANDLERS FOR FALLBACK
            # =========================
            if primary_intent == "user_profile":
                from chatbot.services.orchestrator import handle_user_profile
                profile_result = await handle_user_profile(concrete_user)
                response_text = profile_result.get("response_text", profile_result.get("message", "Could not retrieve profile."))
                success = profile_result.get("success", False)

            elif primary_intent == "user_history":
                from chatbot.services.orchestrator import handle_user_history
                history_result = await handle_user_history(concrete_user)
                response_text = history_result.get("response_text", history_result.get("message", "Could not retrieve booking history."))
                success = history_result.get("success", False)

            elif primary_intent == "booking":
                # NOTE: No validate_booking_entities gate here.
                # handle_prepare_booking handles missing fields via LLM clarification.
                from chatbot.services.orchestrator import handle_prepare_booking
                booking_result = await handle_prepare_booking(accumulated_entities, user_message)
                success = booking_result.get('success', False)
                response_text = booking_result.get('message', 'Booking preparation failed')
                preview = booking_result.get('preview')
                actions = booking_result.get('actions', [])
                criteria = booking_result.get('criteria')

                if success and preview:
                    # Booking found — clear the in-progress flag
                    session_ctx.pop("booking_in_progress", None)
                    await sync_to_async(set_booking_preview)(session_id, {
                        "criteria": criteria,
                        "room_id": preview['room']['id'],
                        "room_name": preview['room']['name'],
                        "room_number": preview['room']['room_number'],
                        "room_capacity": preview['room']['capacity'],
                        "equipment": preview['room'].get('equipment', []),
                    })
                    await sync_to_async(save_session_context)(session_id, session_ctx)
                else:
                    # Still missing info — mark booking as in-progress so next
                    # message is also routed to the booking handler
                    session_ctx["booking_in_progress"] = True
                    await sync_to_async(save_session_context)(session_id, session_ctx)
                    actions = []
                    preview = None

            elif primary_intent == "availability":
                from chatbot.services.orchestrator import handle_availability_query
                availability_result = await handle_availability_query(accumulated_entities, user_message)
                success = availability_result.get("success", False)
                response_text = availability_result.get("response_text", "Searching for rooms...")
                if availability_result.get("rooms"):
                    rooms = availability_result.get("rooms")
                    rooms_payload = [
                        {
                            "id": r['room'].id,
                            "name": r['room'].name,
                            "room_number": r['room'].room_number,
                            "capacity": r['room'].capacity,
                            "room_type": getattr(r['room'], 'room_type', 'other'),
                            "equipment": [item.strip() for item in r['room'].equipment.replace(',', ' ').split() if item.strip()] if r['room'].equipment else [],
                            "description": r['room'].description,
                            "available_until": r.get('available_until', 'End of day')
                        }
                        for r in rooms
                    ]
                    actions = [{"type": "book_room", "label": "Book a Room"}]

            elif primary_intent == "modification":
                from chatbot.services.orchestrator import handle_modify_booking
                mod_result = await handle_modify_booking(concrete_user, accumulated_entities, session_ctx)
                success = mod_result.get("success", False)
                response_text = mod_result.get("message", "Could not process modification request.")
                actions = mod_result.get("actions", [])
                await sync_to_async(save_session_context)(session_id, session_ctx)

            # elif primary_intent == "cancellation":
            #     from chatbot.services.orchestrator import handle_cancel_booking
            #     cancel_result = await handle_cancel_booking(concrete_user, session_ctx)
            #     success = cancel_result.get("success", False)
            #     response_text = cancel_result.get("message", "Could not process cancellation request.")
            #     actions = cancel_result.get("actions", [])
            #     await sync_to_async(save_session_context)(session_id, session_ctx)

        # =========================
        # ROOM DETAIL CARD INJECTION
        # If a specific room number is mentioned, fetch room details to display a card
        # =========================
        mentioned_room_number = accumulated_entities.get("room_number")
        if mentioned_room_number and not rooms_payload:
            from booking.models import Room
            room_obj = await sync_to_async(
                lambda: Room.objects.filter(room_number__iexact=mentioned_room_number, is_available=True).first()
            )()
            if room_obj:
                equipment_list = await sync_to_async(
                    lambda: [item.strip() for item in room_obj.equipment.replace(',', ' ').split() if item.strip()] if room_obj.equipment else []
                )()
                rooms_payload = [{
                    "id": room_obj.id,
                    "name": room_obj.name,
                    "room_number": room_obj.room_number,
                    "capacity": room_obj.capacity,
                    "room_type": room_obj.get_room_type_display() if hasattr(room_obj, "get_room_type_display") else room_obj.room_type,
                    "equipment": equipment_list,
                    "description": room_obj.description
                }]

        # =========================
        # RESPONSE BUILDING
        # =========================
        structured = build_chat_response(
            response_text=response_text,
            response_html=response_html,
            actions=actions,
            entities=accumulated_entities,
            primary_intent=primary_intent,
            reflection_scores=reflection_scores,
            session_id=session_id,
            rag_result=rag_result,
            retrieved_docs=rag_result.get("retrieved_docs", []),
        )

        # attach frontend-friendly data
        structured["rooms"] = rooms_payload
        structured["booking_criteria"] = criteria
        structured["data"] = preview

        return JsonResponse(structured)

    except Exception as e:
        logger.exception(e)
        return JsonResponse({
            "error": "internal_error",
            "reply_text": "Something went wrong."
        }, status=500)


# =========================
# CONFIRM BOOKING
# =========================
@csrf_exempt
@require_http_methods(["POST"])
async def confirm_booking(request):
    from chatbot.services.orchestrator import handle_confirm_booking
    
    ok, body, err, status = parse_json_body(request)
    if not ok:
        return JsonResponse({"error": err}, status=status)

    ok, session_id, err, status = require_string_field(body, "session_id")
    if not ok:
        return JsonResponse({"error": err}, status=status)

    # Resolve lazy user object to avoid async context errors
    def resolve_user(u):
        if u and u.is_authenticated:
            # Force evaluation
            _ = u.id
            return u
        return None
    concrete_user = await sync_to_async(resolve_user)(request.user)

    preview = await sync_to_async(get_booking_preview)(session_id)

    if not preview:
        return JsonResponse({"reply_text": "No booking found."}, status=400)

    criteria = preview["criteria"]

    # Use orchestrator to handle booking (prefers plugin/automation where available)
    result = await handle_confirm_booking(concrete_user, criteria)

    await sync_to_async(clear_booking_preview)(session_id)

    if result.get("success"):
        await sync_to_async(clear_session_context)(session_id)

    # Sanitize result for JSON serialization — strip ORM objects
    safe_result = {
        "success": result.get("success", False),
        "booking_id": result.get("booking_id"),
        "room_name": result.get("room_name"),
        "room_number": result.get("room_number"),
        "date": result.get("date"),
        "time": result.get("time"),
        "error": result.get("error"),
        "user_message": result.get("user_message"),
    }

    return JsonResponse({
        "reply_text": result.get("user_message", "Booking confirmed"),
        "result": safe_result,
        "session_id": session_id
    })


# =========================
# UPDATE BOOKING PREVIEW (NEW)
# =========================
@csrf_exempt
@require_http_methods(["POST"])
async def update_booking_preview(request):
    from chatbot.services.orchestrator import handle_prepare_booking
    
    ok, body, err, status = parse_json_body(request)
    if not ok:
        return JsonResponse({"error": err, "reply_text": "Invalid request format."}, status=status)

    ok, session_id, err, status = require_string_field(body, "session_id")
    if not ok:
        return JsonResponse({"error": err, "reply_text": "Session ID is required."}, status=status)

    # Get existing session context
    session_ctx = await sync_to_async(get_session_context)(session_id)
    
    # Read the updated fields from payload
    new_date = optional_string(body, "date")
    new_start_time = optional_string(body, "start_time")
    new_end_time = optional_string(body, "end_time")
    new_capacity = body.get("capacity")
    new_purpose = optional_string(body, "purpose")
    new_notes = optional_string(body, "additional_notes")
    
    # Update session context with explicit new values
    if new_date: session_ctx["date"] = new_date
    if new_start_time: session_ctx["start_time"] = new_start_time
    if new_end_time: session_ctx["end_time"] = new_end_time
    if new_capacity is not None:
        try:
            session_ctx["capacity"] = int(new_capacity)
            session_ctx["attendees"] = int(new_capacity)
        except (ValueError, TypeError):
            pass
    if new_purpose: session_ctx["purpose"] = new_purpose
    if new_notes is not None: session_ctx["additional_notes"] = new_notes
    
    await sync_to_async(save_session_context)(session_id, session_ctx)
    
    # Re-prepare booking with the updated criteria
    booking_result = await handle_prepare_booking(session_ctx, "Update booking request")
    success = booking_result.get("success", False)
    message = booking_result.get("message", "Booking preparation failed")
    preview = booking_result.get("preview")
    actions = booking_result.get("actions", [])
    criteria = booking_result.get("criteria")
    
    if success and preview:
        await sync_to_async(set_booking_preview)(session_id, {
            "criteria": criteria,
            "room_id": preview['room']['id'],
            "room_name": preview['room']['name'],
            "room_number": preview['room']['room_number'],
            "room_capacity": preview['room']['capacity'],
            "equipment": preview['room'].get('equipment', []),
        })
    
    return JsonResponse({
        "success": success,
        "reply_text": message,
        "data": preview,
        "actions": actions,
        "booking_criteria": criteria,
        "session_id": session_id
    })