"""Quick test to identify remaining warnings"""
import time
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
temp = tempfile.mkdtemp(prefix="hta_quick_")
options.add_argument(f"--user-data-dir={temp}")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

try:
    driver.get("file:///C:/Users/user/Downloads/HTA/index.html")
    time.sleep(2)

    # Click demo
    driver.execute_script("document.getElementById('btn-demo').click()")
    time.sleep(3)

    print("=== Testing PSA ===")
    # Navigate to PSA
    driver.execute_script("window.showSection('psa')")
    time.sleep(0.5)

    # Check for PSA button
    btn = driver.find_element(By.ID, "btn-run-psa-full")
    print(f"PSA button found: {btn is not None}")
    print(f"PSA button displayed: {btn.is_displayed()}")

    # Click PSA button
    driver.execute_script("document.getElementById('btn-run-psa-full').click()")
    time.sleep(3)

    # Check CE plane chart
    chart_exists = driver.execute_script("""
        const canvas = document.getElementById('ce-plane-chart');
        console.log('Canvas:', canvas);
        if (!canvas) return 'canvas not found';
        const ctx = canvas.getContext('2d');
        console.log('Context:', ctx);
        return ctx ? 'has context' : 'no context';
    """)
    print(f"CE plane chart status: {chart_exists}")

    print("\n=== Testing Input Focus ===")
    # Navigate to parameters
    driver.execute_script("window.showSection('parameters')")
    time.sleep(0.5)

    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"Found {len(inputs)} inputs")

    if inputs:
        # Try to find a visible input
        for i, inp in enumerate(inputs[:10]):
            try:
                if inp.is_displayed():
                    print(f"Input {i} is displayed, type: {inp.get_attribute('type')}")
                    inp.click()
                    focused = driver.execute_script("return document.activeElement.tagName.toLowerCase()")
                    print(f"After click, focused element: {focused}")
                    break
            except Exception as e:
                print(f"Input {i} error: {e}")

    print("\n=== Testing Export ===")
    driver.execute_script("window.showSection('export')")
    time.sleep(0.5)

    export_btns = driver.find_elements(By.CSS_SELECTOR, "[id*='export'], [id*='download']")
    print(f"Found {len(export_btns)} export/download buttons")
    for btn in export_btns[:5]:
        print(f"  - {btn.get_attribute('id')}")

    print("\n=== Console Logs ===")
    logs = driver.get_log('browser')
    warnings = [l for l in logs if l['level'] == 'WARNING']
    errors = [l for l in logs if l['level'] == 'SEVERE']
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors:
        print("\nErrors:")
        for e in errors[:5]:
            print(f"  - {e['message'][:100]}")

    if warnings:
        print("\nWarnings:")
        for w in warnings[:5]:
            print(f"  - {w['message'][:100]}")

finally:
    driver.quit()
    print("\nDone.")
