# 🥛 Shree Milk Bank Dairy — Smart Dairy ERP

A complete **web-based Dairy Management System (Dairy ERP)** that digitizes the entire milk value chain — from farmer registration and daily milk collection to quality testing, automated pricing, payments, procurement, inventory, reporting, and branch operations — in one unified platform.

Built with a **Flask REST API backend** and a **vanilla JavaScript single-page application (SPA) frontend**, Smart Dairy ERP is designed for dairy cooperatives, milk collection centers, and dairy companies operating across multiple branches.

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🧱 Tech Stack](#-tech-stack)
- [🏗️ Architecture Overview](#️-architecture-overview)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
  - [Seeding Demo Data](#seeding-demo-data)
  - [Default Login Credentials](#default-login-credentials)
- [📁 Project Structure](#-project-structure)
- [🗄️ Database Models](#️-database-models)
- [🔐 Authentication & Role-Based Access](#-authentication--role-based-access)
- [🧮 Pricing Engine & Quality Grading](#-pricing-engine--quality-grading)
- [📡 REST API Reference](#-rest-api-reference)
- [🖥️ Frontend Architecture](#️-frontend-architecture)
- [🧪 Testing](#-testing)
- [🔒 Security Notes](#-security-notes)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [📄 License](#-license)

---

## ✨ Features

### 📊 Dashboard & Analytics
- Real-time KPI cards — today's collection (liters), revenue, active farmers, average fat/SNF, pending payments, rejections, and collection efficiency.
- Interactive **collection & revenue trend charts** (14 / 30 day views) built on Chart.js.
- **Branch performance** comparison table with ₹/liter efficiency metric.
- Today's entries feed, pending payments list, new farmers, top-5 farmers by quantity, and a system health panel.

### 🧪 Milk Collection Desk
- Three-panel collection workflow: **find farmer → enter analyzer readings → see live price**.
- Farmer lookup by **QR code, code, phone, or name** with a live queue.
- Fat/SNF analyzer input grid (fat, SNF, CLR, temperature, density, water, protein, lactose).
- **Live pricing engine** that recomputes rate/liter and total amount as you type.
- Auto-generated sequential receipt numbers (`RC0000001`).

### 👨‍🌾 Farmer Management
- Full farmer registration: personal info, address, livestock details, bank account, and branch assignment.
- **Auto-generated farmer codes** by milk type (`C1042` = Cow, `B0387` = Buffalo, `M0215` = Mixed).
- Farmer profiles with quick stats, quality & earnings charts, and collection passbook.
- Farmer status workflow: `ACTIVE`, `INACTIVE`, `BLOCKED` (with reason).
- QR code generation for fast identification at the collection desk.

### 💰 Payments
- **Generate payment sheets** from unpaid, accepted collections within a date range (grouped per farmer).
- Payment lifecycle: `PENDING → APPROVED → PAID` with paid-at timestamp and reference number.
- Payment summary — total paid (this month), total pending, and payment rate %.

### 📈 Rate Engine (Pricing)
- **Versioned fat/SNF rates** per milk type (COW / BUFFALO) with effective-from/to dates.
- Creating a new rate automatically deactivates the previous active version and bumps the version number.

### 🔬 Quality Control
- Full lab test parameters: fat, SNF, CLR, density, protein, lactose, water content, temperature, acidity, MBRT, alcohol test, freezing point.
- **Automatic quality grading** (PASS / BORDERLINE / FAIL) based on configurable thresholds with explanatory warnings.

### ❌ Milk Rejections
- Record rejected milk with predefined reasons (`HIGH_WATER`, `LOW_FAT`, `SOUR_MILK`, `HIGH_TEMP`, `ADULTERATION`, `OTHER`).
- Linked rejections automatically mark the corresponding collection as `REJECTED`.

### 🏢 Multi-Branch Operations
- Manage branches with codes, managers, and contact/address details.
- **Branch-level data isolation** — branch-scoped users only see their own branch's data.

### 🚚 Procurement & Logistics
- **Collection centers** (MAIN, SUB_CENTER, CHILLING_POINT, MOBILE) with capacity and operating hours.
- **Collection routes** with driver and vehicle assignment.
- **Chilling centers** with tank count, capacity, current stock, and generator backup info.

### 📦 Inventory
- Stock items with categories, units, and minimum stock thresholds.
- Automatic **Low Stock / In Stock** status detection.

### 👷 Employees & 🚛 Vehicles
- Employee registry (operators, accountants, managers, drivers) with salary and branch.
- Vehicle fleet management (TANKER, PICKUP, MINI_VAN) with capacity, driver, service dates, and maintenance status.

### 📋 Reports
- Six report types with date-range and branch filters:
  - **Collection report** — totals, morning/evening split, avg fat/SNF.
  - **Payment report** — paid vs pending amounts.
  - **Farmer ledger** — complete per-farmer transaction history.
  - **Quality report** — pass/borderline/fail rates.
  - **Rejection report** — quantities grouped by reason.
  - **Branch report** — side-by-side branch comparison.

### 🧾 Audit Trail
- Complete **audit log** of all actions (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT) with entity, user, IP, and timestamps — visible to SUPER_ADMIN only.

### 🔔 Notifications & Settings
- In-app notification center (payment, collection, quality, system, farmer types) with unread counts.
- System settings: dairy name, currency, timezone, language, auto-backup scheduling, and notification toggles.
- Backup creation/download and API key regeneration.

### 🎨 UX / UI
- Dark & light theme toggle, mobile-responsive sidebar, global search, breadcrumbs, live clock.
- Multi-language login screen (English / मराठी / हिंदी).
- CSV export and print support on all major tables.

---

## 🧱 Tech Stack

| Layer        | Technology |
|--------------|-----------|
| **Backend**  | Python 3, Flask 3.1.0 |
| **Database** | SQLite (default) — any SQLAlchemy-supported DB via `DATABASE_URL` |
| **ORM**      | Flask-SQLAlchemy 3.1.1 |
| **Auth**     | Flask-JWT-Extended 4.7.1 (JWT Bearer tokens), bcrypt 4.2.1 (password hashing) |
| **CORS**     | Flask-CORS 5.0.1 |
| **Config**   | python-dotenv 1.1.0 (`.env` support) |
| **Frontend** | Vanilla JavaScript SPA (no framework), HTML5, CSS3 design system |
| **Charts**   | Chart.js 4.4.7 (CDN) |
| **Icons**    | Lucide (CDN) |
| **Fonts**    | Google Fonts — Inter & Playfair Display |

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                    FRONTEND (SPA)                          │
│   templates/index.html  +  static/js/*  +  static/css/*    │
│   Hash-based routing (Router.navigate) → page containers   │
│   API client (api.js) → fetch() with JWT Bearer header     │
└───────────────────────────┬────────────────────────────────┘
                            │  JSON over HTTP (REST)
┌───────────────────────────▼────────────────────────────────┐
│                    BACKEND (Flask)                         │
│   app.py — application factory (create_app)                │
│   Blueprints per module → routes/*_routes.py               │
│   auth.py — JWT helpers + RBAC decorators                  │
│   pricing.py — pricing & quality-grading business logic    │
│   utils.py — formatting & code generators                  │
│   models.py — SQLAlchemy ORM models                        │
└───────────────────────────┬────────────────────────────────┘
                            │  SQLAlchemy
┌───────────────────────────▼────────────────────────────────┐
│                    DATABASE (SQLite)                       │
│   smart_dairy.db  — auto-created via db.create_all()       │
└────────────────────────────────────────────────────────────┘
```

**Key design points:**

- **Application factory pattern** (`backend/app.py`) — `create_app()` configures the Flask app, initializes extensions (CORS, SQLAlchemy, JWT), registers blueprints, and creates database tables.
- **REST API + SPA** — the backend is a pure JSON API. A single `index.html` shell hosts every page; the JS router shows/hides page containers based on the URL hash (`#dashboard`, `#farmers`, …).
- **JWT stateless auth** — tokens carry the user identity (id, username, name, role, branch) as a JSON string in the `sub` claim; the client stores it in `localStorage`.
- **Branch isolation** — non-global roles automatically get their queries scoped to their assigned `branch_id`.
- **Versioned & immutable records** — collections are immutable receipts; rate changes are versioned instead of overwritten.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** installed and available on `PATH`
- *(Optional but recommended)* a virtual environment
- Git (to clone the repository)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/parshwa12367556/Shree-Milk-Bank-Dairy.git
cd shree-milk-bank-dairy

# 2. (Recommended) Create & activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configuration

All configuration is loaded from environment variables (optionally via a `.env` file at the project root). Create a `.env` file to override defaults:

```ini
# Application environment: development | production
FLASK_ENV=development

# Change these in production!
SECRET_KEY=your-very-long-random-secret
JWT_SECRET_KEY=your-very-long-random-jwt-secret

# Database (defaults to SQLite at ./smart_dairy.db)
DATABASE_URL=sqlite:///smart_dairy.db
```

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Enables Flask debug mode when `development` |
| `SECRET_KEY` | hard-coded dev value | Flask session/signing secret — **must change in production** |
| `JWT_SECRET_KEY` | hard-coded dev value | JWT signing secret — **must change in production** |
| `DATABASE_URL` | `sqlite:///smart_dairy.db` | SQLAlchemy database URL (any supported dialect) |

The default JWT access token lifetime is **24 hours** (configurable in `config.py`).

### Running the Application

```bash
python run.py
```

The development server starts at **http://localhost:5000** (debug mode, auto-reload enabled).

> The SQLite database file (`smart_dairy.db`) is created automatically on first run with all tables.

### Seeding Demo Data

To populate the database with realistic sample data (branches, users, 20+ farmers, 14 days of collections, payments, quality tests, rejections, procurement, inventory, employees, vehicles, notifications, and audit logs):

```bash
python run.py --seed
```

> ⚠️ **Seeding clears all existing data** before inserting sample data.

### Default Login Credentials

After seeding, use these accounts:

| Username    | Password       | Role           | Branch Scope        |
|-------------|----------------|----------------|---------------------|
| `admin`     | `admin123`     | SUPER_ADMIN    | All branches        |
| `manager`   | `manager123`   | BRANCH_MANAGER | Branch 1 (Agar)     |
| `operator`  | `operator123`  | OPERATOR       | Branch 1 (Agar)     |
| `accountant`| `accountant123`| ACCOUNTANT     | All branches        |

---

## 📁 Project Structure

```
shree-milk-bank-dairy/
├── run.py                      # Entry point (python run.py [--seed])
├── config.py                   # Environment-based configuration classes
├── requirements.txt            # Python dependencies
├── smart_dairy.db              # SQLite database (auto-created)
├── backend/
│   ├── app.py                  # Application factory, JWT handlers, blueprint registration
│   ├── auth.py                 # Password hashing, JWT identity, RBAC decorators
│   ├── models.py               # All SQLAlchemy ORM models
│   ├── pricing.py              # Pricing formula & quality auto-grading engine
│   ├── utils.py                # INR formatting, date helpers, code generators
│   ├── seed.py                 # Database seeder (sample data)
│   └── routes/                 # One blueprint per module
│       ├── auth_routes.py      #   Login/logout/profile/password
│       ├── dashboard_routes.py #   Aggregated dashboard stats
│       ├── health_routes.py    #   /api/health
│       ├── branch_routes.py    #   Branch CRUD
│       ├── farmer_routes.py    #   Farmer CRUD + stats
│       ├── collection_routes.py#   Milk collections
│       ├── payment_routes.py   #   Payment sheets & approvals
│       ├── pricing_routes.py   #   Rate master (versioned)
│       ├── quality_routes.py   #   Quality tests with auto-grading
│       ├── rejection_routes.py #   Milk rejections
│       ├── procurement_routes.py # Collection centers, routes, chilling centers
│       ├── inventory_routes.py #   Stock items
│       ├── employee_routes.py  #   Employees
│       ├── vehicle_routes.py   #   Vehicles
│       ├── report_routes.py    #   Six report types
│       ├── audit_routes.py     #   Audit logs (SUPER_ADMIN)
│       ├── settings_routes.py  #   System settings & backups
│       └── notification_routes.py # In-app notifications
├── templates/
│   └── index.html              # SPA shell — contains ALL page views
│   # (other *.html files in this folder are legacy/unused — only
│   #  index.html is rendered by the app; pages load inside the SPA)
├── static/
│   ├── css/                    # Design system & page styles (variables.css, style.css, …)
│   └── js/                     # Vanilla JS modules
│       ├── api.js              #   REST API client (window.API)
│       ├── router.js           #   Hash router (window.Router)
│       ├── app.js              #   App bootstrap & global handlers
│       ├── auth.js             #   Login/logout/session logic
│       ├── storage.js          #   localStorage wrapper
│       ├── chart.js            #   Chart.js helpers
│       ├── table.js            #   Table rendering, CSV export, print
│       ├── utils.js            #   Shared UI helpers
│       └── *.js                #   One controller per page (dashboard, farmers, collection, …)
├── test_check.py               # Smoke test — verifies the app serves correctly
└── test_seed.py                # Verifies database seeding
```

---

## 🗄️ Database Models

All models live in `backend/models.py` and use SQLAlchemy ORM. Tables are created automatically via `db.create_all()`.

| Model              | Table                | Purpose                                                      |
|--------------------|----------------------|--------------------------------------------------------------|
| `User`             | `users`              | System accounts with roles (`SUPER_ADMIN`, `HEAD_OFFICE`, `BRANCH_MANAGER`, `OPERATOR`,  `ACCOUNTANT`) |
| `Branch`           | `branches`           | Dairy branches / collection centers |
| `Farmer`           | `farmers`            | Registered milk producers (personal, address, livestock data) |
| `BankDetail`       | `bank_details`       | One-to-one farmer bank/UPI details |
| `RateMaster`       | `rate_masters`       | Versioned fat/SNF pricing rates per milk type |
| `Collection`       | `collections`        | Daily milk collection receipts (immutable after creation) |
| `Payment`          | `payments`           | Payment sheets linking collections to farmer payouts |
| `QualityTest`      | `quality_tests`      | Lab quality test records with auto-grading results |
| `MilkRejection`    | `milk_rejections`    | Rejected milk records with reasons |
| `CollectionCenter` | `collection_centers` | Procurement collection centers |
| `CollectionRoute`  | `collection_routes`  | Milk collection routes |
| `ChillingCenter`   | `chilling_centers`   | Chilling/cooling storage centers |
| `InventoryItem`    | `inventory_items`    | Stock items with min-stock thresholds |
| `Employee`         | `employees`          | Staff records |
| `Vehicle`          | `vehicles`           | Fleet registry |
| `AuditLog`         | `audit_logs`         | Full audit trail of system actions |
| `Notification`     | `notifications`      | In-app notifications per user/global |

**Code generation conventions** (see `backend/utils.py`):

| Code type | Format | Example |
|-----------|--------|---------|
| Collection receipt | `RC` + 7-digit zero-padded | `RC0001241` |
| Payment code | `PAY` + 7-digit zero-padded | `PAY0000101` |
| Farmer code | `C`/`B`/`M` (milk type) + sequence | `C1042`, `B0387`, `M0215` |

---

## 🔐 Authentication & Role-Based Access

**Authentication flow:**
1. `POST /api/auth/login` with username + password → returns a **JWT** (`Bearer <token>`) and user object.
2. The client stores the token in `localStorage` (`sd_token`) and sends it via the `Authorization: Bearer <token>` header on every request.
3. `GET /api/auth/me` returns the current session; `POST /api/auth/logout` is client-side (stateless tokens).

**Password handling:** bcrypt hashing (`hash_password` / `check_password` in `backend/auth.py`).

**Role hierarchy & permissions:**

| Capability | Allowed Roles |
|------------|---------------|
| Record collections (`can_collect`) | SUPER_ADMIN, HEAD_OFFICE, BRANCH_MANAGER, OPERATOR |
| Payments & approvals (`can_pay`) | SUPER_ADMIN, HEAD_OFFICE, ACCOUNTANT |
| Manage rates (`can_manage_rates`) | SUPER_ADMIN, HEAD_OFFICE |
| Global / cross-branch access (`is_global_role`) | SUPER_ADMIN, HEAD_OFFICE |
| Branch CRUD | SUPER_ADMIN, HEAD_OFFICE |
| Audit logs | SUPER_ADMIN only |
| Settings & backups | SUPER_ADMIN (settings PATCH: SUPER_ADMIN + HEAD_OFFICE) |

**Branch isolation:** roles without global access automatically see only data belonging to their assigned `branch_id` (enforced on collections, farmers, and payments queries).

---

## 🧮 Pricing Engine & Quality Grading

### Pricing formula (`backend/pricing.py` → `compute_price`)

```
rate_per_liter = fat × fat_rate + snf × snf_rate
amount         = rate_per_liter × quantity
```

Example: fat = 4.2%, SNF = 8.6%, fat_rate = ₹5.00, snf_rate = ₹2.50, quantity = 25 L
→ rate_per_liter = 4.2 × 5.00 + 8.6 × 2.50 = ₹42.50/L → amount = ₹1,062.50

### Quality auto-grading (`backend/pricing.py` → `auto_grade_quality`)

| Parameter | PASS | BORDERLINE | FAIL |
|-----------|------|-----------|------|
| Temperature | ≤ 6°C | 6–8°C | > 8°C |
| CLR | ≥ min\* | min−2 ≤ CLR < min | < min−2 |
| Water content | ≤ 5% | 5–8% | > 8% |
| Fat | ≥ min\* | 70–100% of min | < 70% of min |

\*Minimums by milk type — Fat: COW 3.0%, BUFFALO 4.5%, MIXED 3.5% · CLR: COW 28.0, BUFFALO 27.0, MIXED 27.5.

Overall result = `FAIL` if any parameter fails → `BORDERLINE` if any borderline → `PASS` otherwise. The grading response includes per-parameter status and human-readable warnings stored on the quality test record.

---

## 📡 REST API Reference

All endpoints return JSON. Except where noted, every endpoint requires `Authorization: Bearer <token>`.

### System & Auth
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/health` | Health check (version, timestamp) | Public |
| POST | `/api/auth/login` | Authenticate and receive JWT | Public |
| POST | `/api/auth/logout` | Logout | Any |
| GET | `/api/auth/me` | Current user session | Any |
| PATCH | `/api/auth/profile` | Update own profile | Any |
| POST | `/api/auth/change-password` | Change own password | Any |
| POST | `/api/auth/forgot-password` | Request password reset | Public |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | KPIs, trends, branch performance, today's entries (`?days=14\|30`) |

### Branches
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/branches` | List active branches | Public |
| POST | `/api/branches` | Create branch | SUPER_ADMIN, HEAD_OFFICE |
| PATCH | `/api/branches/<id>` | Update branch | SUPER_ADMIN, HEAD_OFFICE |
| DELETE | `/api/branches/<id>` | Soft-delete branch | SUPER_ADMIN, HEAD_OFFICE |

### Farmers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/farmers` | List (paged; filters: `q`, `branchId`, `milk_type`, `status`) |
| POST | `/api/farmers` | Register farmer (auto-generates code) |
| GET | `/api/farmers/stats` | Farmer statistics by type/status |
| GET | `/api/farmers/<code>` | Farmer detail + stats + recent collections |
| PATCH | `/api/farmers/<code>` | Update farmer |

### Collections
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/collections` | List (filters: `date`, `shift`, `farmerId`, `branchId`) |
| POST | `/api/collections` | Record collection (roles: collect) — computes price, returns receipt |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payments` | List + summary (paid/pending/rate) |
| POST | `/api/payments` | Generate payment sheets from unpaid collections |
| PATCH | `/api/payments/<id>` | Set status to `APPROVED` or `PAID` |

### Pricing / Rate Engine
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/pricing` | All rate versions + current COW/BUFFALO rates |
| POST | `/api/pricing` | Create new rate version (deactivates previous) |

### Quality & Rejections
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET / POST | `/api/quality` | List / create quality test (auto-graded) |
| GET / POST | `/api/rejections` | List / record milk rejection |

### Procurement, Inventory, Employees, Vehicles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET / POST | `/api/procurement/centers` | Collection centers |
| GET / POST | `/api/procurement/routes` | Collection routes |
| GET / POST | `/api/procurement/chilling` | Chilling centers |
| GET / POST | `/api/inventory` | Inventory items |
| GET / POST | `/api/employees` | Employees |
| GET / POST | `/api/vehicles` | Vehicles |
| PATCH / DELETE | `/api/vehicles/<id>` | Update / delete vehicle |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports?type=<type>&from=&to=&branchId=&farmerId=` | Report engine — types: `collection`, `payment`, `farmer`, `quality`, `rejection`, `branch` |

### Audit, Settings, Notifications
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/audit` | Audit log list | SUPER_ADMIN |
| GET / PATCH | `/api/settings` | Get / update system settings | PATCH: SUPER_ADMIN, HEAD_OFFICE |
| POST / GET | `/api/settings/backup` | Create / download backup | SUPER_ADMIN |
| POST | `/api/settings/regenerate-key` | Regenerate API key | SUPER_ADMIN |
| GET / PATCH / DELETE | `/api/notifications` | List / mark-read / delete notifications | Any |

---

## 🖥️ Frontend Architecture

The frontend is a **single-page application without any framework** — all views live inside `templates/index.html` as `<div class="page-container">` blocks, and vanilla JS modules control behavior.

- **Routing** (`static/js/router.js`): hash-based routing. `Router.navigate('farmers')` switches the visible page container and updates `window.location.hash` (`#farmers`). The router also listens to `hashchange`.
- **API client** (`static/js/api.js`): a single `API` object wrapping `fetch()` — automatically attaches the JWT `Authorization` header, centralizes 401 handling (clears session, redirects to login), and exposes typed helpers (`API.getFarmers(...)`, `API.createCollection(...)`, …).
- **State** (`static/js/storage.js`): localStorage wrapper. Keys: `sd_token`, `sd_user`, `sd_theme`, `sd_sidebar`.
- **Page controllers**: one JS file per module (`dashboard.js`, `farmers.js`, `collection.js`, `payments.js`, `pricing.js`, `quality.js`, `rejections.js`, `branches.js`, `procurement.js`, `inventory.js`, `employees.js`, `vehicles.js`, `reports.js`, `audit.js`, `settings.js`, `notifications.js`, `profile.js`, `farmer-form.js`, `farmer-profile.js`).
- **Shared components**: `table.js` (rendering, sorting, pagination, CSV export, print), `chart.js` (Chart.js wrapper), `modal.js` (modal dialogs), `form-validation.js`, `utils.js`.
- **Design system** (`static/css/`): CSS custom properties in `variables.css` drive theming (light/dark via `data-theme` attribute on `<html>`), `style.css` provides base layout, `responsive.css` handles mobile, and per-module stylesheets cover each page.
- **CDN dependencies**: Chart.js 4.4.7, Lucide icons, Google Fonts (Inter + Playfair Display).

---

## 🧪 Testing

Two lightweight verification scripts are included (no test framework required):

```bash
# 1. Smoke test — verifies the Flask app boots and serves the SPA correctly
python test_check.py

# 2. Seed test — verifies database seeding
#    ⚠️ WARNING: Deletes smart_dairy.db first, then re-seeds it
python test_seed.py
```

The seed test prints a summary of seeded row counts (users, branches, farmers, collections, payments, quality tests, rejections, inventory, employees, vehicles) and exits with `=== ALL OK ===` on success.

---

## 🔒 Security Notes

> **For production deployment, you MUST do the following:**

1. **Change the secrets** — set strong random values for `SECRET_KEY` and `JWT_SECRET_KEY` via environment variables (never use the hard-coded development defaults).
2. **Set `FLASK_ENV=production`** — this disables Flask debug mode (which otherwise exposes the interactive debugger).
3. **Run behind a production WSGI server** — use Gunicorn / Waitress / uWSGI instead of the built-in development server.
4. **Use a production-grade database** — the default SQLite setup is fine for a single-instance deployment; switch `DATABASE_URL` to PostgreSQL or MySQL for multi-instance/high-availability setups.
5. **Enable HTTPS** — all traffic should be TLS-encrypted, since authentication uses Bearer tokens.
6. **Password reset** — `POST /api/auth/forgot-password` currently returns the reset email in the response (dev-mode behavior). Wire it to a real email-sending service (e.g., SMTP, SendGrid, Resend) before production.
7. **Settings store** — system settings and backups are stored in memory (`settings_routes.py`); persist them to the database for multi-process deployments.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Activate your virtual environment and run `pip install -r requirements.txt` |
| Port 5000 already in use | Change the port in `run.py` (`app.run(debug=True, port=5000)`) |
| Login fails after fresh install | The database has no users — run `python run.py --seed` to create demo accounts |
| Database is missing / tables not created | Tables are auto-created on app start; verify `smart_dairy.db` is writable |
| `Invalid username or password` | Check the username is exact and use the seeded passwords (`admin123`, etc.) |
| Seed script errors | `test_seed.py` / `--seed` clears the DB first — back up `smart_dairy.db` if you have real data |
| Collections show wrong price | Verify the active `RateMaster` version for the farmer's milk type in **Rate Engine** |
| Branch user sees no data | Confirm the user is assigned to a branch and that branch has data (see **Branches**) |
| JWT expiry errors (401) | Tokens last 24h by default — log in again to refresh |

---

## 📄 License

This project is proprietary/internal. See the repository owner for licensing and usage terms.

---

*Built with ❤️ for the dairy industry — Shree Milk Bank Dairy.*
