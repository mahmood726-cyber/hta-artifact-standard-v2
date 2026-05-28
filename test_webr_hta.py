"""Test WebR validation in HTA Artifact Standard using Selenium + Edge"""
import io
import os
import sys
import time

if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options

options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1440,900')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

print("Starting Edge...")
driver = webdriver.Edge(options=options)
driver.set_page_load_timeout(60)

os.makedirs("Submission", exist_ok=True)

try:
    # 1. Load the app
    print("Loading HTA app...")
    driver.get("http://localhost:8768/index.html")
    time.sleep(5)
    print(f"Title: {driver.title}")

    # 2. Take initial screenshot
    driver.save_screenshot("Submission/Figure_1_Main.png")
    print("-> Figure_1_Main.png")

    # 3. Check for meta-analysis tab and navigate to it
    has_ma = driver.execute_script("""
        var tabs = document.querySelectorAll('[data-section], [onclick*="show"], .tab, .nav-item, button');
        var found = [];
        for (var i = 0; i < tabs.length; i++) {
            var t = tabs[i].textContent.trim().substring(0, 40);
            if (t.indexOf('Meta') >= 0 || t.indexOf('Evidence') >= 0 || t.indexOf('Pairwise') >= 0) {
                found.push(t);
                tabs[i].click();
            }
        }
        return found;
    """)
    print(f"MA tabs found: {has_ma}")
    time.sleep(2)
    driver.save_screenshot("Submission/Figure_2_MetaAnalysis.png")
    print("-> Figure_2_MetaAnalysis.png")

    # 4. Navigate to validation section
    print("Looking for validation section...")
    val_found = driver.execute_script("""
        var tabs = document.querySelectorAll('[data-section], [onclick*="show"], .tab, .nav-item, button, a');
        for (var i = 0; i < tabs.length; i++) {
            var t = tabs[i].textContent.trim();
            if (t.indexOf('Validation') >= 0 || t.indexOf('Verify') >= 0 || t.indexOf('Quality') >= 0) {
                tabs[i].click();
                return t;
            }
        }
        return 'not found';
    """)
    print(f"Validation section: {val_found}")
    time.sleep(2)

    # 5. Check for WebR button
    webr_exists = driver.execute_script("return !!document.getElementById('webrRunBtn');")
    print(f"WebR button found: {webr_exists}")

    if not webr_exists:
        # Trigger MutationObserver by toggling to/from validation
        print("Trying to trigger MutationObserver...")
        driver.execute_script("""
            // Try to show validation section
            var sections = document.querySelectorAll('[id*="validation"], [id*="quality"]');
            for (var s of sections) { s.style.display = 'block'; }
        """)
        time.sleep(2)
        webr_exists = driver.execute_script("return !!document.getElementById('webrRunBtn');")
        print(f"WebR after trigger: {webr_exists}")

    driver.save_screenshot("Submission/Figure_3_Validation.png")
    print("-> Figure_3_Validation.png")

    if webr_exists:
        # Scroll to WebR
        driver.execute_script("document.getElementById('webrRunBtn').scrollIntoView({block: 'center'});")
        time.sleep(1)
        driver.save_screenshot("Submission/Figure_4_WebR.png")
        print("-> Figure_4_WebR.png")

        # Check if there's data to validate
        has_data = driver.execute_script("""
            var rows = document.querySelectorAll('#ma-data-body tr');
            return rows ? rows.length : 0;
        """)
        print(f"MA data rows: {has_data}")

        if has_data > 0:
            print("Clicking WebR... (30-60s)")
            driver.execute_script("document.getElementById('webrRunBtn').click();")
            for i in range(18):
                time.sleep(5)
                badge = driver.execute_script("var b = document.getElementById('webrBadge'); return b ? b.textContent.trim() : '';")
                results = driver.execute_script("var r = document.getElementById('webrResults'); return r ? r.textContent.substring(0, 80) : '';")
                print(f"  [{(i+1)*5}s] badge='{badge}' results='{results}'")
                if (badge and 'GOLD' in badge.upper()) or 'FALLBACK' in badge.upper() or 'VALIDATED' in badge.upper():
                    print(f"  WebR completed! Badge: {badge}")
                    break

            driver.execute_script("var r = document.getElementById('webrResults'); if(r) r.scrollIntoView({block:'start'});")
            time.sleep(1)
            driver.save_screenshot("Submission/Figure_5_WebR_Results.png")
            print("-> Figure_5_WebR_Results.png")

            full = driver.execute_script("var r = document.getElementById('webrResults'); return r ? r.textContent : 'empty';")
            print(f"\nWebR Results:\n{full[:500]}")
        else:
            print("No MA data loaded — WebR needs data. Skipping WebR test.")
    else:
        print("WebR button not found in DOM")

    print(f"\n=== DONE ===\nFiles: {os.listdir('Submission/')}")

finally:
    driver.quit()
