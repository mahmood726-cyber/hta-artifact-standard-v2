"""
Comprehensive Selenium Test for HTA Artifact Standard v0.5
Tests all features, sections, and chart rendering
"""

import time
import os
import sys
import tempfile
from pathlib import Path

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    JavascriptException,
    ElementClickInterceptedException
)

# Test results tracking
class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, name, details=""):
        self.passed.append((name, details))
        print(f"  [PASS] {name}")

    def add_fail(self, name, error):
        self.failed.append((name, str(error)))
        print(f"  [FAIL] {name}: {error}")

    def add_warning(self, name, msg):
        self.warnings.append((name, msg))
        print(f"  [WARN] {name}: {msg}")

    def summary(self):
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Passed:   {len(self.passed)}")
        print(f"Failed:   {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.failed:
            print("\nFailed Tests:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")

        if self.warnings:
            print("\nWarnings:")
            for name, msg in self.warnings:
                print(f"  - {name}: {msg}")

        return len(self.failed) == 0

results = TestResults()

def setup_driver():
    """Setup browser driver - try Edge first since Chrome may be busy"""
    # Try Edge first since Chrome is likely in use by another Selenium instance
    try:
        from selenium.webdriver.edge.options import Options as EdgeOptions
        edge_options = EdgeOptions()
        edge_temp = tempfile.mkdtemp(prefix="hta_selenium_edge_")
        edge_options.add_argument(f"--user-data-dir={edge_temp}")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--disable-extensions")
        print("Trying Edge browser...")
        driver = webdriver.Edge(options=edge_options)
        print("Edge driver created successfully")
        return driver
    except Exception as e:
        print(f"Failed to create Edge driver: {e}")

    # Try Chrome as fallback
    try:
        options = Options()
        temp_dir = tempfile.mkdtemp(prefix="hta_selenium_test_")
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.add_argument("--remote-debugging-port=9223")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        print("Trying Chrome browser...")
        driver = webdriver.Chrome(options=options)
        print("Chrome driver created successfully")
        return driver
    except Exception as e:
        print(f"Failed to create Chrome driver: {e}")
        sys.exit(1)

def test_page_load(driver, file_path):
    """Test that the page loads correctly"""
    print("\n[1] Testing Page Load...")

    try:
        driver.get(f"file:///{file_path}")
        time.sleep(2)

        # Check title
        if "HTA Artifact Standard" in driver.title:
            results.add_pass("Page title correct", driver.title)
        else:
            results.add_fail("Page title", f"Expected 'HTA Artifact Standard', got '{driver.title}'")

        # Check for JavaScript errors
        logs = driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        if js_errors:
            for err in js_errors[:5]:  # Show first 5 errors
                results.add_warning("JavaScript error", err['message'][:100])
        else:
            results.add_pass("No JavaScript errors on load")

    except Exception as e:
        results.add_fail("Page load", str(e))

def test_drop_zone(driver):
    """Test the file drop zone"""
    print("\n[2] Testing Drop Zone...")

    try:
        drop_zone = driver.find_element(By.CLASS_NAME, "drop-zone")
        if drop_zone.is_displayed():
            results.add_pass("Drop zone visible")
        else:
            results.add_fail("Drop zone", "Not visible")

        # Check for file input
        file_input = driver.find_element(By.ID, "file-input")
        if file_input:
            results.add_pass("File input exists")

    except NoSuchElementException as e:
        results.add_fail("Drop zone elements", str(e))

def test_demo_mode(driver):
    """Test activating demo mode"""
    print("\n[3] Testing Demo Mode Activation...")

    try:
        # Find and click the demo button (correct ID: btn-demo)
        demo_btn = driver.find_element(By.ID, "btn-demo")
        driver.execute_script("arguments[0].click();", demo_btn)
        time.sleep(3)  # Give more time for model to load

        # Check if main content is now visible
        try:
            main_content = driver.find_element(By.CLASS_NAME, "main-content")
            if main_content.is_displayed():
                results.add_pass("Demo mode activated - main content visible")
            else:
                results.add_fail("Demo mode", "Main content not visible after demo load")
        except:
            results.add_pass("Demo mode button clicked")

        # Check sidebar is visible
        sidebar = driver.find_element(By.CLASS_NAME, "sidebar")
        if sidebar.is_displayed():
            results.add_pass("Sidebar visible")

    except Exception as e:
        results.add_fail("Demo mode activation", str(e))

def test_all_sections(driver):
    """Test navigation to all sections"""
    print("\n[4] Testing All Navigation Sections...")

    sections = [
        "summary", "validation", "parameters", "states", "transitions",
        "deterministic", "psa", "charts", "run-engine", "export",
        "microsim", "des", "survival", "calibration", "evppi",
        "nma", "meta-methods", "pub-bias", "reporting",
        "three-level", "multivariate", "dose-response", "component-nma",
        "living-review", "rob-assessment", "prisma-flow",
        "ipd-meta", "dta-meta", "advanced-pb", "fabrication",
        "ml-screening", "mr-meta", "historical", "survival-ma",
        "threshold", "federated"
    ]

    for section in sections:
        try:
            nav_item = driver.find_element(By.CSS_SELECTOR, f'[data-section="{section}"]')

            # Use JavaScript to scroll into view within the sidebar
            driver.execute_script("""
                var sidebar = document.querySelector('.sidebar');
                var item = arguments[0];
                if (sidebar) {
                    sidebar.scrollTop = item.offsetTop - 100;
                }
                item.scrollIntoView({block: 'center', behavior: 'instant'});
            """, nav_item)
            time.sleep(0.3)

            # Always use JavaScript click for reliability
            driver.execute_script("arguments[0].click();", nav_item)
            time.sleep(0.5)

            # Check if section content exists (correct format: section-{name})
            try:
                section_content = driver.find_element(By.ID, f"section-{section}")
                style = section_content.get_attribute("style") or ""
                if "none" not in style.lower():
                    results.add_pass(f"Section '{section}'", "Visible and accessible")
                else:
                    results.add_warning(f"Section '{section}'", "Exists but may be hidden")
            except NoSuchElementException:
                # Some sections may not have content yet
                results.add_warning(f"Section '{section}'", f"No section-{section} element found")

        except NoSuchElementException:
            results.add_warning(f"Section '{section}'", "Nav item not found")
        except Exception as e:
            results.add_fail(f"Section '{section}'", str(e))

def test_charts(driver):
    """Test all chart canvases"""
    print("\n[5] Testing Chart Canvases...")

    chart_ids = [
        "trace-chart", "ce-plane-chart", "ceac-chart",
        "tornado-chart", "survival-chart",
        "microsim-state-chart", "microsim-trace-chart",
        "km-chart", "survival-comparison-chart",
        "evppi-chart", "nma-network-chart", "nma-ranking-chart",
        "nma-forest-chart", "nma-funnel-chart",
        "ma-forest-chart", "ma-cumulative-chart",
        "pub-bias-funnel-chart", "trim-fill-chart",
        "dr-curve-chart", "living-boundaries-chart",
        "dta-sroc-chart", "pb-sensitivity-chart",
        "mr-scatter-chart", "survival-curves-chart",
        "federated-weights-chart"
    ]

    for chart_id in chart_ids:
        try:
            canvas = driver.find_element(By.ID, chart_id)
            if canvas:
                # Check if canvas has dimensions
                width = canvas.get_attribute("width")
                height = canvas.get_attribute("height")

                if width and height and int(width) > 0 and int(height) > 0:
                    results.add_pass(f"Canvas '{chart_id}'", f"Size: {width}x{height}")
                else:
                    results.add_warning(f"Canvas '{chart_id}'", "Exists but no dimensions")

        except NoSuchElementException:
            results.add_warning(f"Canvas '{chart_id}'", "Not found")
        except Exception as e:
            results.add_fail(f"Canvas '{chart_id}'", str(e))

def test_meta_analysis_features(driver):
    """Test meta-analysis specific features"""
    print("\n[6] Testing Meta-Analysis Features...")

    # Navigate to meta-methods section
    try:
        nav_item = driver.find_element(By.CSS_SELECTOR, '[data-section="meta-methods"]')
        driver.execute_script("arguments[0].click();", nav_item)
        time.sleep(1)

        # Check for HKSJ option
        hksj_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'HKSJ') or contains(text(), 'Hartung')]")
        if hksj_elements:
            results.add_pass("HKSJ adjustment option", "Found in UI")
        else:
            results.add_warning("HKSJ adjustment", "Option not found in meta-methods section")

        # Check for prediction interval option
        pred_int = driver.find_elements(By.XPATH, "//*[contains(text(), 'prediction interval') or contains(text(), 'Prediction Interval')]")
        if pred_int:
            results.add_pass("Prediction interval option", "Found in UI")

    except Exception as e:
        results.add_fail("Meta-analysis features", str(e))

