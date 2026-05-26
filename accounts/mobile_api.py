"""
Mobile API endpoints for the Flutter app.
These are separate from the session-based web views.
"""

import json

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

User = get_user_model()


@csrf_exempt
@require_http_methods(["POST"])
def mobile_login(request):
    """
    Mobile login endpoint - returns user data on success.
    POST /accounts/api/login/
    Body: { "email": "...", "password": "..." }
    """
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            return JsonResponse({"success": False, "error": "Email and password are required."}, status=400)

        user = authenticate(request, username=email, password=password)

        if user is None:
            return JsonResponse({"success": False, "error": "Invalid email or password."}, status=401)

        if not user.is_active:
            return JsonResponse({"success": False, "error": "Account is deactivated."}, status=403)

        return JsonResponse(
            {
                "success": True,
                "token": str(user.pk),  # Simple token; replace with DRF Token if available
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "student_id": getattr(user, "student_id", ""),
                    "phone_number": getattr(user, "phone_number", ""),
                    "faculty": getattr(user, "faculty", ""),
                    "department": getattr(user, "department", ""),
                    "position": getattr(user, "position", ""),
                    "is_admin": user.is_staff or user.is_superuser,
                    "is_staff": user.is_staff,
                    "profile_picture": (
                        request.build_absolute_uri(user.profile_picture.url)
                        if hasattr(user, "profile_picture") and user.profile_picture
                        else None
                    ),
                },
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body."}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mobile_register(request):
    """
    Mobile registration endpoint.
    POST /accounts/api/register/
    Body: { "email": "...", "password": "...", "first_name": "...", "last_name": "..." }
    """
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()

        if not email or not password:
            return JsonResponse({"success": False, "error": "Email and password are required."}, status=400)

        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"success": False, "error": "Invalid email format."}, status=400)

        if len(password) < 8:
            return JsonResponse({"success": False, "error": "Password must be at least 8 characters."}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "error": "An account with this email already exists."}, status=409)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Account created successfully. Please wait for admin approval before booking rooms.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=201,
        )
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body."}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def mobile_logout(request):
    """
    Mobile logout endpoint (token-based: client simply discards the token).
    POST /accounts/api/logout/
    Body: { "user_id": 1 }  (optional – for future server-side token invalidation)
    """
    return JsonResponse({"success": True, "message": "Logged out successfully."})


@csrf_exempt
@require_http_methods(["GET"])
def mobile_profile(request):
    """
    Return profile for the user identified by user_id query param.
    GET /accounts/api/profile/?user_id=1
    """
    try:
        user_id = request.GET.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "error": "user_id is required."}, status=400)

        user = User.objects.get(pk=user_id)
        return JsonResponse(
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "student_id": getattr(user, "student_id", ""),
                    "phone_number": getattr(user, "phone_number", ""),
                    "faculty": getattr(user, "faculty", ""),
                    "department": getattr(user, "department", ""),
                    "position": getattr(user, "position", ""),
                    "is_admin": user.is_staff or user.is_superuser,
                },
            }
        )
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
