# Nourish — Food Microtracker

A Django app for tracking food, daily calories, macronutrients, and selected
micronutrients. Each signed-in user has a personal food log and editable daily
nutrition goals. Manually added foods are private to the account that created
them.

## Requirements

- Python 3.10 or newer
- pip

## Run locally on Windows

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit <http://127.0.0.1:8000/> and register an account.

Create an administrator account if you need the Django admin:

```powershell
python manage.py createsuperuser
```

## Checks and tests

```powershell
python manage.py check
python manage.py test myapp
```

## Django secret key

The app uses a development-only fallback key for local use. Before deployment,
set a new, private `DJANGO_SECRET_KEY` environment variable. Never reuse a key
that has been committed or pushed to GitHub.

For a PowerShell development session, generate and set a fresh key with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
$env:DJANGO_SECRET_KEY = "paste-the-generated-key-here"
```

Use your hosting provider's secret/environment-variable settings for deployment.
Do not commit `.env` files, databases, user data, virtual environments, or Python
cache files.

## Nutrition data

Food nutrient values are stored per 100 grams. A log entry's serving weight is
used to calculate its contribution to daily totals. Users can change their
nutrition goals from the Profile page.

## Production note

The checked-in Django settings are for local development. Before deployment,
disable `DEBUG`, configure `ALLOWED_HOSTS`, use a production database, serve
static files appropriately, and set a new secret key outside source control.
Tailwind CSS is loaded from its CDN for development simplicity.