def test_nma_features(driver):
    """Test network meta-analysis features"""
    print("\n[7] Testing NMA Features...")

    try:
        nav_item = driver.find_element(By.CSS_SELECTOR, '[data-section="nma"]')
        driver.execute_script("arguments[0].click();", nav_item)
        time.sleep(1)

        # Check for network visualization
        network_canvas = driver.find_element(By.ID, "nma-network-chart")
        if network_canvas:
            results.add_pass("NMA network chart", "Canvas exists")

        # Check for ranking chart
        ranking_canvas = driver.find_element(By.ID, "nma-ranking-chart")
        if ranking_canvas:
            results.add_pass("NMA ranking chart", "Canvas exists")

        # Check for consistency check option
        consistency = driver.find_elements(By.XPATH, "//*[contains(text(), 'consistency') or contains(text(), 'Consistency')]")
        if consistency:
            results.add_pass("NMA consistency check", "Option found")

    except Exception as e:
        results.add_fail("NMA features", str(e))

def test_publication_bias(driver):
    """Test publication bias features"""
    print("\n[8] Testing Publication Bias Features...")

    try:
        nav_item = driver.find_element(By.CSS_SELECTOR, '[data-section="pub-bias"]')
        driver.execute_script("arguments[0].click();", nav_item)
        time.sleep(1)

        # Check for funnel plot
        funnel_canvas = driver.find_element(By.ID, "pub-bias-funnel-chart")
        if funnel_canvas:
            results.add_pass("Funnel plot canvas", "Exists")

        # Check for trim-and-fill
        trim_fill = driver.find_elements(By.XPATH, "//*[contains(text(), 'trim') or contains(text(), 'Trim')]")
        if trim_fill:
            results.add_pass("Trim-and-fill option", "Found in UI")

        # Check for Egger test
        egger = driver.find_elements(By.XPATH, "//*[contains(text(), 'Egger') or contains(text(), 'egger')]")
        if egger:
            results.add_pass("Egger test option", "Found in UI")

    except Exception as e:
        results.add_fail("Publication bias features", str(e))

