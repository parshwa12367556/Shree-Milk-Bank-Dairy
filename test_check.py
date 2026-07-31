"""Quick test to verify Flask app serves the login page correctly"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from backend.app import create_app
app = create_app()
print("Server OK")
with app.test_client() as c:
    r = c.get('/')
    html = r.data.decode('utf-8')
    print(f"Status: {r.status_code}")
    print(f"Content length: {len(html)} bytes")
    checks = [
        ("login-page", "login-page" in html),
        ("login-form", "login-form" in html),
        ("login-username", "login-username" in html),
        ("login.css", "login.css" in html),
        ("style.css", "style.css" in html),
        ("variables.css", "variables.css" in html),
        ("app.js", "app.js" in html),
        ("api.js", "api.js" in html),
        ("auth.js", "auth.js" in html),
        ("chart.js", "chart.js" in html),
        ("lucide", "unpkg.com/lucide" in html),
        ("chart.js CDN", "chart.js" in html),
    ]
    for name, ok in checks:
        print(f"  {'OK' if ok else 'MISSING'}: {name}")
    print("DONE")
