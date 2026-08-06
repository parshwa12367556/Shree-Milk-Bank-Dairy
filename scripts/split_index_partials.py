"""
Smart Dairy ERP — Split SPA Shell into Partials
===============================================
One-time migration tool. The ~3000-line `templates/index.html` SPA shell is
split into focused Jinja2 partials under `templates/index/`:

    templates/
      index.html                       # thin shell: {% include %}s the partials
      index/
        _head.html                     # <head>: fonts, CDN libs, CSS links
        _login.html                    # login page
        _modal_change_password.html    # forced password-change modal
        _modal_forgot_password.html    # forgot-password OTP modal
        _layout_open.html              # .app-layout open + mobile overlay
        _sidebar.html                  # sidebar nav
        _wrapper_open.html             # .main-wrapper open
        _navbar.html                   # top navbar
        _main_open.html                # .main-content open
        _main_close.html               # </main> + footer + layout closes
        _modals_extra.html             # quality-test & payment modals
        _scripts.html                  # script tags + inline helpers
        pages/
          _dashboard.html              # one file per page container
          _collection.html
          ...

Safety guarantees:
  * Refuses to run if index.html already contains '{% include' (already split).
  * Every structural marker must be found exactly once, in file order.
  * Partials are extracted VERBATIM (no content rewriting), so the rendered
    page is byte-for-byte identical to the original (verify with
    scripts/verify_index_split.py + diff).

Run:
    python scripts/split_index_partials.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'templates', 'index.html')
OUT_DIR = os.path.join(ROOT, 'templates', 'index')
PAGES_DIR = os.path.join(OUT_DIR, 'pages')

SHELL = '__shell__'  # region stays in index.html (e.g. <body>, </html>)


def fatal(msg):
    print(f'[FATAL] {msg}', file=sys.stderr)
    sys.exit(1)


def main():
    if not os.path.exists(SRC):
        fatal(f'missing {SRC}')
    with open(SRC, 'r', encoding='utf-8-sig') as f:
        text = f.read()
    if '{% include' in text:
        fatal('index.html already contains Jinja includes — refusing to re-split.')

    lines = text.split('\n')
    n = len(lines)

    def find_lines(pred, what):
        hits = [i for i, ln in enumerate(lines) if pred(ln)]
        if len(hits) != 1:
            fatal(f'marker {what!r} found {len(hits)} times (expected 1): {[h + 1 for h in hits]}')
        return hits[0]

    def find_first(pred, what):
        for i, ln in enumerate(lines):
            if pred(ln):
                return i
        fatal(f'marker {what!r} not found')

    def stripped_eq(value):
        return lambda ln: ln.strip() == value

    def contains(value):
        return lambda ln: value in ln

    def comment_start(line_idx, what):
        """Walk back to the opening `<!--` line of a multi-line comment block."""
        j = line_idx
        while j >= 0 and not lines[j].strip().startswith('<!--'):
            j -= 1
        if j < 0:
            fatal(f'no comment opener found for marker {what!r}')
        return j

    # ── Locate structural markers ─────────────────────────────────
    head_start = find_lines(stripped_eq('<head>'), '<head>')
    head_end = find_lines(stripped_eq('</head>'), '</head>')
    body_end = find_lines(stripped_eq('</body>'), '</body>')
    main_close = find_lines(stripped_eq('</main>'), '</main>')

    login_start = comment_start(
        find_lines(contains('LOGIN PAGE (shown when not authenticated)'), 'LOGIN PAGE'), 'LOGIN PAGE')
    change_pw_start = comment_start(
        find_lines(contains('CHANGE PASSWORD MODAL (forced after first login)'), 'CHANGE PASSWORD MODAL'),
        'CHANGE PASSWORD MODAL')
    forgot_pw_start = comment_start(
        find_lines(contains('FORGOT PASSWORD MODAL (OTP flow)'), 'FORGOT PASSWORD MODAL'), 'FORGOT PASSWORD MODAL')
    app_layout_start = comment_start(
        find_lines(stripped_eq('APP LAYOUT'), 'APP LAYOUT'), 'APP LAYOUT')
    sidebar_start = comment_start(
        find_lines(stripped_eq('SIDEBAR'), 'SIDEBAR'), 'SIDEBAR')
    main_wrapper_start = comment_start(
        find_lines(stripped_eq('MAIN WRAPPER'), 'MAIN WRAPPER'), 'MAIN WRAPPER')
    top_navbar_start = comment_start(
        find_lines(stripped_eq('TOP NAVBAR'), 'TOP NAVBAR'), 'TOP NAVBAR')
    main_content_start = comment_start(
        find_lines(stripped_eq('MAIN CONTENT'), 'MAIN CONTENT'), 'MAIN CONTENT')
    app_scripts_start = comment_start(
        find_lines(stripped_eq('APPLICATION SCRIPTS'), 'APPLICATION SCRIPTS'), 'APPLICATION SCRIPTS')
    first_script_start = find_first(
        lambda ln: ln.strip().startswith('<script src="/static/js'), 'first <script src="/static/js')

    # ── Locate page containers (one file per page) ────────────────
    page_markers = []  # (slug, line_index)
    for i, ln in enumerate(lines):
        # NB: no `$` anchor — some pages have the opening <div> on the same
        # line as the `<!-- ── Name Page ── -->` comment (procurement, inventory).
        m = re.match(r'^\s*<!--\s*──\s*(.+?)\s*Page\s*──\s*-->', ln)
        if m:
            slug = re.sub(r'[^a-zA-Z0-9]+', '_', m.group(1).strip().lower()).strip('_')
            page_markers.append((slug, i))
    print(f'[INFO] found {len(page_markers)} page containers')
    for slug, idx in page_markers:
        print(f'        {slug:>22}  (line {idx + 1})')

    # ── Ordered region boundaries; region i spans [b[i], b[i+1]) ───
    # Leading (SHELL, 0) keeps <!DOCTYPE html> / <html ...> in index.html.
    boundaries = [
        (SHELL, 0),
        ('head', head_start),
        (SHELL, head_end + 1),
        ('login', login_start),
        ('modal_change_password', change_pw_start),
        ('modal_forgot_password', forgot_pw_start),
        ('layout_open', app_layout_start),
        ('sidebar', sidebar_start),
        ('wrapper_open', main_wrapper_start),
        ('navbar', top_navbar_start),
        ('main_open', main_content_start),
    ]
    for slug, idx in page_markers:
        boundaries.append((f'pages/{slug}', idx))
    boundaries += [
        ('main_close', main_close),
        ('modals_extra', app_scripts_start),
        ('scripts', first_script_start),
        (SHELL, body_end),
    ]
    boundaries.append(('__end__', n))

    # Validate ordering + coverage
    prev = boundaries[0][1]
    for name, idx in boundaries[1:]:
        if idx <= prev:
            fatal(f'region boundaries out of order: {name!r} at line {idx + 1} after {prev + 1}')
        prev = idx

    # ── Write partials + shell ─────────────────────────────────────
    os.makedirs(PAGES_DIR, exist_ok=True)
    written = []
    shell = []
    for (name, start), (_, end) in zip(boundaries, boundaries[1:]):
        if name in (SHELL, '__end__'):
            shell.extend(lines[start:end])
            continue
        rel = f'index/{name}.html' if name.startswith('pages/') else f'index/_{name}.html'
        path = os.path.join(ROOT, 'templates', *rel.split('/'))
        # Jinja strips ONE trailing newline from every included template
        # (keep_trailing_newline=False). An extra trailing '\n' compensates,
        # so the include renders the block byte-for-byte.
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(lines[start:end]) + '\n')
        written.append(rel)
        shell.append(f"{{% include '{rel}' %}}")

    shell_text = '\n'.join(shell)
    with open(SRC, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(shell_text)

    total = sum(1 for r in written)
    print(f'[OK] wrote {total} partials')
    for rel in written:
        print(f'      templates/{rel}')
    print(f'[OK] rewrote templates/index.html as {len(shell_text)}-char Jinja shell')


if __name__ == '__main__':
    main()
