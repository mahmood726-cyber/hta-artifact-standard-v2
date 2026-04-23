"""Check what's exported on window"""
from _hta_url import hta_index_url, hta_index_path
import time
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
temp = tempfile.mkdtemp(prefix="hta_exp_")
options.add_argument(f"--user-data-dir={temp}")

print("Starting Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.get(hta_index_url())
    time.sleep(3)

    result = driver.execute_script("""
        const classes = [
            'MetaAnalysisMethods',
            'NetworkMetaAnalysis',
            'CopasSelectionModel',
            'AdvancedEnhancements',
            'FrontierMeta',
            'MarkovModel',
            'PSA'
        ];
        const found = {};
        for (const c of classes) {
            found[c] = typeof window[c] !== 'undefined';
        }
        return found;
    """)

    print("\nExported classes on window:")
    for name, available in result.items():
        status = "FOUND" if available else "NOT FOUND"
        print(f"  {name}: {status}")

finally:
    driver.quit()
