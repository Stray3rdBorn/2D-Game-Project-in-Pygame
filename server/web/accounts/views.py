import json

from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .tokens import make_token


def read_json(request):
    try:
        data = json.loads(request.body)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def token_response(user, status):
    return JsonResponse({"token": make_token(user), "username": user.username}, status=status)


@csrf_exempt
@require_POST
def register(request):
    data = read_json(request)
    password = data.get("password", "")
    form = UserCreationForm({"username": data.get("username", ""), "password1": password, "password2": password})
    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0]
        return JsonResponse({"detail": first_error}, status=400)
    return token_response(form.save(), 201)


@csrf_exempt
@require_POST
def login(request):
    data = read_json(request)
    user = authenticate(username=data.get("username", ""), password=data.get("password", ""))
    if user is None:
        return JsonResponse({"detail": "Wrong username or password"}, status=401)
    return token_response(user, 200)