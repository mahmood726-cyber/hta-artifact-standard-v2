"""Test advanced enhancement classes with Edge"""
import time
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service

options = EdgeOptions()
temp = tempfile.mkdtemp(prefix="hta_edge_")
options.add_argument(f"--user-data-dir={temp}")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--headless=new")

print("Starting Edge browser...")
driver = webdriver.Edge(options=options)

try:
    driver.get("file:///C:/Users/user/Downloads/HTA/index.html")
    time.sleep(3)

    # List of classes that should be loaded
    classes = [
        'HKSJAdjustment',
        'CopasSelectionModel',
        'ProfileLikelihoodCI',
        'RoystonParmarSurvival',
        'MCMCDiagnostics',
        'MultivariateMetaAnalysis',
        'NetworkMetaRegression',
        'MixtureCureModel',
        'GRADEAssessment',
        'ValidationReport'
    ]

    print("\n=== Testing Advanced Enhancement Classes ===\n")

    passed = 0
    failed = 0
    for cls in classes:
        exists = driver.execute_script(f"return typeof window.{cls} !== 'undefined'")
        if exists:
            print(f"  [OK] {cls}")
            passed += 1
        else:
            print(f"  [FAIL] {cls}")
            failed += 1

    print(f"\n=== Results: {passed}/{len(classes)} classes loaded ===")

    # Quick functional test
    print("\n=== Functional Test: HKSJ ===")
    result = driver.execute_script("""
        try {
            const hksj = new HKSJAdjustment();
            const studies = [
                {effect: 0.5, se: 0.1},
                {effect: 0.3, se: 0.15},
                {effect: 0.6, se: 0.12}
            ];
            const r = hksj.adjust(studies, 0.01, 0.47);
            return 'CI: [' + r.ci_lower.toFixed(3) + ', ' + r.ci_upper.toFixed(3) + '] with t-dist df=' + r.df;
        } catch(e) {
            return 'Error: ' + e.message;
        }
    """)
    print(f"  {result}")

    # Check console errors
    logs = driver.get_log('browser')
    errors = [l for l in logs if l['level'] == 'SEVERE' and 'advancedEnhancements' in l['message']]
    if errors:
        print("\n=== Errors in advancedEnhancements.js ===")
        for e in errors:
            print(f"  {e['message'][:100]}")
    else:
        print("\n  No errors in advancedEnhancements.js")

finally:
    driver.quit()
    print("\nDone.")
