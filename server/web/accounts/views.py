from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.db.models import Max

from .models import ApiKey, Score


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            ApiKey.objects.create(user=user)
            login(request, user)
            return redirect("profile")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile(request):
    api_key, _ = ApiKey.objects.get_or_create(user=request.user)
    scores = Score.objects.filter(user_id=request.user.id)[:10]
    return render(request, "profile.html", {"api_key": api_key.key, "scores": scores})


def leaderboard(request):
    scores = Score.objects.values("player_name").annotate(best=Max("score")).order_by("-best")[:10]
    return render(request, "leaderboard.html", {"scores": scores})