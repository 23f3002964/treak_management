# Project Report

## 1. Developer Details

**Name:** Aditya Raj  
**Email:** 23f3002964@ds.study.iitm.ac.in 

**About the Developer:** Developer with expertise in Python, Flask, PostgreSQL, and modern frontend technologies. Demonstrates strong understanding of MVC architecture, role-based access control, database design, and RESTful API development.

---

## 2. Project Details

### Project Title
**TrekOut — Trekking Management System**

### Problem Statement
Trekking organizations face significant operational challenges in managing trek routes, guide assignments, participant bookings, and real-time capacity tracking. Existing solutions are too generic (spreadsheets). There is a need for a purpose-built, role-based web application that streamlines the end-to-end workflow for administrators, guides, and trekkers while preventing overbooking and ensuring data integrity.

### Objectives
1. Provide a centralized platform for trek creation, scheduling, and guide assignment
2. Implement role-based access control for Admin, Staff (Guides), and Trekkers
3. Enable real-time slot availability tracking with overbooking prevention
4. Support booking management with cancellation workflows and business rule enforcement
5. Deliver a modern, responsive UI design system


### Target Users
| Role | Description |
|------|-------------|
| **Administrator** | Full system oversight: trek CRUD, staff approval, user management, booking logs |
| **Staff / Guide** | Manage assigned treks: update status, adjust slots, view participants |
| **Trekker (Participant)** | Browse available treks, book/cancel slots, view history, manage profile |

### Approach
- **Backend:** Flask 3.1.3 with application factory pattern, Blueprint-based modular routing
- **Database:** PostgreSQL with SQLAlchemy 2.0 ORM, declarative models, cascade relationships
- **Authentication:** Session-based with signed cookies, bcrypt password hashing (Werkzeug)
- **Authorization:** Decorator-based RBAC (`login_required`, `role_required`)
- **Frontend:** Server-rendered Jinja2 templates, Bootstrap 5.3, FontAwesome 6, Google Fonts
- **Design System:** Custom CSS with CSS custom properties, glassmorphism components, responsive grids

---

## 3. AI  Declaration

**Estimated AI Usage:** ~15–25% 

**AI-Assisted Areas:**
- Boilerplate debugging-code generation 
- CSS design system (glassmorphism variables, component classes)
- Template structure and Bootstrap integration

---

## 4. Technologies & Frameworks Used

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Core programming language | 3.14  |
| **Flask** | Web framework (routing, templates, sessions) | 3.1.3 |
| **Flask-SQLAlchemy** | ORM for PostgreSQL | 3.1.1 |
| **SQLAlchemy** | Core ORM engine | 2.0.51 |
| **PostgreSQL** | Primary relational database | 14+ |
| **psycopg2-binary** | PostgreSQL driver for Python | 2.9.12 |
| **Werkzeug** | WSGI utilities, password hashing, routing | 3.1.8 |
| **Bootstrap** | CSS framework (grid, components, utilities) | 5.3.0 (CDN) |
| **FontAwesome** | Icon library | 6.4.0 (CDN) |
| **Google Fonts** | Typography (Inter, Outfit) | Latest (CDN) |
| **Jinja2** | Template engine | 3.1.6 |


---

## 5. Database Schema

### Database
**Type:** PostgreSQL  
**Connection URI Pattern:** `postgresql://user:pass@host:5432/trekking_db`  
**Auto-Creation:** `db_init.py` connects to default `postgres` database and creates `trekking_db` if missing

### ORM
**Flask-SQLAlchemy 3.1.1** with **SQLAlchemy 2.0** declarative base

### Models

#### 5.1 User Model (`application/models.py`)
```python
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact_details = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'staff', 'trekker'
    status = db.Column(db.String(20), nullable=False)  # 'active', 'pending', 'approved', 'blacklisted'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    assigned_treks = db.relationship('Trek', backref='assigned_staff', 
                                     foreign_keys='Trek.assigned_staff_id', lazy=True)
    bookings = db.relationship('Booking', backref='trekker', lazy=True)
```

**Primary Key:** `id` (Integer, Auto-increment)  
**Unique Constraints:** `username`  
**Indexes:** `username` (explicit index)  
**Foreign Keys:** None (referenced by Trek.assigned_staff_id, Booking.user_id)

#### 5.2 Trek Model
```python
class Trek(db.Model):
    __tablename__ = 'treks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # 'Easy', 'Moderate', 'Hard'
    duration = db.Column(db.Integer, nullable=False)  # days
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', 'Open', 'Closed', 'Completed'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, default=0.0)
    
    # Relationships
    bookings = db.relationship('Booking', backref='trek', 
                               cascade='all, delete-orphan', lazy=True)
```

**Primary Key:** `id` (Integer, Auto-increment)  
**Foreign Keys:** `assigned_staff_id` → `users.id` (ON DELETE SET NULL)  
**Cascade:** `bookings` — `all, delete-orphan` (deleting trek removes its bookings)  
**Enums (Application-Level):** `difficulty` ∈ {Easy, Moderate, Hard}, `status` ∈ {Pending, Approved, Open, Closed, Completed}

