from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


INPUT_CLASS = (
    "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm "
    "text-slate-800 outline-none transition placeholder:text-slate-400 "
    "focus:border-leaf-500 focus:ring-4 focus:ring-leaf-50"
)
GOAL_FIELDS = (
    "calorie_goal",
    "protein_goal",
    "carbs_goal",
    "fats_goal",
    "sodium_goal",
    "sugar_goal",
    "iron_goal",
)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=100)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = INPUT_CLASS
            if not field.widget.attrs.get("placeholder"):
                field.widget.attrs["placeholder"] = field.label


class AccountProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class NutritionGoalsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = GOAL_FIELDS
        widgets = {
            field: forms.NumberInput(attrs={"min": 1, "step": 1, "class": INPUT_CLASS})
            for field in GOAL_FIELDS
        }

    def clean(self):
        cleaned_data = super().clean()
        for field_name in GOAL_FIELDS:
            value = cleaned_data.get(field_name)
            if value is not None and value < 1:
                self.add_error(field_name, "Enter a goal of at least 1.")
        return cleaned_data