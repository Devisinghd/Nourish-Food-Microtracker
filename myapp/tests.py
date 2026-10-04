from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Consume, Food, UserProfile


class FoodTrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alex",
            password="safe-password-123",
            first_name="Alex",
        )
        self.client.force_login(self.user)
        self.food = Food.objects.create(
            name="Oats",
            calories=389,
            protein=16.9,
            carbs=66.3,
            fats=6.9,
            sodium=2,
            sugar=0,
            iron=4.7,
        )

    def test_personal_pages_require_login(self):
        self.client.logout()
        for url_name in ("index", "log_food", "history", "profile"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={reverse(url_name)}",
                )

    def test_dashboard_shows_weight_adjusted_daily_nutrients(self):
        Consume.objects.create(user=self.user, food_consumed=self.food, weight_grams=50)
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_calories"], 195)
        self.assertEqual(response.context["totals"]["protein"], 8.45)
        self.assertContains(response, "Oats")

    def test_manual_food_entry_belongs_only_to_current_user(self):
        response = self.client.post(
            reverse("log_food"),
            {
                "manual_entry": "on",
                "food_name": "Lentils",
                "weight_grams": "150",
                "calories": "116",
                "protein": "9",
                "carbs": "20",
                "fats": "0.4",
                "sodium": "2",
                "sugar": "1.8",
                "iron": "3.3",
            },
        )
        self.assertRedirects(response, reverse("index"))
        food = Food.objects.get(name="Lentils")
        entry = Consume.objects.get(food_consumed=food)
        self.assertEqual(entry.weight_grams, 150)
        self.assertEqual(food.iron, 3.3)
        self.assertEqual(food.owner, self.user)

    def test_user_cannot_log_another_users_custom_food(self):
        other_user = User.objects.create_user(username="sam", password="safe-password-456")
        private_food = Food.objects.create(
            name="Sam's food",
            calories=100,
            protein=1,
            carbs=1,
            fats=1,
            owner=other_user,
        )
        response = self.client.post(
            reverse("log_food"),
            {"food": private_food.pk, "weight_grams": "100"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Consume.objects.filter(food_consumed=private_food).exists())

    def test_profile_updates_account_and_personal_nutrition_goals(self):
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)
        response = self.client.post(
            reverse("profile"),
            {
                "account-first_name": "Alexandra",
                "account-last_name": "Morgan",
                "account-email": "alex@example.com",
                "goals-calorie_goal": "1800",
                "goals-protein_goal": "110",
                "goals-carbs_goal": "210",
                "goals-fats_goal": "65",
                "goals-sodium_goal": "2000",
                "goals-sugar_goal": "40",
                "goals-iron_goal": "20",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(self.user.first_name, "Alexandra")
        self.assertEqual(profile.calorie_goal, 1800)
        dashboard = self.client.get(reverse("index"))
        self.assertEqual(dashboard.context["calorie_goal"], 1800)
        self.assertEqual(dashboard.context["macro_cards"][0]["goal"], 110)

    def test_registration_creates_account_profile_and_authenticates_user(self):
        self.client.logout()
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-user",
                "first_name": "New",
                "last_name": "Member",
                "email": "new@example.com",
                "password1": "StrongPassword987!",
                "password2": "StrongPassword987!",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        user = User.objects.get(username="new-user")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_login_and_post_logout_work(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        login_response = self.client.post(
            reverse("login"),
            {"username": "alex", "password": "safe-password-123"},
        )
        self.assertRedirects(login_response, reverse("index"))
        logout_response = self.client.post(reverse("logout"))
        self.assertRedirects(logout_response, reverse("login"))

    def test_invalid_weight_does_not_create_log(self):
        response = self.client.post(
            reverse("log_food"),
            {"food": self.food.pk, "weight_grams": "-3"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Consume.objects.count(), 0)
        self.assertContains(response, "Enter a weight greater than zero grams.")
