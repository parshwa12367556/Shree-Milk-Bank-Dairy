import os
import sys
import ast
import re
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

bugs = []

def report(category, severity, file_path, line_no, title, details):
    bugs.append({
        "category": category,
        "severity": severity,
        "file": os.path.relpath(file_path, BASE_DIR) if (file_path and os.path.isabs(file_path)) else (file_path or "N/A"),
        "line": line_no,
        "title": title,
        "details": details
    })

print("=" * 60)
print(" STARTING DEEP COMPREHENSIVE BUG SCAN OF SHREE MILK BANK DAIRY")
print("=" * 60)

# -------------------------------------------------------------
# 1. SCAN ALL FLASK ENDPOINTS FOR AUTH & RBAC DECORATORS
# -------------------------------------------------------------
# This project protects its API with flask-jwt-extended + custom RBAC
# decorators (@jwt_required(), @role_required(...), @can_pay(), ...). The
# scan below reads the actual AST of each route module, so it understands
# the REAL security architecture — it never mistakes the absence of
# @login_required for an unprotected endpoint.
print("\n[STEP 1] Auditing Flask Routes for Security & Role Scoping...")

try:
    from backend.app import create_app
    from flask import current_app
    app = create_app('testing')

    # Decorator names that this project treats as authentication / RBAC.
    AUTH_DECORATORS = {
        'jwt_required', 'login_required', 'token_required',
        'role_required', 'can_pay', 'can_collect', 'can_manage_rates',
        'is_global_role', 'roles_required', 'require_role',
    }

    # Functions whose bodies also perform their own auth (public helpers).
    PUBLIC_API_PREFIXES = (
        '/api/auth/login',
        '/api/auth/forgot-password',
        '/api/auth/reset-password',
        '/api/health',
        '/api/health/ping',
        '/api/pages/manifest',
        # Intentionally public: the login screen lists active branches so the
        # user can pick one — it only ever returns branch names/ids, never
        # operational data. (Documented as Public in the README API table.)
        '/api/branches',
    )

    def _parse_module(file_path):
        """Return {func_name: (decorator_names, def_line)} from a Python file."""
        result = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
        except (OSError, SyntaxError):
            return result
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names = set()
                for d in node.decorator_list:
                    fn = d.func if isinstance(d, ast.Call) else d
                    if isinstance(fn, ast.Attribute):
                        names.add(fn.attr)
                    elif isinstance(fn, ast.Name):
                        names.add(fn.id)
                result[node.name] = (names, node.lineno)
        return result

    with app.app_context():
        for rule in app.url_map.iter_rules():
            endpoint = rule.endpoint
            view_func = app.view_functions.get(endpoint)
            if not view_func:
                continue

            methods = [m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
            rule_str = rule.rule

            # Locate the module + the route function's AST decorations.
            try:
                func_file = sys.modules[view_func.__module__].__file__
            except Exception:
                func_file = None
            func_name = getattr(view_func, '__name__', '')

            decorators, def_line = set(), 0
            if func_file and os.path.exists(func_file):
                module_map = _parse_module(func_file)
                if func_name in module_map:
                    decorators, def_line = module_map[func_name]

            # Check public vs protected API endpoints
            if rule_str.startswith('/api/'):
                if not any(rule_str.startswith(p) for p in PUBLIC_API_PREFIXES):
                    has_auth = bool(decorators & AUTH_DECORATORS)
                    if not has_auth:
                        report(
                            "Security / RBAC", "HIGH", func_file or "Unknown", def_line,
                            f"Unprotected API Endpoint: {methods} {rule_str}",
                            f"Endpoint '{endpoint}' starts with /api/ and has NO authentication "
                            f"decorator (@jwt_required / @role_required / @can_pay ...). "
                            f"Detected decorators: {sorted(decorators) or 'none'}."
                        )

except Exception as e:
    report("Flask Audit", "HIGH", "backend/app.py", 0, "Flask App Inspection Error", str(e))

# -------------------------------------------------------------
# 2. SCAN PYTHON BUSINESS LOGIC & UTILITIES
# -------------------------------------------------------------
print("\n[STEP 2] Auditing Backend Business Logic, Models & Calculation Engine...")

py_files = []
for root, dirs, files in os.walk(BASE_DIR):
    if any(p in root for p in [".git", "__pycache__", ".venv", "node_modules", "scripts/archive"]):
        continue
    for file in files:
        if file.endswith(".py"):
            py_files.append(os.path.join(root, file))

for py_path in py_files:
    try:
        with open(py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.splitlines()
    except Exception:
        continue

    for idx, line in enumerate(lines, 1):
        # 2a. Check for potential division by zero without zero check
        if "/" in line and not line.strip().startswith("#"):
            # looking for pattern val / (x) or val / x where x could be 0
            if re.search(r'/\s*([a-zA-Z_][a-zA-Z0-9_]*)\b', line):
                var_name = re.search(r'/\s*([a-zA-Z_][a-zA-Z0-9_]*)\b', line).group(1)
                if var_name in ('total_days', 'days', 'count', 'qty', 'quantity', 'liters', 'total_liters', 'fat', 'snf', 'lrr'):
                    # Check if preceding 5 lines check for 0
                    context = "\n".join(lines[max(0, idx-6):idx])
                    if f"if {var_name}" not in context and f"if not {var_name}" not in context and f"{var_name} > 0" not in context and f"{var_name} !=" not in context and f"or 1" not in line and f"max(" not in line:
                        report(
                            "Unhandled Exception Risk", "MEDIUM", py_path, idx,
                            f"Potential ZeroDivisionError on variable '{var_name}'",
                            f"Line calculates division by '{var_name}' without explicit zero verification: `{line.strip()}`"
                        )
                        
        # 2b. Check for float precision issues on currency/amount calculations
        if re.search(r'amount\s*=\s*.*\*', line) or re.search(r'total_amount\s*=\s*.*\*', line):
            if "round(" not in line and "Decimal" not in line:
                report(
                    "Financial / Precision", "LOW", py_path, idx,
                    "Unrounded Currency Calculation",
                    f"Financial calculation amount may introduce floating point precision drift: `{line.strip()}`"
                )

        # 2c. Check for missing commit/rollback in DB mutation routes or except blocks
        if "db.session.commit()" in line:
            # check if there is except block nearby with rollback
            context_around = "\n".join(lines[max(0, idx-10):min(len(lines), idx+15)])
            if "except" in context_around and "db.session.rollback()" not in context_around:
                report(
                    "Database Transaction Risk", "MEDIUM", py_path, idx,
                    "Missing db.session.rollback() in Exception Handler",
                    f"db.session.commit() is used but exception handler in scope does not call db.session.rollback()."
                )

# -------------------------------------------------------------
# 3. SCAN JAVASCRIPT FILES & FRONTEND APP INTEGRATION
# -------------------------------------------------------------
print("\n[STEP 3] Auditing JavaScript Frontend Scripts...")

js_files = []
static_js_dir = os.path.join(BASE_DIR, 'static', 'js')
for root, dirs, files in os.walk(static_js_dir):
    for file in files:
        if file.endswith('.js'):
            js_files.append(os.path.join(root, file))

for js_path in js_files:
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.splitlines()

    # Find API endpoints referenced in JS fetches
    fetch_matches = re.findall(r'fetch\s*\(\s*[`\'"](/api/[^`\'"?]+)', content)
    for endpoint_url in set(fetch_matches):
        # Normalize route parameter patterns like /api/farmers/${id} -> /api/farmers/<id>
        normalized = re.sub(r'\$\{[^}]+\}', '<param>', endpoint_url)
        normalized = re.sub(r'/[0-9]+', '/<param>', normalized)
        
        # Verify if Flask app has matching route rule
        matched_rule = False
        with app.app_context():
            for rule in app.url_map.iter_rules():
                rule_regex = re.sub(r'<[^>]+>', '[^/]+', rule.rule)
                if re.fullmatch(rule_regex, endpoint_url.split('?')[0]):
                    matched_rule = True
                    break
        if not matched_rule:
            report(
                "Frontend / API Mismatch", "HIGH", js_path, 0,
                f"JS calls non-existent Flask API route: {endpoint_url}",
                f"JavaScript file calls `{endpoint_url}`, but no matching route was found in Flask app.url_map."
            )

    # Inspect for common DOM / JS bugs
    for idx, line in enumerate(lines, 1):
        # 3a. Check for missing error handling in fetch promises
        if "fetch(" in line and "await" not in line and ".catch" not in line:
            context = "\n".join(lines[idx:min(len(lines), idx+5)])
            if ".catch" not in context:
                report(
                    "Frontend Robustness", "LOW", js_path, idx,
                    "Unhandled Promise Rejection in fetch()",
                    f"Asynchronous fetch call lacks .catch() handler: `{line.strip()}`"
                )
                
        # 3b. Check for innerHTML XSS injection with raw variables
        if ".innerHTML =" in line or ".innerHTML+=" in line:
            if re.search(r'\.innerHTML\s*\+?=\s*[`\'"].*\$\{', line):
                if "escapeHtml" not in line and "sanitize" not in line:
                    report(
                        "Security / XSS Risk", "MEDIUM", js_path, idx,
                        "Potential DOM XSS via innerHTML",
                        f"Direct interpolation into innerHTML without sanitization/escaping: `{line.strip()}`"
                    )

# -------------------------------------------------------------
# 4. SCAN HTML TEMPLATES & ASSETS
# -------------------------------------------------------------
print("\n[STEP 4] Auditing HTML Templates & Assets...")

template_dir = os.path.join(BASE_DIR, 'templates')
html_files = []
for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

for html_path in html_files:
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.splitlines()

    for idx, line in enumerate(lines, 1):
        # Check for static asset links in templates (script src / link href)
        src_matches = re.findall(r'(?:src|href)=["\']/static/([^"\']+)["\']', line)
        for asset_rel in src_matches:
            # Strip query params like ?v=1.0
            clean_asset = asset_rel.split('?')[0]
            asset_full = os.path.join(BASE_DIR, 'static', clean_asset.replace('/', os.sep))
            if not os.path.exists(asset_full):
                report(
                    "Broken Asset Link", "MEDIUM", html_path, idx,
                    f"Referenced static asset file does not exist: {clean_asset}",
                    f"Template includes `/static/{clean_asset}`, but file was not found on disk."
                )

        # Check for unclosed Jinja tags or syntax mistakes
        jinja_opens = len(re.findall(r'\{\%', line))
        jinja_closes = len(re.findall(r'\%\}', line))
        if jinja_opens != jinja_closes:
            report(
                "Jinja Template Syntax", "HIGH", html_path, idx,
                "Mismatched Jinja block delimiters '{%' and '%}'",
                f"Line has unequal Jinja tag delimiters: `{line.strip()}`"
            )

# -------------------------------------------------------------
# 5. RUN EXISTING TEST SUITES AND RECORD ANY FAILURES
# -------------------------------------------------------------
print("\n[STEP 5] Auditing Test Suite Execution...")

import subprocess

test_files_to_run = [
    "test_login_system.py",
    "test_security_rbac.py",
    "test_farmer_portal.py",
    "test_email_notifications.py",
    "test_new_features.py",
    "test_seed.py",
    "scripts/validate_templates.py"
]

for tf in test_files_to_run:
    tf_path = os.path.join(BASE_DIR, tf)
    if os.path.exists(tf_path):
        res = subprocess.run([sys.executable, tf_path], capture_output=True, text=True, cwd=BASE_DIR)
        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            # Extract last line or error summary
            err_summary = err_msg.splitlines()[-1] if err_msg else "Unknown failure"
            report(
                "Automated Test Failure", "HIGH", tf, 0,
                f"Test suite '{tf}' failed during execution",
                f"Exit code {res.returncode}. Output:\n{err_msg[-400:]}"
            )

print("\n" + "=" * 60)
print(f" SCAN COMPLETE! TOTAL BUGS / ISSUES IDENTIFIED: {len(bugs)}")
print("=" * 60)

output_file = os.path.join(BASE_DIR, 'scripts', 'deep_scan_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(bugs, f, indent=2)

for b in bugs:
    print(f"[{b['severity']}] ({b['category']}) {b['file']}:{b['line']} - {b['title']}")
    print(f"  Details: {b['details'][:150]}...")
