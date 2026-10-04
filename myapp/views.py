import math

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from .forms import AccountProfileForm, NutritionGoalsForm, RegistrationForm
from .models import Consume, Food, UserProfile


def _user_logs(request):
    return Consume.objects.filter(user=request.user).select_related("food_consumed")


def _available_foods(user):
    return Food.objects.filter(Q(owner__isnull=True) | Q(owner=user)).order_by("name")


def _profile_for(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _nutrition_totals(logs):
    totals = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fats": 0,
        "sodium": 0,
        "sugar": 0,
        "iron": 0,
    }
    for log in logs:
        scale = log.weight_grams / 100
        for nutrient in totals:
            totals[nutrient] += getattr(log.food_consumed, nutrient) * scale
    return totals


def _progress(value, goal):
    return min(round(value / goal * 100), 100) if goal else 0


def _display_value(value):
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


@login_required
def index(request):
    profile = _profile_for(request.user)
    if request.method == "POST":
        food_id = request.POST.get("food")
        food = _available_foods(request.user).filter(pk=food_id).first() if food_id else None
        if food is None:
            messages.error(request, "Choose a food from your available list before adding it.")
        else:
            Consume.objects.create(user=request.user, food_consumed=food)
            messages.success(request, f"{food.name} added to your food log.")
        return redirect("index")

    today = timezone.localdate()
    today_logs = _user_logs(request).filter(logged_at__date=today)
    totals = _nutrition_totals(today_logs)
    macro_cards = [
        {
            "label": label,
            "value": _display_value(totals[key]),
            "goal": goal,
            "unit": "g",
            "progress": _progress(totals[key], goal),
            "color": color,
        }
        for key, label, color, goal in (
            ("protein", "Protein", "emerald", profile.protein_goal),
            ("carbs", "Carbohydrates", "indigo", profile.carbs_goal),
            ("fats", "Healthy fats", "amber", profile.fats_goal),
        )
    ]
    metrics = [
        {
            "name": label,
            "value": _display_value(totals[key]),
            "goal": goal,
            "unit": unit,
            "progress": _progress(totals[key], goal),
            "is_warning": totals[key] > goal,
        }
        for key, label, unit, goal in (
            ("sodium", "Sodium", "mg", profile.sodium_goal),
            ("sugar", "Added sugar", "g", profile.sugar_goal),
            ("iron", "Iron", "mg", profile.iron_goal),
        )
    ]
    return render(
        request,
        "myapp/dashboard.html",
        {
            "foods": _available_foods(request.user),
            "today_logs": today_logs.order_by("-logged_at"),
            "today": today,
            "total_calories": _display_value(totals["calories"]),
            "calorie_goal": profile.calorie_goal,
            "calorie_progress": _progress(totals["calories"], profile.calorie_goal),
            "macro_cards": macro_cards,
            "micro_metrics": metrics,
            "totals": totals,
        },
    )


@login_required
def log_food(request):
    foods = _available_foods(request.user)
    if request.method == "POST":
        try:
            weight_grams = float(request.POST.get("weight_grams", ""))
            if not math.isfinite(weight_grams) or weight_grams <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Enter a weight greater than zero grams.")
            return render(request, "myapp/log_food.html", {"foods": foods})

        if request.POST.get("manual_entry") == "on":
            name = request.POST.get("food_name", "").strip()
            try:
                nutrition = {
                    "calories": int(request.POST.get("calories", "")),
                    "protein": float(request.POST.get("protein", "")),
                    "carbs": float(request.POST.get("carbs", "")),
                    "fats": float(request.POST.get("fats", "")),
                    "sodium": float(request.POST.get("sodium") or "0"),
                    "sugar": float(request.POST.get("sugar") or "0"),
                    "iron": float(request.POST.get("iron") or "0"),
                }
                if (
                    not name
                    or len(name) > 100
                    or any(not math.isfinite(value) or value < 0 for value in nutrition.values())
                ):
                    raise ValueError
            except ValueError:
                messages.error(request, "Enter a food name and valid, non-negative nutrition values.")
                return render(request, "myapp/log_food.html", {"foods": foods})
            food = Food.objects.create(name=name, owner=request.user, **nutrition)
        else:
            food_id = request.POST.get("food")
            food = foods.filter(pk=food_id).first() if food_id else None
            if food is None:
                messages.error(request, "Choose a food from your available list or switch to manual entry.")
                return render(request, "myapp/log_food.html", {"foods": foods})

        Consume.objects.create(
            user=request.user,
            food_consumed=food,
            weight_grams=weight_grams,
        )
        messages.success(request, f"{food.name} added to your food log.")
        return redirect("index")

    return render(request, "myapp/log_food.html", {"foods": foods})


@login_required
def history(request):
    logs = _user_logs(request).order_by("-logged_at")
    return render(request, "myapp/history.html", {"food_logs": logs})


@login_required
def profile(request):
    profile = _profile_for(request.user)
    account_form = AccountProfileForm(request.POST or None, instance=request.user, prefix="account")
    goals_form = NutritionGoalsForm(request.POST or None, instance=profile, prefix="goals")

    if request.method == "POST":
        account_is_valid = account_form.is_valid()
        goals_are_valid = goals_form.is_valid()
        if account_is_valid and goals_are_valid:
            account_form.save()
            goals_form.save()
            messages.success(request, "Your profile and nutrition goals have been updated.")
            return redirect("profile")
        messages.error(request, "Please correct the highlighted fields and try again.")

    return render(
        request,
        "myapp/profile.html",
        {
            "account_form": account_form,
            "goals_form": goals_form,
            "logged_food_count": _user_logs(request).count(),
        },
    )


@login_required
def delete_consume(request, id):
    consumed_food = get_object_or_404(_user_logs(request), id=id)
    if request.method == "POST":
        name = consumed_food.food_consumed.name
        consumed_food.delete()
        messages.success(request, f"{name} removed from your food log.")
        return redirect("index")
    return render(request, "myapp/delete.html", {"consumed_food": consumed_food})


def register(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        UserProfile.objects.create(user=user)
        auth_login(request, user)
        messages.success(request, f"Welcome, {user.first_name or user.username}! Your profile is ready.")
        return redirect("profile")
    return render(request, "myapp/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = AuthenticationForm(request, data=request.POST or None)
    for field in form.fields.values():
        field.widget.attrs["class"] = (
            "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm "
            "text-slate-800 outline-none transition placeholder:text-slate-400 "
            "focus:border-leaf-500 focus:ring-4 focus:ring-leaf-50"
        )
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        messages.success(request, f"Welcome back, {request.user.first_name or request.user.username}.")
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("index")
    return render(request, "myapp/login.html", {"form": form})


@login_required
def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("login")
    return redirect("profile")
