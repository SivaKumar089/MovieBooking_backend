# 🎬 Bookit Cinema — Backend REST API Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Django_REST_Framework-API-EF4444?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/JWT-SimpleJWT_Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Database-MySQL_%2F_SQLite-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/Tests-8%20Passed-10B981?style=for-the-badge&logo=pytest&logoColor=white" />
</p>

> **A high-concurrency, transaction-safe backend for Movie Ticket Booking and Theater Auditorium Management**, engineered with **Django 5** and **Django REST Framework (DRF)**. Features atomic seat reservation, dynamic multi-tier seating grids, role-based access control (Admin, Theater Owner, Customer), and Gatebox QR ticket verification.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Role-Based Access Control (RBAC)](#-role-based-access-control-rbac)
- [Atomic Seat Booking Engine](#-atomic-seat-booking-engine)
- [API Reference](#-api-reference)
- [Local Development Setup](#-local-development-setup)
- [Automated Testing](#-automated-testing)
- [Database Configuration](#-database-configuration)
- [Production Deployment](#-production-deployment)

---

## 🚀 Key Features

* 🔐 **Secure JWT Authentication:** Access & Refresh tokens powered by SimpleJWT with user identity claims and email-based OTP password recovery.
* 🛡️ **Role-Based Access Control:** Strict permission segregation across `admin`, `owner`, and `user` roles without hindering legitimate owner bookings.
* 🎟️ **Atomic Double-Booking Prevention:** Utilizes `transaction.atomic()` and `select_for_update()` to eliminate race conditions during high-demand seat bookings.
* 💺 **Dynamic Seating Grid:** Automatic generation of 100 seats (Rows A–J × 10 Columns) with three tiers (`VIP`, `PREMIUM`, `STANDARD`) and tier-based pricing.
* 🔄 **Real-Time Seat State Tracking:** Seats provide dynamic contextual attributes: `is_booked`, `is_mine`, `booked_by`, and `booking_code`.
* 📊 **Live Show Metrics:** Instant recalculation of `total_seats`, `booked_seats`, and `available_seats` with strict `-1` decrement upon confirmed booking and restoration upon cancellation.
* 📱 **Gatebox QR Verification API:** Cryptographically verifiable ticket pass validation endpoint restricted to owners and administrators.

---

## 🧱 System Architecture

```
                  ┌───────────────────────────────┐
                  │    React Client (Vite/Tailwind) │
                  └───────────────┬───────────────┘
                                  │ HTTP / JSON (Bearer JWT)
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Django REST Framework API                     │
│                                                                 │
│   ┌───────────────────┐  ┌───────────────────┐  ┌─────────────┐ │
│   │   accounts App    │  │   theaters App    │  │bookings App │ │
│   │  - Auth & Profile │  │  - Theaters/Shows │  │- Transaction│ │
│   │  - SimpleJWT / OTP│  │  - Seats & Tiers  │  │- QR Verify  │ │
│   └───────────────────┘  └───────────────────┘  └─────────────┘ │
│                                                                 │
│             Middleware & Custom Permission Guards                │
│             (IsAuthenticated, IsAdminOrOwner)                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ ORM (Transactions & Row Locks)
                                ▼
         ┌──────────────────────────────────────────────┐
         │         Database Engine (ACID Compliant)     │
         │  - Runtime: Clever Cloud MySQL               │
         │  - Testing: In-Memory SQLite (:memory:)      │
         └──────────────────────────────────────────────┘
```

---

## 👥 Role-Based Access Control (RBAC)

| Role | Browse & Book Tickets | Manage Theaters & Shows | Owner Status & Map | Gatebox QR Scanner | Full Admin Panel |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **User (Customer)** | ✅ Yes | ❌ No | ❌ No | ❌ Denied (403) | ❌ No |
| **Owner** | ✅ Yes | ✅ Yes (Own items) | ✅ Yes | ✅ Allowed | ❌ No |
| **Admin** | ✅ Yes | ✅ Yes (All items) | ✅ Yes | ✅ Allowed | ✅ Full Access |

---

## ⚡ Atomic Seat Booking Engine

To prevent race conditions and overbooking when multiple users attempt to reserve the same seat simultaneously:

1. **Transaction Wrapping:** The booking process runs inside `transaction.atomic()`.
2. **Pessimistic Locking:** Targeted seat records are queried with `select_for_update()`.
3. **Availability Validation:** If any selected seat is already marked `is_booked=True` or has an active uncancelled booking, the entire transaction aborts immediately with HTTP 400 (`Seat(s) already booked`).
4. **Immediate Status Lock:** The seats are marked `is_booked=True`, an `Order` and corresponding `Booking` records are generated, and a unique `booking_code` (e.g., `BK-XXXXXXXX`) is assigned.
5. **Auto-Restoration:** If a booking is cancelled via `PATCH /bookings/<id>/cancel/`, the associated seat is freed (`is_booked=False`), and available seat counts are incremented automatically.

---

## 📡 API Reference

### 1. Authentication (`accounts/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/login/` | Authenticate user, return JWT tokens & profile | No |
| `POST` | `/signup/` | Register new account (`user` or `owner`) | No |
| `GET` | `/profile/` | Fetch current user's profile details | Yes |
| `POST` | `/token/refresh/` | Obtain fresh access token | No |
| `POST` | `/otp/request/` | Generate email verification OTP | No |
| `POST` | `/otp/verify/` | Verify OTP for password reset | No |

### 2. Shows & Seats (`theaters/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/shows/` | List all active shows with live seat counts | Optional |
| `GET` | `/shows/?managed=true` | Shows filtered for the authenticated owner | Owner / Admin |
| `GET` | `/shows/<id>/` | Detailed show information | Optional |
| `GET` | `/shows/<id>/seats/` | Full 100-seat layout with `is_mine`, `is_booked`, tier | Optional |
| `POST` | `/shows/` | Create a new screening (auto-generates 100 seats) | Owner / Admin |

### 3. Bookings & Verification (`bookings/`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/bookings/` | Create atomic booking for selected seat IDs | Yes |
| `GET` | `/my-tickets/` | Retrieve authenticated user's confirmed tickets | Yes |
| `PATCH`| `/bookings/<id>/cancel/` | Cancel confirmed ticket and free seat | Yes (Owner/Self) |
| `POST` | `/bookings/verify/` | Verify ticket QR pass against database | **Owner / Admin Only** |
| `POST` | `/bookings/clear-test-data/` | Clear sandbox test reservations | Yes |

---

## 💻 Local Development Setup

### Prerequisites
* **Python 3.11+** installed
* **MySQL** or **SQLite**
* **Git**

### Step-by-Step Installation

```bash
# 1. Clone repository & navigate to backend directory
cd MovieBooking_backend

# 2. Activate virtual environment
# Windows:
.\env\Scripts\activate
# Linux / macOS:
source env/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Configure environment variables (.env)
# Create a .env file with your database credentials:
# DB_NAME=your_db_name
# DB_USER=your_db_user
# DB_PASSWORD=your_db_password
# DB_HOST=your_db_host
# DB_PORT=3306

# 5. Apply migrations
python manage.py migrate

# 6. Run development server
python manage.py runserver 127.0.0.1:8000
```

The backend API will be available at `http://127.0.0.1:8000/`.

---

## 🧪 Automated Testing

The backend includes a comprehensive unit test suite covering the entire booking lifecycle:

```bash
python manage.py test
```

### Test Suite Coverage:
1. `test_seats_auto_generated_with_tiers`: Validates 100-seat matrix (20 VIP, 40 Premium, 40 Standard).
2. `test_atomic_multi_seat_booking_success`: Ensures atomic checkout, price tallying, and database locks.
3. `test_prevent_double_booking_conflict`: Verifies duplicate booking prevention and 400 error response.
4. `test_cancellation_releases_seat`: Confirms cancellation releases seat back to available status.
5. `test_owner_can_book_seats_normally`: Asserts owners can book tickets and view them in "My Tickets".
6. `test_seat_counts_synchronization`: Validates exact `-1` decrement and post-cancellation restoration.
7. `test_gatebox_scanner_permissions`: Confirms 403 Forbidden for regular users and access for owners/admins.
8. `test_seat_serializer_is_mine_logic`: Ensures accurate ownership identification per authenticated user.

*All 8 tests execute in an isolated in-memory SQLite database (`:memory:`) in ~12 seconds.*

---

## ☁️ Production Deployment

### Production Checklist
1. Set `DEBUG=False` in environment settings.
2. Ensure `ALLOWED_HOSTS` contains your production domain.
3. Serve static files with **WhiteNoise** or an S3 bucket:
   ```bash
   python manage.py collectstatic --noinput
   ```
4. Run via high-performance WSGI server:
   ```bash
   gunicorn moviebooking.wsgi:application --workers 3 --timeout 120
   ```

---

<p align="center">
  Crafted with precision by <b>Siva Kumar</b> • Built for scalable, production-grade cinema management.
</p>