#### 5.3 Booking Model
```python
class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')  # 'Booked', 'Cancelled', 'Completed'
```

**Primary Key:** `id` (Integer, Auto-increment)  
**Foreign Keys:** 
- `user_id` → `users.id` (ON DELETE CASCADE)
- `trek_id` → `treks.id` (ON DELETE CASCADE)  
**Enums (Application-Level):** `status` ∈ {Booked, Cancelled, Completed}

### Relationships Summary

| From | To | Type | Cascade | On Delete |
|------|-----|------|---------|-----------|
| User.assigned_treks | Trek | One-to-Many | — | SET NULL (on staff) |
| User.bookings | Booking | One-to-Many | — | CASCADE |
| Trek.assigned_staff | User | Many-to-One | — | SET NULL |
| Trek.bookings | Booking | One-to-Many | all, delete-orphan | CASCADE |
| Booking.trekker | User | Many-to-One | — | CASCADE |
| Booking.trek | Trek | Many-to-One | — | CASCADE |


![alt text](image.png)

https://drive.google.com/file/d/1ZB_Lw4nutWWPs9SQyT_bW9T7xjNaN7Rn/view?usp=sharing
---

## 6. API Resource Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/treks` | Retrieve all treks as JSON array | Public (no auth) |
| GET | `/api/bookings` | Retrieve all bookings as JSON array | Admin only (session) |
| GET | `/api/users` | Retrieve all users as JSON array | Admin only (session) |

### 6.1 `/api/treks` — GET
**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Valley of Flowers",
    "location": "Uttarakhand",
    "difficulty": "Moderate",
    "duration": 5,
    "total_slots": 15,
    "available_slots": 10,
    "assigned_staff_id": null,
    "assigned_staff_name": "None",
    "status": "Open",
    "start_date": "2026-08-01",
    "end_date": "2026-08-05",
    "description": "Beautiful trek through flowers",
    "price": 150.0
  }
]
```

### 6.2 `/api/bookings` — GET
**Authentication:** Session cookie with `role=admin`  
**Response (200 OK):** Array of booking objects with nested trekker and trek details  
**Error (403 Forbidden):** `{"error": "Unauthorized access. Admin privileges required."}`

### 6.3 `/api/users` — GET
**Authentication:** Session cookie with `role=admin`  
**Response (200 OK):** Array of user objects (password_hash excluded)  
**Error (403 Forbidden):** `{"error": "Unauthorized access. Admin privileges required."}`

---

### 7 Authentication Flow

```
1. User submits credentials → POST /login
2. Server validates: User.exists ∧ check_password_hash(password_hash, password)
3. On success: session['user_id'], session['username'], session['role'], session['name'] set
4. Encrypted session cookie sent to browser (SECRET_KEY)
5. Subsequent requests: Browser sends cookie → Flask decrypts → session available
6. Decorators verify: session['user_id'] exists, user not deleted, not blacklisted
7. Role decorators verify: session['role'] ∈ allowed_roles
8. Staff decorator additionally checks: user.status == 'approved'
```


---


## 8. Submission Contents

### 8.1 Directory Structure

```
MAD/
├── main.py                      # Application entry point
├── db_init.py                   # Database initialization & admin seeding
├── requirements.txt             # Python dependencies
├── PROJECT_REPORT.md            # Business-facing project report
├── application/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration management
│   ├── controllers.py           # All routes & business logic (~750 lines)
│   └── models.py                # Database models (User, Trek, Booking)
├── templates/
│   ├── base.html                # Master layout (navbar, footer, flash)
│   ├── index.html               # Landing page
│   ├── login.html               # Login form
│   ├── register.html            # Registration form
│   ├── admin/
│   │   ├── dashboard.html       # Admin stats + pending staff + recent bookings
│   │   ├── treks.html           # Trek CRUD with modals, assign guide dropdown
│   │   ├── staff.html           # Staff approval/blacklist management
│   │   ├── users.html           # Trekker blacklist management
│   │   └── bookings.html        # Global bookings log with filters
│   ├── staff/
│   │   ├── dashboard.html       # Assigned treks overview
│   │   ├── trek_detail.html     # Trek status/slots + participant list
│   │   └── pending.html         # Pending approval page
│   ├── user/
│   │   ├── dashboard.html       # Browse treks with search/filter
│   │   ├── history.html         # Booking history with cancellation
│   │   └── profile.html         # Profile & password update
│   └── errors/
│       ├── 404.html             # Not found page
│       └── 500.html             # Server error page
└── static/
    └── css/
        └── style.css            # Glassmorphism design system
```


### Video Demo url :-

https://drive.google.com/drive/folders/15-u98yaRy5aN-zOug7hKoIpupFb8mzBx?usp=sharing


*Project: TrekOut — Trekking Management System* 