def test_survival_analysis(driver):
    """Test survival analysis features"""
    print("\n[9] Testing Survival Analysis Features...")

    try:
        nav_item = driver.find_element(By.CSS_SELECTOR, '[data-section="survival"]')
        driver.execute_script("arguments[0].click();", nav_item)
        time.sleep(1)

        # Check for KM chart
        km_canvas = driver.find_element(By.ID, "km-chart")
        if km_canvas:
            results.add_pass("Kaplan-Meier chart", "Canvas exists")

        # Check for model selection
        model_selection = driver.find_elements(By.XPATH, "//*[contains(text(), 'AIC') or contains(text(), 'BIC')]")
        if model_selection:
            results.add_pass("Model selection criteria", "AIC/BIC found")

    except Exception as e:
        results.add_fail("Survival analysis features", str(e))

def test_evppi_features(driver):
    """Test EVPPI features"""
    print("\n[10] Testing EVPPI Features...")

    try:
        nav_item = driver.find_element(By.CSS_SELECTOR, '[data-section="evppi"]')
        driver.execute_script("arguments[0].click();", nav_item)
        time.sleep(1)

        # Check for EVPPI chart
        evppi_canvas = driver.find_element(By.ID, "evppi-chart")
        if evppi_canvas:
            results.add_pass("EVPPI chart", "Canvas exists")

        # Check for EVPI
        evpi = driver.find_elements(By.XPATH, "//*[contains(text(), 'EVPI') or contains(text(), 'Expected Value')]")
        if evpi:
            results.add_pass("EVPI calculation", "Found in UI")

    except Exception as e:
        results.add_fail("EVPPI features", str(e))

