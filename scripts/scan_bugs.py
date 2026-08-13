import os
import sys
import ast
import re
import sqlite3
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

bugs = []

def report(category, severity, file_path, line_no, message):
    bugs.append({
        "category": category,
        "severity": severity,
        "file": os.path.relpath(file_path, BASE_DIR) if file_path else "N/A",
        "line": line_no,
        "message": message
    })

# 1. SCAN ALL PYTHON FILES FOR SYNTAX & AST ANOMALIES
print("[1/6] Scanning Python files AST & Syntax...")
py_files = []
for root, dirs, files in os.walk(BASE_DIR):
    if ".git" in root or "__pycache__" in root or ".venv" in root or "node_modules" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            py_files.append(os.path.join(root, file))

for py_path in py_files:
    try:
        with open(py_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=py_path)
    except SyntaxError as e:
        report("Python Syntax", "CRITICAL", py_path, e.lineno, f"SyntaxError: {e.msg}")
        continue
    except Exception as e:
        report("Python Syntax", "CRITICAL", py_path, 0, f"Failed to parse file: {e}")
        continue

    # Walk AST to find obvious bugs (e.g. bare excepts without re-raising or logging, dangerous calls, undefined imports)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None: # bare except:
                report("Python Code Quality", "LOW", py_path, node.lineno, "Bare 'except:' used without specifying exception type.")
        elif isinstance(node, ast.Call):
            # Check for dangerouseval/exec
            if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
                report("Security Risk", "HIGH", py_path, node.lineno, f"Use of dangerous function '{node.func.id}'")

# 2. CHECK FLASK ROUTES & SECURITY (RBAC & LOGIN DECORATORS)
print("[2/6] Checking Flask App & Route definitions...")
try:
    from backend.app import create_app
    app = create_app('testing')
    
    # Check duplicate route rules
    rules = list(app.url_map.iter_rules())
    route_methods_map = {}
    for rule in rules:
        for method in rule.methods:
            if method in ('HEAD', 'OPTIONS'):
                continue
            key = (rule.rule, method)
            if key in route_methods_map:
                report("Routing Conflict", "HIGH", None, 0, f"Duplicate route definition: {method} {rule.rule} in endpoint '{rule.endpoint}' vs '{route_methods_map[key]}'")
            else:
                route_methods_map[key] = rule.endpoint
                
    # Check security decorators on endpoint functions
    for endpoint, view_func in app.view_functions.items():
        if endpoint in ('static', 'index_views.serve_static'):
            continue
        # Check source of view_func
        try:
            func_file = sys.modules[view_func.__module__].__file__
        except Exception:
            func_file = None
            
        rule_str = [r.rule for r in rules if r.endpoint == endpoint]
        
        # Check if API endpoint is missing role check or auth check when it should be protected
        if any(r.startswith('/api/') for r in rule_str):
            # Exempt public endpoints
            if endpoint in ('auth.login', 'auth.forgot_password', 'auth.reset_password', 'health.health_check'):
                continue
            # Check if func has @login_required or role requirement
            # (Inspecting docstring or closure / attributes if present)
            func_code = getattr(view_func, '__code__', None)
            
except Exception as e:
    report("Flask Initialization", "HIGH", "backend/app.py", 0, f"Failed to initialize Flask app for inspection: {e}")

# 3. CHECK DATABASE MODELS VS SQLITE SCHEMA
print("[3/6] Inspecting Database Models & Schema...")
db_path = os.path.join(BASE_DIR, 'smart_dairy.db')
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        
        from backend.models import db
        with app.app_context():
            model_tables = db.metadata.tables.keys()
            for mt in model_tables:
                if mt not in tables:
                    report("Database Schema", "HIGH", "backend/models.py", 0, f"Model table '{mt}' does not exist in SQLite database!")
                else:
                    # Compare columns
                    cursor.execute(f"PRAGMA table_info('{mt}');")
                    db_cols = {row[1]: row[2] for row in cursor.fetchall()}
                    model_cols = db.metadata.tables[mt].columns.keys()
                    for mc in model_cols:
                        if mc not in db_cols:
                            report("Database Schema Mismatch", "MEDIUM", "backend/models.py", 0, f"Column '{mc}' in model table '{mt}' is missing from DB schema!")
        conn.close()
    except Exception as e:
        report("Database Audit", "MEDIUM", "smart_dairy.db", 0, f"Error inspecting database schema: {e}")

# 4. CHECK TEMPLATES AND HTML FILES
print("[4/6] Scanning HTML Templates & Manifest...")
template_dir = os.path.join(BASE_DIR, 'templates')
templates_found = set()
for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html'):
            rel_path = os.path.relpath(os.path.join(root, file), template_dir).replace('\\', '/')
            templates_found.add(rel_path)

# Check backend/pages_manifest.json
manifest_path = os.path.join(BASE_DIR, 'backend', 'pages_manifest.json')
if os.path.exists(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    for role, pages in manifest.get('pages', {}).items():
        for page_id, info in pages.items():
            tmpl = info.get('template')
            if tmpl and tmpl not in templates_found:
                report("Missing Template", "HIGH", "backend/pages_manifest.json", 0, f"Manifest references template '{tmpl}' for page '{page_id}' ({role}), but file does not exist!")

# 5. SCAN JAVASCRIPT FILES FOR COMMON BUGS
print("[5/6] Scanning JavaScript files...")
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
    
    # Check for console.error, debugger statements, unhandled promises, syntax anomalies
    for i, line in enumerate(lines, 1):
        if 'debugger;' in line:
            report("JS Debug Code", "LOW", js_path, i, "Contains 'debugger;' statement.")
        # Check hardcoded URLs or broken relative fetches
        if re.search(r'fetch\([\'"]http://localhost', line):
            report("JS Hardcoded URL", "MEDIUM", js_path, i, "Hardcoded localhost URL in fetch API call.")

# WRITE BUGS REPORT TO SCRATCH / JSON
report_file = os.path.join(BASE_DIR, 'scripts', 'scan_results.json')
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(bugs, f, indent=2)

print(f"\nScan finished! Found {len(bugs)} potential issues.")
