# 🎬 MovieBooking Backend

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/DRF-REST%20API-EF4444?logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-316192?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/JWT-Auth-000000?logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Render-Deploy-46E3B7?logo=render&logoColor=111" />
</p>

> **A production-ready backend for a Movie Ticket Booking system** built with **Django + Django REST Framework**. Supports role-based access (admin/owner/user), shows with auto-generated seats (10×10), secure JWT auth, and clean, scalable APIs for movies, theaters, shows, seats, and bookings.

---

## ✨ Features

* 🔐 **JWT Authentication** (access + refresh) with optional **OTP-based password reset**
* 👑 **Roles**: `admin`, `owner` (can manage theaters & shows), `user`
* 🎭 **Movie & Theater Management**
* 🗓️ **Shows** with **auto seat grid generation** (e.g., 10×10 = 100 seats) on creation
* 🎟️ **Seat selection & booking** flow (atomic, avoids double booking)
* 🚦 **Status-aware seats**: available / selected / booked
* 📦 Clean project structure, environment-based settings, and ready for **Render** deploy

---

## 🛠️ Tech Stack

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Django%20REST%20Framework-API-EF4444?logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-DB-316192?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/SimpleJWT-Tokens-000000?logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Whitenoise-Static-555555" />
  <img src="https://img.shields.io/badge/Gunicorn-WSGI-2CA5E0?logo=gunicorn&logoColor=white" />
  <img src="https://img.shields.io/badge/Render-Hosting-46E3B7?logo=render&logoColor=111" />
</p>

---

## 🧱 Architecture

```
Client (React / React Native)
        │   JSON over HTTPS (JWT)
        ▼
   Django REST Framework
        ├─ apps: users, theaters, movies, shows, bookings
        ├─ auth: JWT + (optional) OTP reset
        ▼
      PostgreSQL
```

```bash
# install packages
pip install -r requirements.txt
```


### 4) Run Migrations & Server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## ☁️ Deploy to Render

### A) Prepare the codebase

1. **Add production deps** in `requirements.txt` (already shown above). Ensure `dj-database-url` is added if you use it:

   ```
   dj-database-url
   ```
2. **Procfile** (Gunicorn entrypoint). Replace `core` with your Django project name:

   ```
   web: gunicorn core.wsgi:application --preload
   ```
3. **Static files**: ensure `whitenoise` middleware present and `collectstatic` runs.
4. **Settings**: set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for Render domain.

   ```python
   CSRF_TRUSTED_ORIGINS = [
       "https://*.onrender.com",
       "https://your-custom-domain.com",
   ]
   ```

### B) Create services on Render

1. **Push code to GitHub**.

2. In **Render Dashboard** → **New +** → **Web Service** → **Build from GitHub** → select your repo.

3. **Environment**: `Python 3`

4. **Region**: closest to your users.

5. **Build Command**:

   ```bash
   pip install -r requirements.txt 
   ```

6. **Start Command** (matches `Procfile`):

   ```bash
   gunicorn core.wsgi:application --preload
   ```
---

### 💡 Notes & Tips

* Shows can auto-generate **10×10 seats** on creation. If you want dynamic rows/cols, store `rows` & `cols` on the `Show` model and generate accordingly.
* Wrap seat booking in DB transactions to avoid double booking.
* Consider rate limiting login/OTP endpoints in production.

---

> Made with ❤️ for interview-ready, scalable backends.
