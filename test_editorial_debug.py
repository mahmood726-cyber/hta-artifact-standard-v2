"""Debug Editorial Review Round 2 Fixes"""
import time
import sys
import tempfile
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
temp = tempfile.mkdtemp(prefix="hta_debug_")
options.add_argument(f"--user-data-dir={temp}")

print("Starting Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.get("file:///C:/Users/user/Downloads/HTA/index.html")
    time.sleep(2)

    print("\n=== Debug Editorial Round 2 ===\n")

    # Test 1: Meta-regression
    result1 = driver.execute_script("""
        try {
            const ma = new MetaAnalysis({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.15, moderator: 1 },
                { effect: 0.3, se: 0.20, moderator: 2 },
                { effect: 0.7, se: 0.12, moderator: 3 },
                { effect: 0.4, se: 0.18, moderator: 2 },
                { effect: 0.6, se: 0.14, moderator: 3 }
            ];
            const result = ma.metaRegression(studies, ['moderator']);
            return { result: JSON.stringify(result) };
        } catch(e) {
            return { error: e.message, stack: e.stack };
        }
    """)
    print("1. Meta-regression:")
    if result1.get('error'):
        print(f"   ERROR: {result1['error']}")
        print(f"   Stack: {result1.get('stack', '')[:300]}")
    else:
        print(f"   Result: {result1.get('result', 'null')[:300]}")

    # Test 2: Trim-and-fill
    result2 = driver.execute_script("""
        try {
            const ma = new MetaAnalysis({ model: 'random' });
            const studies = [
                { effect: 0.8, se: 0.15 },
                { effect: 0.6, se: 0.18 },
                { effect: 0.9, se: 0.12 },
                { effect: 0.7, se: 0.20 },
                { effect: 0.5, se: 0.22 }
            ];
            const result = ma.trimAndFill(studies);
            return { result: JSON.stringify(result) };
        } catch(e) {
            return { error: e.message, stack: e.stack };
        }
    """)
    print("\n2. Trim-and-fill:")
    if result2.get('error'):
        print(f"   ERROR: {result2['error']}")
        print(f"   Stack: {result2.get('stack', '')[:300]}")
    else:
        print(f"   Result: {result2.get('result', 'null')[:300]}")

    # Test 3: Selection model
    result3 = driver.execute_script("""
        try {
            const ma = new MetaAnalysis({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.10 },
                { effect: 0.3, se: 0.08 },
                { effect: 0.6, se: 0.09 },
                { effect: 0.1, se: 0.15 },
                { effect: 0.15, se: 0.18 },
                { effect: 0.4, se: 0.11 },
                { effect: 0.2, se: 0.20 }
            ];
            const result = ma.selectionModel(studies);
            return { result: JSON.stringify(result) };
        } catch(e) {
            return { error: e.message, stack: e.stack };
        }
    """)
    print("\n3. Selection model:")
    if result3.get('error'):
        print(f"   ERROR: {result3['error']}")
        print(f"   Stack: {result3.get('stack', '')[:300]}")
    else:
        print(f"   Result: {result3.get('result', 'null')[:300]}")

    # Test 6: Subgroup analysis
    result6 = driver.execute_script("""
        try {
            const ma = new MetaAnalysis({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.15, group: 'A' },
                { effect: 0.4, se: 0.18, group: 'A' },
                { effect: 0.6, se: 0.12, group: 'A' },
                { effect: 0.8, se: 0.14, group: 'B' },
                { effect: 0.9, se: 0.16, group: 'B' },
                { effect: 0.7, se: 0.20, group: 'B' }
            ];
            const result = ma.subgroupAnalysis(studies, 'group');
            return { result: JSON.stringify(result) };
        } catch(e) {
            return { error: e.message, stack: e.stack };
        }
    """)
    print("\n6. Subgroup analysis:")
    if result6.get('error'):
        print(f"   ERROR: {result6['error']}")
        print(f"   Stack: {result6.get('stack', '')[:300]}")
    else:
        print(f"   Result: {result6.get('result', 'null')[:300]}")

finally:
    driver.quit()
