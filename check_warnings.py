"""Check what the console warnings are"""
import sys
import tempfile
import time

from _hta_url import hta_index_url

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
temp = tempfile.mkdtemp(prefix="hta_warn_")
options.add_argument(f"--user-data-dir={temp}")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

try:
    driver.get(hta_index_url())
    time.sleep(2)

    # Click demo
    driver.execute_script("document.getElementById('btn-demo').click()")
    time.sleep(3)

    # Get logs
    logs = driver.get_log('browser')

    warnings = [l for l in logs if l['level'] == 'WARNING']
    errors = [l for l in logs if l['level'] == 'SEVERE']

    print(f"Total logs: {len(logs)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errors: {len(errors)}")

    if warnings:
        print("\nFirst 10 warnings:")
        for w in warnings[:10]:
            print(f"  - {w['message'][:150]}")

    if errors:
        print("\nAll errors:")
        for e in errors:
            print(f"  - {e['message'][:150]}")

finally:
    driver.quit()
