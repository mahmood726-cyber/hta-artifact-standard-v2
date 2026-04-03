"""
Test script to verify BeginnerMode features work correctly
"""
import time
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_beginner_mode():
    options = EdgeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    temp = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={temp}')

    driver = webdriver.Edge(options=options)

    try:
        print("Loading HTA app...")
        driver.get('file:///C:/Users/user/Downloads/HTA/index.html')
        time.sleep(3)

        results = {}

        # Test 1: Check if BeginnerMode class exists
        print("\n1. Testing BeginnerMode class exists...")
        exists = driver.execute_script('return typeof BeginnerMode !== "undefined"')
        results['BeginnerMode exists'] = exists
        print(f"   BeginnerMode class exists: {exists}")

        # Test 2: Check if welcome modal was created
        print("\n2. Testing welcome modal...")
        modal = driver.execute_script('return document.getElementById("welcome-modal") !== null')
        results['Welcome modal created'] = modal
        print(f"   Welcome modal created: {modal}")

        # Test 3: Check if help button was created
        print("\n3. Testing help button...")
        help_btn = driver.execute_script('return document.getElementById("help-button") !== null')
        results['Help button created'] = help_btn
        print(f"   Help button created: {help_btn}")

        # Test 4: Check if help panel was created
        print("\n4. Testing help panel...")
        help_panel = driver.execute_script('return document.getElementById("help-panel") !== null')
        results['Help panel created'] = help_panel
        print(f"   Help panel created: {help_panel}")

        # Test 5: Test sample datasets function
        print("\n5. Testing sample datasets...")
        datasets = driver.execute_script('''
            if (window.beginnerMode && window.beginnerMode.getSampleDatasets) {
                const datasets = window.beginnerMode.getSampleDatasets();
                return {
                    hasBCG: !!datasets.bcg,
                    hasAmlodipine: !!datasets.amlodipine,
                    hasSmoking: !!datasets.smoking,
                    hasDiabetes: !!datasets.diabetes,
                    bcgStudyCount: datasets.bcg ? datasets.bcg.studies.length : 0
                };
            }
            return null;
        ''')
        if datasets:
            results['Sample datasets'] = datasets['hasBCG'] and datasets['hasAmlodipine']
            print(f"   BCG dataset: {datasets['hasBCG']} ({datasets['bcgStudyCount']} studies)")
            print(f"   Amlodipine dataset: {datasets['hasAmlodipine']}")
            print(f"   Smoking NMA dataset: {datasets['hasSmoking']}")
            print(f"   Diabetes DTA dataset: {datasets['hasDiabetes']}")
        else:
            results['Sample datasets'] = False
            print("   Sample datasets: Failed to load")

        # Test 6: Test loading a sample dataset
        print("\n6. Testing loading BCG dataset...")
        load_result = driver.execute_script('''
            if (window.beginnerMode && window.beginnerMode.loadSampleDataset) {
                try {
                    window.beginnerMode.loadSampleDataset('bcg');
                    return true;
                } catch(e) {
                    return { error: e.message };
                }
            }
            return false;
        ''')
        results['Load BCG dataset'] = load_result == True
        print(f"   Load BCG dataset: {load_result}")

        # Test 7: Test help panel toggle
        print("\n7. Testing help panel toggle...")
        toggle_result = driver.execute_script('''
            const panel = document.getElementById('help-panel');
            if (panel && window.beginnerMode && window.beginnerMode.toggleHelpPanel) {
                window.beginnerMode.toggleHelpPanel();
                const visible = panel.style.display !== 'none';
                window.beginnerMode.toggleHelpPanel();
                return visible;
            }
            return false;
        ''')
        results['Help panel toggle'] = toggle_result
        print(f"   Help panel toggle: {toggle_result}")

        # Test 8: Test result interpretation
        print("\n8. Testing result interpretation...")
        interp_result = driver.execute_script('''
            if (window.beginnerMode && window.beginnerMode.interpretResults) {
                const testResults = {
                    pooled: { effect: 0.5, ci: [0.3, 0.8] },
                    heterogeneity: { I2: 75, Q: 20, pValue: 0.001 }
                };
                const interp = window.beginnerMode.interpretResults('OR', testResults);
                return interp && interp.length > 0;
            }
            return false;
        ''')
        results['Result interpretation'] = interp_result
        print(f"   Result interpretation works: {interp_result}")

        # Test 9: Check tooltips
        print("\n9. Testing tooltips...")
        tooltip_count = driver.execute_script('''
            return document.querySelectorAll('.stat-term-tooltip').length;
        ''')
        results['Tooltips added'] = tooltip_count > 0
        print(f"   Tooltips added: {tooltip_count} tooltips found")

        # Test 10: Test data entry interface
        print("\n10. Testing data entry interface...")
        data_entry = driver.execute_script('''
            if (window.beginnerMode && window.beginnerMode.showDataEntryModal) {
                try {
                    window.beginnerMode.showDataEntryModal();
                    const panel = document.getElementById('data-entry-panel');
                    const exists = panel !== null;
                    if (panel) panel.classList.remove('active');
                    return exists;
                } catch(e) {
                    return { error: e.message };
                }
            }
            return false;
        ''')
        results['Data entry interface'] = data_entry == True
        print(f"   Data entry interface: {data_entry}")

        # Summary
        print("\n" + "=" * 50)
        print("BEGINNER MODE TEST SUMMARY")
        print("=" * 50)

        passed = sum(1 for v in results.values() if v == True or v is True)
        total = len(results)

        for test, result in results.items():
            status = "PASS" if result == True or result is True else "FAIL"
            print(f"  {test}: {status}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("\nAll beginner mode features working correctly!")
            return True
        else:
            print("\nSome features need attention.")
            return False

    finally:
        driver.quit()

if __name__ == '__main__':
    success = test_beginner_mode()
    sys.exit(0 if success else 1)
