"""
Smart Dairy ERP — Render Capture
================================
Renders `/` through the real Flask app (test client) and writes the raw
response bytes to a file. Used to verify the SPA shell split:

    python scripts/verify_index_split.py before.html   # run pre-split
    python scripts/verify_index_split.py after.html    # run post-split
    diff before.html after.html                       # expect: identical

Usage:
    python scripts/verify_index_split.py [output_path]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app import create_app  # noqa: E402


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'index_rendered.html')
    app = create_app()
    with app.test_client() as client:
        resp = client.get('/')
        if resp.status_code != 200:
            print(f'[ERROR] GET / returned {resp.status_code}', file=sys.stderr)
            sys.exit(1)
        with open(out, 'wb') as f:
            f.write(resp.data)
    print(f'[OK] rendered GET / ({len(resp.data)} bytes) -> {out}')


if __name__ == '__main__':
    main()
