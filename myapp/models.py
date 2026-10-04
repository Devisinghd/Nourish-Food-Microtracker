from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.
class Food(models.Model):

    def __str__(self):
        return self.name
    name = models.CharField(max_length=100)
    carbs = models.FloatField()
    protein = models.FloatField()
    fats = models.FloatField()
    calories = models.IntegerField()
    sodium = models.FloatField(default=0)
    sugar = models.FloatField(default=0)
    iron = models.FloatField(default=0)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_foods",
    )

class Consume(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    food_consumed = models.ForeignKey(Food,on_delete=models.CASCADE)
    weight_grams = models.FloatField(default=100)
    logged_at = models.DateTimeField(default=timezone.now, editable=False)
    session_key = models.CharField(max_length=40, blank=True, default="")


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="nutrition_profile")
    calorie_goal = models.PositiveIntegerField(default=2000)
    protein_goal = models.PositiveIntegerField(default=120)
    carbs_goal = models.PositiveIntegerField(default=250)
    fats_goal = models.PositiveIntegerField(default=70)
    sodium_goal = models.PositiveIntegerField(default=2300)
    sugar_goal = models.PositiveIntegerField(default=50)
    iron_goal = models.PositiveIntegerField(default=18)

    def __str__(self):
        return f"{self.user.username}'s nutrition profile"