"""Audit every manifest template: is it wired to real JS? Does it contain fake data?"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
manifest = json.load(open(os.path.join(ROOT, 'backend', 'pages_manifest.json'), encoding='utf-8'))
tpls = sorted({v['template'] for v in manifest.values()})

HARD_RE = re.compile(r'₹[0-9][\d,.]*[LC]?|[0-9][\d,]* / [0-9][\d,]*|>[0-9][\d.]*\s*L<')
CHART_RE = re.compile(r"data:\[\d|data:\[\s*\d|\[40,55|\[45,35|labels:\['Mon'")


def classify(rel):
    p = os.path.join(ROOT, 'templates', rel)
    if not os.path.exists(p):
        return 'MISSING', '-', '-', '-', '-'
    text = open(p, encoding='utf-8').read()
    init_m = re.search(r'page_init %}init(\w+)', text)
    init = init_m.group(1) if init_m else ''
    js = 'YES' if re.search(r'script src="/static/js/', text) else ''
    hard = 'HARD' if HARD_RE.search(text) else ''
    chart = 'FAKE' if CHART_RE.search(text) else ''
    return init, js, hard, chart


print(f"{'TEMPLATE':60} {'INIT':30} {'JS':4} {'HARD':5} {'FAKECHART':10}")
print('-' * 115)
for rel in tpls:
    init, js, hard, chart = classify(rel)
    print(f"{rel:60} {init:30} {js:4} {hard:5} {chart:10}")
