#!/usr/bin/env python3
"""Ta skjermbilder av portalen for visuell iterasjon. Bruk: python3 screenshot.py [url-suffix] [navn]"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = "/workspace/.vibe/shots"
import os; os.makedirs(OUT, exist_ok=True)

pages = [
    ("/", "forside"),
    ("/om", "om"),
    ("/modell", "modell"),
    ("/admin", "admin"),
]
if len(sys.argv) > 1:
    pages = [(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "shot")]

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    for path, name in pages:
        pg.goto(BASE + path, wait_until="networkidle")
        pg.wait_for_timeout(800)
        fp = f"{OUT}/{name}.png"
        pg.screenshot(path=fp, full_page=True)
        print("lagret", fp)
    b.close()