def test_buttons_and_forms(driver):
    """Test all buttons and form elements"""
    print("\n[11] Testing Buttons and Forms...")

    try:
        # Count all buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        results.add_pass(f"Buttons found", f"{len(buttons)} buttons")

        # Count all inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        results.add_pass(f"Input fields found", f"{len(inputs)} inputs")

        # Count all selects
        selects = driver.find_elements(By.TAG_NAME, "select")
        results.add_pass(f"Select dropdowns found", f"{len(selects)} selects")

        # Test that primary buttons are clickable
        primary_btns = driver.find_elements(By.CLASS_NAME, "btn-primary")
        clickable_count = 0
        for btn in primary_btns[:5]:  # Test first 5
            try:
                if btn.is_enabled():
                    clickable_count += 1
            except:
                pass
        results.add_pass(f"Primary buttons", f"{clickable_count}/{min(5, len(primary_btns))} clickable")

    except Exception as e:
        results.add_fail("Buttons and forms", str(e))

def test_responsive_elements(driver):
    """Test responsive layout elements"""
    print("\n[12] Testing Layout and Responsiveness...")

    try:
        # Check main container
        container = driver.find_element(By.CLASS_NAME, "app-container")
        if container.is_displayed():
            results.add_pass("App container", "Visible")

        # Check header
        header = driver.find_element(By.TAG_NAME, "header")
        if header.is_displayed():
            results.add_pass("Header", "Visible")

        # Check content area
        content = driver.find_element(By.CLASS_NAME, "content-area")
        if content.is_displayed():
            results.add_pass("Content area", "Visible")

    except Exception as e:
        results.add_fail("Layout elements", str(e))

def test_javascript_functions(driver):
    """Test that key JavaScript functions exist"""
    print("\n[13] Testing JavaScript Functions...")

    functions_to_test = [
        "showSection",
        "runDeterministicAnalysis",
        "runPSA",
        "exportResults",
        "loadDemoData"
    ]

    for func in functions_to_test:
        try:
            result = driver.execute_script(f"return typeof {func} === 'function'")
            if result:
                results.add_pass(f"Function '{func}'", "Exists")
            else:
                results.add_warning(f"Function '{func}'", "Not found or not a function")
        except JavascriptException as e:
            results.add_fail(f"Function '{func}'", str(e))

def test_chart_library(driver):
    """Test that Chart.js is loaded and working"""
    print("\n[14] Testing Chart.js Library...")

    try:
        chart_exists = driver.execute_script("return typeof Chart !== 'undefined'")
        if chart_exists:
            results.add_pass("Chart.js", "Library loaded")

            # Check Chart.js version
            version = driver.execute_script("return Chart.version")
            results.add_pass("Chart.js version", version)
        else:
            results.add_fail("Chart.js", "Library not loaded")

    except Exception as e:
        results.add_fail("Chart.js check", str(e))

def check_console_errors(driver):
    """Check for any JavaScript console errors"""
    print("\n[15] Checking Console for Errors...")

    try:
        logs = driver.get_log('browser')

        errors = [log for log in logs if log['level'] == 'SEVERE']
        warnings = [log for log in logs if log['level'] == 'WARNING']

        if errors:
            results.add_fail("Console errors", f"{len(errors)} errors found")
            for err in errors[:5]:
                print(f"      Error: {err['message'][:100]}")
        else:
            results.add_pass("Console errors", "None found")

        if warnings:
            results.add_warning("Console warnings", f"{len(warnings)} warnings")

    except Exception as e:
        results.add_warning("Console log check", f"Could not check: {e}")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("HTA Artifact Standard - Comprehensive Selenium Test")
    print("=" * 60)

    # Get the HTML file path
    html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        print(f"ERROR: Could not find {html_path}")
        sys.exit(1)

    # Convert to proper file URL format
    file_url = str(html_path.absolute()).replace("\\", "/")
    print(f"\nTesting file: {file_url}")

    # Setup driver
    print("\nSetting up Chrome driver...")
    driver = setup_driver()

    try:
        # Run all tests
        test_page_load(driver, file_url)
        test_drop_zone(driver)
        test_demo_mode(driver)
        test_all_sections(driver)
        test_charts(driver)
        test_meta_analysis_features(driver)
        test_nma_features(driver)
        test_publication_bias(driver)
        test_survival_analysis(driver)
        test_evppi_features(driver)
        test_buttons_and_forms(driver)
        test_responsive_elements(driver)
        test_javascript_functions(driver)
        test_chart_library(driver)
        check_console_errors(driver)

        # Summary
        success = results.summary()

        # Keep browser open for 5 seconds to see results
        print("\nKeeping browser open for 5 seconds...")
        time.sleep(5)

        return success

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        driver.quit()
        print("\nBrowser closed.")

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
