# 🥛 Shree Milk Bank Dairy — Smart Dairy ERP

A complete **web-based Dairy Management System (Dairy ERP)** that digitizes the entire milk value chain — from farmer registration and daily milk collection to quality testing, automated pricing, payments, procurement, inventory, reporting, and multi-branch operations — in one unified platform.

Built with a **Flask REST API backend** and a **vanilla JavaScript single-page application (SPA) frontend**, Smart Dairy ERP is designed for dairy cooperatives, milk collection centers, and dairy companies operating across multiple branches.

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🧱 Tech Stack](#-tech-stack)
- [🏗️ Architecture Overview](#️-architecture-overview)
- [🚀 Getting Started](#-getting-started)
- [📁 Project Structure](#-project-structure)
- [🗄️ Database Models](#️-database-models)
- [🔐 Authentication, Roles & Permission Matrix](#-authentication-roles--permission-matrix)
- [🧮 Pricing Engine & Quality Grading](#-pricing-engine--quality-grading)
- [📡 REST API Reference](#-rest-api-reference)
- [🖥️ Frontend Architecture](#️-frontend-architecture)
- [🧪 Testing](#-testing)
- [🔒 Security Notes](#-security-notes)
- [🛠️ Troubleshooting](#️-troubleshooting)

---

## ✨ Features

### 🏢 Organization & Branch Model
- One **Head Office (Super Admin)** + multiple dairy branches (BR01–BR05+), all under one company: **Shree Milk Bank Dairy**.
- **Branch-level data isolation** — branch managers only see their own branch's data; the Super Admin sees everything.
- Branch management: create, edit, activate/deactivate, **reset password**, and soft-delete.

### 📊 Dashboard & Analytics
- Real-time KPI cards — today's collection (liters), revenue, active farmers, average fat/SNF, pending payments, rejections, and collection efficiency.
- **Profit & Loss KPIs** — 30-day revenue, expenses, and profit.
- **Monthly collection**, **rejected-milk %**, and **low-stock count** analytics.
- Interactive **collection & revenue trend charts** (14 / 30 day views) built on Chart.js.
- **Branch performance** comparison table with ₹/liter efficiency metric.
- Today's entries feed, pending payments list, new farmers, top-5 farmers by quantity, and a system health panel.

### 👨‍🌾 Farmer Management & Verification Workflow
- Full farmer registration (branch manager only): personal info, address, livestock details, bank/UPI details.
- **Auto-generated farmer IDs** per branch: `<branch_code><3-digit serial>` — e.g. `BR01001`, `BR01002` (unique company-wide, non-editable).
- **Head Office verification workflow**:
  - `PENDING_VERIFICATION` (on registration) → Head Office **Approves** → `ACTIVE`
  - or Head Office **Rejects** (with reason) → `REJECTED` → branch edits & **resubmits**
- **Bank detail verification** — Head Office can Verify/Reject the farmer's bank name, account number, IFSC, and Aadhaar.
- Farmer statuses: `PENDING_VERIFICATION`, `ACTIVE`, `REJECTED`, `BLOCKED`, `INACTIVE`.
- **Payments can only be generated for `ACTIVE` farmers.**
- Super Admin views all farmers across all branches; search by Farmer ID, name, mobile, **Aadhaar**, or village; filter by branch, milk type, and status.
- Farmer profiles with quick stats, quality & earnings charts, and collection **passbook**.
- **CSV export** of the farmer list (branch-scoped).

### 🧪 Milk Collection Desk
- Three-panel collection workflow: **find farmer → enter analyzer readings → see live price**.
- Farmer lookup by **QR code, code, phone, or name** with a live queue.
- Fat/SNF analyzer input grid (fat, SNF, CLR, temperature, density, water, protein, lactose).
- **Live pricing engine** that recomputes rate/liter and total amount as you type.
- Auto-generated sequential receipt numbers (`RC0000124`); collections are immutable once accepted.

### 💰 Payments (Head Office Only)
- **Only the Super Admin** can generate, approve, and mark payments (`can_pay`).
- **Generate payment sheets** from unpaid, accepted collections within a date range (grouped per farmer).
- Payment lifecycle: `PENDING → APPROVED → PAID` with paid-at timestamp and **bank reference (UTR)** number.
- Pending/completed totals and payment rate % on the payments page.

### 📈 Rate Engine (Pricing)
- **Versioned fat/SNF rates** per milk type (COW / BUFFALO) with effective-from/to dates.
- Creating a new rate automatically deactivates the previous active version and bumps the version number.

### 🔬 Quality Control & ❌ Milk Rejections
- Full lab test parameters: fat, SNF, CLR, density, protein, lactose, water content, temperature, acidity, MBRT, alcohol test, freezing point.
- **Automatic quality grading** (PASS / BORDERLINE / FAIL) based on configurable thresholds with explanatory warnings.
- Record rejected milk with predefined reasons; linked rejections automatically mark the corresponding collection as `REJECTED`.

### 🚚 Procurement Management (Head Office Only)
- **Suppliers** — company name, contact person, phone, **GSTIN**, email, address, category, status.
- **Purchase Orders** — `PO000001` style codes, line items (name, qty, unit, price), delivery date, and full status workflow:
  `DRAFT → PENDING → APPROVED → ORDERED → RECEIVED → COMPLETED` (plus `CANCELLED`).
- **Goods Receipt (GRN)** — receiving a PO auto-generates a GRN number and **stock-in** to central inventory.
- **Delivery tracking** — dispatch / in-transit / delivered.
- **Vendor payments** — pending / partially paid / paid; a PO auto-completes when fully paid.
- Collection centers, collection routes, and chilling centers.

### 📦 Central Inventory & Branch Allocation
- Head Office owns the **central warehouse**; branches only receive **allocated stock**.
- Stock items with categories, units, **minimum/maximum** stock, **reserved** and **available** quantities.
- **Stock movements ledger** — stock-in, stock-out, allocate (with reference & note).
- **Per-branch allocations** — allocate/deallocate with available-stock validation; automatic **Low Stock** alerts.
- Branch managers cannot create or edit central stock.

### 💸 Expenses & Profit & Loss
- Operational **expenses** registry — category (salary, fuel, maintenance, procurement, electricity, repairs, miscellaneous, feed, etc.), amount, date, description.
- **Profit & Loss report**: revenue (milk) − expenses − procurement spend − **farmer payments** = net profit/loss.
- Dashboard shows Revenue / Expenses / Profit KPIs.

### 📋 Reports (View / CSV / Excel / PDF)
- Report types: **collection, payment, farmer ledger, quality, rejection, branch comparison, expense, P&L, inventory, procurement, vehicle, employee**.
- Date-range, branch, and farmer filters on applicable reports.
- **Export** every report as **CSV**, **Excel (XLSX)**, or **PDF** via `/api/reports/export?format=...`.

### 🚛 Vehicles
- Fleet registry (TANKER, PICKUP, MINI_VAN) with capacity, driver, **insurance number/expiry, fitness, permit, GPS status, mileage**, and service dates.
- **Service history records** — description, cost, odometer, date.
- Service-due and insurance-expiry tracking in the vehicle report.

### 👷 Employees
- Employee registry (operators, accountants, managers, drivers) with salary, role, and branch.
- **Update / delete** employees; **daily attendance** with present/absent/leave summaries.

### 🧾 Live Audit Trail
- Every important action creates an audit log automatically: login/logout, branch create/update, farmer register/verify/reject/block, collection added, quality test added, milk rejected, payment generated/approved/paid, procurement created, inventory stock-in/allocate, vehicle added, employee added, settings updated, **password changed**, exports.
- Each entry captures **user, role, branch code, module, record ID, description, IP address, device (user-agent), and timestamp** — visible to SUPER_ADMIN only, with filters (action, entity, user, date range).

### 🔔 Notifications & Backup
- **Automatic in-app notifications** on key events: farmer registered/verified/rejected, payment approved/paid, milk rejected, purchase order received, low stock, vehicle service due.
- **Backups persisted to disk** (`smart_dairy_backup_<timestamp>.db`), list backups, and **restore** — plus an **automatic daily backup** on app start.
- System settings: dairy name, currency, timezone, language, **SMS provider (MSG91 etc.), email SMTP config**, and notification toggles.

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
| **Exports**  | openpyxl (Excel XLSX), reportlab (PDF) |
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
│   audit.py — live audit-log helper (role/branch/IP)        │
│   notify.py — automatic notification helper                │
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

- **Application factory pattern** (`backend/app.py`) — `create_app()` configures the Flask app, initializes extensions (CORS, SQLAlchemy, JWT), registers blueprints, runs lightweight schema migrations, and creates database tables.
- **REST API + SPA** — the backend is a pure JSON API. A single `index.html` shell hosts every page; the JS router shows/hides page containers based on the URL hash (`#dashboard`, `#farmers`, …).
- **JWT stateless auth** — tokens carry the user identity (id, username, name, role, branch) as a JSON string in the `sub` claim; the client stores it in `localStorage`.
- **Branch isolation** — non-global roles automatically get their queries scoped to their assigned `branch_id` (enforced on farmers, collections, payments, reports, and more).
- **Versioned & immutable records** — collections are immutable receipts; rate changes are versioned instead of overwritten.
- **Audit + notifications everywhere** — key routes write audit logs and auto-create notifications as a side effect of the business action.

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

> The SQLite database file (`smart_dairy.db`) is created automatically on first run with all tables, and an **automatic daily backup** is scheduled on startup.

### Seeding Demo Data

To populate the database with realistic sample data (branches, users, 50+ farmers, collections, payments, quality tests, rejections, suppliers, purchase orders, inventory, employees, vehicles, expenses, notifications, and audit logs):

```bash
python run.py --seed
```

> ⚠️ **Seeding clears all existing data** before inserting sample data.

### Default Login Credentials

After seeding, use these accounts:

| Username    | Password       | Role           | Branch Scope        |
|-------------|----------------|----------------|---------------------|
| `admin`     | `admin123`     | SUPER_ADMIN    | All branches (Head Office) |
| `BR01`      | `9876543210`   | BRANCH_MANAGER | Branch BR01 — Nippani |
| `BR02`      | `9123456780`   | BRANCH_MANAGER | Branch BR02 — Belagavi |
| `BR03`      | `9234567890`   | BRANCH_MANAGER | Branch BR03 — Chikkodi |
| `BR04`      | `9345678901`   | BRANCH_MANAGER | Branch BR04 — Sankeshwar |
| `BR05`      | `9456789012`   | BRANCH_MANAGER | Branch BR05 — Athani |

Branch usernames are the **branch code**; passwords are the branch's **phone number**. Each branch manager can only see their own branch's data.

---

## 📁 Project Structure

```
shree-milk-bank-dairy/
├── run.py                      # Entry point (python run.py [--seed])
├── config.py                   # Environment-based configuration classes
├── requirements.txt            # Python dependencies
├── smart_dairy.db              # SQLite database (auto-created)
├── test_new_features.py        # 79-test feature suite (audit, verification, procurement, P&L, exports, backup, …)
├── test_check.py               # Smoke test — verifies the app serves correctly
├── test_seed.py                # Verifies database seeding
├── backend/
│   ├── app.py                  # Application factory, JWT handlers, blueprint registration, migrations, auto-backup
│   ├── auth.py                 # Password hashing, JWT identity, RBAC decorators
│   ├── models.py               # All SQLAlchemy ORM models (26 tables)
│   ├── pricing.py              # Pricing formula & quality auto-grading engine
│   ├── audit.py                # Live audit-log helper (action/entity/role/branch/IP)
│   ├── notify.py               # Automatic in-app notification helper
│   ├── utils.py                # INR formatting, date helpers, code generators
│   ├── seed.py                 # Database seeder (sample data)
│   └── routes/                 # One blueprint per module
│       ├── auth_routes.py      #   Login/logout/profile/password
│       ├── dashboard_routes.py #   Aggregated dashboard stats + P&L KPIs
│       ├── health_routes.py    #   /api/health
│       ├── branch_routes.py    #   Branch CRUD + reset password
│       ├── farmer_routes.py    #   Farmer CRUD, verify/reject/resubmit, bank verification, CSV export
│       ├── collection_routes.py#   Milk collections
│       ├── payment_routes.py   #   Payment sheets, approval workflow, UTR reference
│       ├── pricing_routes.py   #   Rate master (versioned)
│       ├── quality_routes.py   #   Quality tests with auto-grading
│       ├── rejection_routes.py #   Milk rejections
│       ├── procurement_routes.py # Suppliers, purchase orders, GRN, delivery tracking, vendor payments, centers/routes/chilling
│       ├── inventory_routes.py #   Central inventory, stock movements, branch allocations
│       ├── expense_routes.py   #   Operational expenses (P&L input)
│       ├── employee_routes.py  #   Employees CRUD + attendance
│       ├── vehicle_routes.py   #   Vehicles + service history
│       ├── report_routes.py    #   12 report types + CSV/XLSX/PDF export
│       ├── audit_routes.py     #   Audit logs (SUPER_ADMIN)
│       ├── settings_routes.py  #   System settings, SMS/email config, disk backups & restore
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
└── backups/                    # Created at runtime — disk backups (smart_dairy_backup_*.db)
```

---

## 🗄️ Database Models

All models live in `backend/models.py` and use SQLAlchemy ORM. Tables are created automatically via `db.create_all()` (+ lightweight migrations in `app.py`).

### Core & Operations

| Model              | Table                | Purpose                                                      |
|--------------------|----------------------|--------------------------------------------------------------|
| `User`             | `users`              | System accounts with roles (`SUPER_ADMIN`, `HEAD_OFFICE`, `BRANCH_MANAGER`, `OPERATOR`, `ACCOUNTANT`) |
| `Branch`           | `branches`           | Dairy branches / collection centers |
| `Farmer`           | `farmers`            | Registered milk producers (personal, address, livestock, verification status) |
| `BankDetail`       | `bank_details`       | One-to-one farmer bank/UPI details + verification status |
| `RateMaster`       | `rate_masters`       | Versioned fat/SNF pricing rates per milk type |
| `Collection`       | `collections`        | Daily milk collection receipts (immutable after creation) |
| `Payment`          | `payments`           | Payment sheets linking collections to farmer payouts |
| `QualityTest`      | `quality_tests`      | Lab quality test records with auto-grading results |
| `MilkRejection`    | `milk_rejections`    | Rejected milk records with reasons |

### Procurement & Inventory

| Model                | Table                   | Purpose                                          |
|----------------------|-------------------------|--------------------------------------------------|
| `Supplier`           | `suppliers`             | Vendors with GSTIN, contact, category, status    |
| `PurchaseOrder`      | `purchase_orders`       | PO codes, status workflow, GRN, delivery tracking |
| `PurchaseOrderItem`  | `purchase_order_items`  | Line items (name, qty, unit, price) on a PO      |
| `VendorPayment`      | `vendor_payments`       | Payments to suppliers against POs                 |
| `InventoryItem`      | `inventory_items`       | Central stock items (min/max, reserved, status)  |
| `StockMovement`      | `stock_movements`       | Stock in/out/allocate ledger entries              |
| `InventoryAllocation`| `inventory_allocations` | Per-branch allocation of central stock            |
| `CollectionCenter`   | `collection_centers`    | Procurement collection centers                    |
| `CollectionRoute`    | `collection_routes`     | Milk collection routes                            |
| `ChillingCenter`     | `chilling_centers`      | Chilling/cooling storage centers                  |

### People, Fleet & Governance

| Model                | Table                     | Purpose                                          |
|----------------------|---------------------------|--------------------------------------------------|
| `Employee`           | `employees`               | Staff records (role, salary, branch)             |
| `EmployeeAttendance` | `employee_attendance`     | Daily attendance (present/absent/leave)          |
| `Vehicle`            | `vehicles`                | Fleet registry (insurance, GPS, service dates)   |
| `VehicleServiceRecord` | `vehicle_service_records` | Service/maintenance history for vehicles         |
| `Expense`            | `expenses`                | Operational expenses (P&L input)                 |
| `AuditLog`           | `audit_logs`              | Full audit trail (role, branch code, IP, device) |
| `Notification`       | `notifications`           | In-app notifications per user/global             |

**Code generation conventions** (see `backend/utils.py`):

| Code type | Format | Example |
|-----------|--------|---------|
| Farmer ID | `<branch_code><3-digit serial>` | `BR01001`, `BR01042` |
| Collection receipt | `RC` + 7-digit zero-padded | `RC0000124` |
| Payment code | `PAY` + 7-digit zero-padded | `PAY0000101` |
| Purchase order | `PO` + 6-digit zero-padded | `PO000001` |
| Goods receipt | `GRN` + 6-digit zero-padded | `GRN000001` |

---

## 🔐 Authentication, Roles & Permission Matrix

**Authentication flow:**
1. `POST /api/auth/login` with username + password → returns a **JWT** (`Bearer <token>`) and user object.
2. The client stores the token in `localStorage` (`sd_token`) and sends it via the `Authorization: Bearer <token>` header on every request.
3. `GET /api/auth/me` returns the current session; `POST /api/auth/logout` is client-side (stateless tokens).

**Password handling:** bcrypt hashing (`hash_password` / `check_password` in `backend/auth.py`).

### Final Permission Matrix

| Module | Super Admin (Head Office) | Branch Manager |
|--------|:---:|:---:|
| Dashboard (all branches / own branch) | ✅ | ✅ |
| Branch Management | ✅ | ❌ |
| Farmer Registration | ❌ (branch's job) | ✅ (own branch only) |
| Farmer Verification (approve/reject) | ✅ | ❌ |
| Bank Detail Verification | ✅ | ❌ |
| View All Farmers | ✅ (all branches) | ✅ (own branch only) |
| Edit Farmers | ✅ | ✅ (own branch only) |
| Milk Collection | ✅ (all branches) | ✅ (own branch only) |
| Process Farmer Payments (generate/approve/pay) | ✅ | ❌ |
| Procurement (suppliers, POs, vendor payments) | ✅ | ❌ |
| Central Inventory (stock-in/out/allocate) | ✅ | ❌ (view allocated stock only) |
| Expenses & Profit/Loss | ✅ | ❌ |
| Vehicle Management | ✅ | ❌ |
| Employee Management | ✅ (all) | ✅ (own branch only) |
| Reports | ✅ (all branches) | ✅ (own branch only) |
| Audit Logs | ✅ | ❌ |
| Settings & Backups | ✅ | ❌ |
| Rate Engine | ✅ | ❌ |

**RBAC decorators** (`backend/auth.py`):

| Capability | Allowed Roles |
|------------|---------------|
| Record collections (`can_collect`) | SUPER_ADMIN, HEAD_OFFICE, BRANCH_MANAGER, OPERATOR |
| Payments & approvals (`can_pay`) | **SUPER_ADMIN only** (per architecture spec) |
| Manage rates (`can_manage_rates`) | SUPER_ADMIN, HEAD_OFFICE |
| Global / cross-branch access (`is_global_role`) | SUPER_ADMIN, HEAD_OFFICE |
| Branch CRUD / procurement / central inventory / expenses | SUPER_ADMIN, HEAD_OFFICE |
| Farmer verification & bank verification | SUPER_ADMIN, HEAD_OFFICE |
| Farmer registration & resubmission | BRANCH_MANAGER |
| Audit logs / settings / backups | SUPER_ADMIN (settings PATCH: SUPER_ADMIN + HEAD_OFFICE) |

**Branch isolation:** roles without global access automatically see only data belonging to their assigned `branch_id` (enforced on farmer list/detail/edit, collections, payments, inventory, employees, and reports). Cross-branch reads/writes return **403**.

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
| POST | `/api/auth/logout` | Logout (audit-logged) | Any |
| GET | `/api/auth/me` | Current user session | Any |
| PATCH | `/api/auth/profile` | Update own profile | Any |
| POST | `/api/auth/change-password` | Change own password (audit-logged) | Any |
| POST | `/api/auth/forgot-password` | Request password reset | Public |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | KPIs (incl. `profit30d`, `monthlyCollection`, `rejectedPct`, `lowStockCount`), trends, branch performance, today's entries (`?days=14\|30`) |

### Branches
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/branches` | List active branches | Public |
| POST | `/api/branches` | Create branch (audit-logged) | SUPER_ADMIN, HEAD_OFFICE |
| PATCH | `/api/branches/<id>` | Update branch (audit-logged) | SUPER_ADMIN, HEAD_OFFICE |
| POST | `/api/branches/<id>/reset-password` | Reset branch password | SUPER_ADMIN, HEAD_OFFICE |
| DELETE | `/api/branches/<id>` | Soft-delete branch | SUPER_ADMIN, HEAD_OFFICE |

### Farmers
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/farmers` | List (paged; filters: `q` [ID/name/mobile/**Aadhaar**/village], `branchId`, `milk_type`, `status`) | Branch-scoped |
| GET | `/api/farmers/stats` | Farmer statistics by type/status | Branch-scoped |
| POST | `/api/farmers` | Register farmer → `PENDING_VERIFICATION` (auto-generates `BR01xxx` code) | BRANCH_MANAGER only |
| GET | `/api/farmers/<code>` | Farmer detail + stats + recent collections | Branch-scoped |
| PATCH | `/api/farmers/<code>` | Update farmer (incl. bank details); status changes Head Office only | Branch-scoped |
| POST | `/api/farmers/<code>/verify` | Approve/reject verification (`{action: approve\|reject, reason}`) | SUPER_ADMIN, HEAD_OFFICE |
| POST | `/api/farmers/<code>/resubmit` | Re-submit a REJECTED farmer | BRANCH_MANAGER (own branch) |
| POST | `/api/farmers/<code>/verify-bank` | Verify/reject bank details | SUPER_ADMIN, HEAD_OFFICE |
| GET | `/api/farmers/export` | Export farmers as CSV (branch-scoped) | Any |

### Collections
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/collections` | List (filters: `date`, `shift`, `farmerId`, `branchId`) |
| POST | `/api/collections` | Record collection (roles: collect) — computes price, returns receipt |

### Payments
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/payments` | List + summary (paid/pending/rate) | Any |
| POST | `/api/payments` | Generate payment sheets from unpaid collections (**ACTIVE farmers only**) | SUPER_ADMIN (`can_pay`) |
| PATCH | `/api/payments/<id>` | Set status to `APPROVED` or `PAID` (PAID sets UTR reference) | SUPER_ADMIN (`can_pay`) |

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

### Procurement (all write ops: SUPER_ADMIN, HEAD_OFFICE)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET / POST | `/api/procurement/centers` | List / create collection centers |
| GET / POST | `/api/procurement/routes` | List / create collection routes |
| GET / POST | `/api/procurement/chilling` | List / create chilling centers |
| GET / POST | `/api/procurement/suppliers` | List / create suppliers (GSTIN supported) |
| PATCH / DELETE | `/api/procurement/suppliers/<id>` | Update / delete supplier |
| GET | `/api/procurement/purchase-orders` | List POs (filters: status, supplierId, from, to) |
| POST | `/api/procurement/purchase-orders` | Create PO (DRAFT) with line items |
| GET | `/api/procurement/purchase-orders/<id>` | PO detail |
| PATCH | `/api/procurement/purchase-orders/<id>` | Advance status (`DRAFT→PENDING→APPROVED→ORDERED→RECEIVED→COMPLETED`; RECEIVED generates **GRN + stock-in**); also `deliveryStatus` (`DISPATCHED`/`IN_TRANSIT`/`DELIVERED`) |
| GET | `/api/procurement/vendor-payments` | List vendor payments |
| POST | `/api/procurement/vendor-payments` | Record vendor payment (auto-completes fully-paid PO) |

### Inventory (write ops: SUPER_ADMIN, HEAD_OFFICE)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/inventory` | Central stock list (incl. available/reserved) |
| POST | `/api/inventory` | Create stock item |
| PATCH / DELETE | `/api/inventory/<id>` | Update / delete item |
| POST | `/api/inventory/<id>/movement` | Stock IN / OUT / ALLOCATE (`{type, quantity, branchId?, note?}`) |
| GET | `/api/inventory/movements` | Global movement ledger |
| GET | `/api/inventory/<id>/movements` | Per-item movement history |
| GET | `/api/inventory/<id>/allocations` | Per-branch allocations for an item |
| POST | `/api/inventory/<id>/allocate` | Allocate stock to a branch (`{branchId, quantity}`) — validated against available |
| POST | `/api/inventory/<id>/deallocate` | Return allocated stock (`{branchId, quantity}`) |

### Expenses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/expenses` | List + summary by category (`from`, `to`, `branchId` filters) |
| POST | `/api/expenses` | Record expense (category, amount, date, description) |
| PATCH / DELETE | `/api/expenses/<id>` | Update / delete expense (SUPER_ADMIN, HEAD_OFFICE) |

### Employees
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | List (branch-scoped) |
| POST | `/api/employees` | Create employee |
| PATCH / DELETE | `/api/employees/<id>` | Update / delete employee |
| GET | `/api/employees/attendance` | Attendance overview (date filter) |
| GET | `/api/employees/<id>/attendance` | Per-employee attendance summary |
| POST | `/api/employees/attendance` | Mark attendance (`{employeeId, status: PRESENT\|ABSENT\|LEAVE, date?}`) |

### Vehicles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles` | List (filters: status, type) |
| POST | `/api/vehicles` | Create vehicle (insurance, GPS, service dates) |
| PATCH / DELETE | `/api/vehicles/<id>` | Update / delete vehicle |
| GET | `/api/vehicles/<id>/service` | Service history list |
| POST | `/api/vehicles/<id>/service` | Add service record (description, cost, odometer, date) |

### Reports & Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports?type=<type>&from=&to=&branchId=&farmerId=` | Report engine — types: `collection`, `payment`, `farmer`, `quality`, `rejection`, `branch`, `expense`, `pnl`, `inventory`, `procurement`, `vehicle`, `employee` |
| GET | `/api/reports/export?type=<type>&from=&to=&format=csv\|xlsx\|pdf` | Export any report as **CSV / Excel / PDF** |

### Audit, Settings, Notifications
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/audit` | Audit log list (filters: action, entity, userId, from, to) | SUPER_ADMIN |
| GET / PATCH | `/api/settings` | Get / update settings (incl. SMS provider, email SMTP) | PATCH: SUPER_ADMIN, HEAD_OFFICE |
| POST | `/api/settings/backup` | Create a backup (persisted to disk) | SUPER_ADMIN |
| GET | `/api/settings/backup` | Download latest backup | SUPER_ADMIN |
| GET | `/api/settings/backups` | List all backups | SUPER_ADMIN |
| POST | `/api/settings/restore/<filename>` | Restore a backup | SUPER_ADMIN |
| POST | `/api/settings/regenerate-key` | Regenerate API key | SUPER_ADMIN |
| GET / PATCH / DELETE | `/api/notifications` | List / mark-read / delete notifications | Any |

---

## 🖥️ Frontend Architecture

The frontend is a **single-page application without any framework** — all views live inside `templates/index.html` as `<div class="page-container">` blocks, and vanilla JS modules control behavior.

- **Routing** (`static/js/router.js`): hash-based routing. `Router.navigate('farmers')` switches the visible page container and updates `window.location.hash` (`#farmers`). The router also listens to `hashchange` and role-gates pages (branch managers are blocked from branches/procurement/vehicles/pricing/audit/settings/expenses).
- **API client** (`static/js/api.js`): a single `API` object wrapping `fetch()` — automatically attaches the JWT `Authorization` header, centralizes 401 handling (clears session, redirects to login), and exposes typed helpers (`API.getFarmers(...)`, `API.verifyFarmer(...)`, `API.createPurchaseOrder(...)`, …).
- **State** (`static/js/storage.js`): localStorage wrapper. Keys: `sd_token`, `sd_user`, `sd_theme`, `sd_sidebar`.
- **Page controllers**: one JS file per module (`dashboard.js`, `farmers.js`, `collection.js`, `payments.js`, `pricing.js`, `quality.js`, `rejections.js`, `branches.js`, `procurement.js`, `inventory.js`, `expenses.js`, `employees.js`, `vehicles.js`, `reports.js`, `audit.js`, `settings.js`, `notifications.js`, `profile.js`, `farmer-form.js`, `farmer-profile.js`).
- **Shared components**: `table.js` (rendering, sorting, pagination, CSV export, print), `chart.js` (Chart.js wrapper), `modal.js` (modal dialogs), `form-validation.js`, `utils.js`.
- **Design system** (`static/css/`): CSS custom properties in `variables.css` drive theming (light/dark via `data-theme` attribute on `<html>`), `style.css` provides base layout, `responsive.css` handles mobile, and per-module stylesheets cover each page.
- **CDN dependencies**: Chart.js 4.4.7, Lucide icons, Google Fonts (Inter + Playfair Display).

---

## 🧪 Testing

Three verification scripts are included:

```bash
# 1. Full feature suite (79 assertions) — audit logging, farmer verification &
#    bank verification, procurement (PO/GRN/vendor payments), inventory
#    movements & allocation, expenses/P&L, CSV/XLSX/PDF exports, vehicle service
#    records, employee attendance, auto-notifications, backups, dashboard KPIs,
#    cross-branch isolation, and role gating.
#    ⚠️ WARNING: Deletes smart_dairy.db first, then re-seeds it
python test_new_features.py

# 2. Smoke test — verifies the Flask app boots and serves the SPA correctly
python test_check.py

# 3. Seed test — verifies database seeding
#    ⚠️ WARNING: Deletes smart_dairy.db first, then re-seeds it
python test_seed.py
```

Expected result: `=== RESULT: 79 passed, 0 failed ===` for the feature suite.

---

## 🔒 Security Notes

> **For production deployment, you MUST do the following:**

1. **Change the secrets** — set strong random values for `SECRET_KEY` and `JWT_SECRET_KEY` via environment variables (never use the hard-coded development defaults).
2. **Set `FLASK_ENV=production`** — this disables Flask debug mode (which otherwise exposes the interactive debugger).
3. **Run behind a production WSGI server** — use Gunicorn / Waitress / uWSGI instead of the built-in development server.
4. **Use a production-grade database** — the default SQLite setup is fine for a single-instance deployment; switch `DATABASE_URL` to PostgreSQL or MySQL for multi-instance/high-availability setups.
5. **Enable HTTPS** — all traffic should be TLS-encrypted, since authentication uses Bearer tokens.
6. **Password reset** — `POST /api/auth/forgot-password` currently returns the reset email in the response (dev-mode behavior). Wire it to a real email-sending service (e.g., SMTP, SendGrid, Resend) before production.
7. **Remove the dev login bypass** — `backend/routes/auth_routes.py` contains a temporary development bypass (`admin` / `admin123` always authenticates while `DEV_LOGIN_ENABLED` is on). Disable it before any production release.
8. **SMS/Email sending** — the settings store SMTP/MSG91 configuration; wire up actual delivery (e.g., via SMTP or MSG91 API) before relying on automatic notifications externally.
9. **Audit & backups** — backups are stored on the local filesystem (`backups/`); for production, ship them to durable object storage and enforce a retention policy.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Activate your virtual environment and run `pip install -r requirements.txt` |
| Port 5000 already in use | Change the port in `run.py` (`app.run(debug=True, port=5000)`) |
| Login fails after fresh install | The database has no users — run `python run.py --seed` to create demo accounts |
| Database is missing / tables not created | Tables are auto-created on app start; verify `smart_dairy.db` is writable |
| `Invalid username or password` | Check the username is exact and use the seeded passwords (`admin123`, or a branch code with the branch phone number) |
| Seed script errors | `--seed` clears the DB first — back up `smart_dairy.db` if you have real data |
| Collections show wrong price | Verify the active `RateMaster` version for the farmer's milk type in **Rate Engine** |
| Branch user sees no data | Confirm the user is assigned to a branch and that branch has data (see **Branches**) |
| JWT expiry errors (401) | Tokens last 24h by default — log in again to refresh |
| New farmer can't get paid | The farmer must be **verified (ACTIVE)** by Head Office first — payments only generate for ACTIVE farmers |
| Cross-branch access denied (403) | Branch managers are restricted to their own branch — this is by design |
| Database locked / `database is locked` errors | A server or test process may still be holding the SQLite file — stop it and retry |

---

*Built with ❤️ for the dairy industry — Shree Milk Bank Dairy.*
