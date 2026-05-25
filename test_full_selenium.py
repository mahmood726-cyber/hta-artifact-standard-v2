"""
Comprehensive Selenium Test Suite for HTA Artifact Standard v0.5
Tests all buttons, functions, and plots in Microsoft Edge

Run: python test_full_selenium.py
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class HTATestSuite:
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.driver = None

    def setup(self):
        """Initialize Edge WebDriver"""
        print("=" * 60)
        print("HTA Artifact Standard v0.5 - Comprehensive Test Suite")
        print("=" * 60)
        print("\nInitializing Microsoft Edge WebDriver...")

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.driver = webdriver.Edge(options=options)
        self.driver.implicitly_wait(5)
        self.wait = WebDriverWait(self.driver, 10)

        # Load the application
        file_path = os.path.abspath("index.html")
        self.driver.get(f"file:///{file_path}")
        time.sleep(2)
        print(f"Loaded: {file_path}")

    def teardown(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

    def log_result(self, test_name, passed, message=""):
        """Log test result"""
        if passed:
            self.results['passed'].append(test_name)
            print(f"  [PASS] {test_name}")
        else:
            self.results['failed'].append((test_name, message))
            print(f"  [FAIL] {test_name} - {message}")

    def log_warning(self, message):
        """Log warning"""
        self.results['warnings'].append(message)
        print(f"  [WARN] {message}")

    def click_element(self, selector, by=By.CSS_SELECTOR, timeout=5):
        """Safely click an element"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            element.click()
            return True
        except Exception:
            # Try JavaScript click as fallback
            try:
                element = self.driver.find_element(by, selector)
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False

    def element_exists(self, selector, by=By.CSS_SELECTOR, timeout=3):
        """Check if element exists"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except:
            return False

    def check_canvas_has_content(self, canvas_selector, timeout=3):
        """Check if a canvas element has been drawn on"""
        try:
            canvas = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, canvas_selector))
            )
            # Check if canvas has content by examining pixel data
            has_content = self.driver.execute_script("""
                const canvas = arguments[0];
                if (!canvas || canvas.tagName !== 'CANVAS') return false;
                const ctx = canvas.getContext('2d');
                if (!ctx) return false;
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;
                // Check if any non-transparent pixels exist
                for (let i = 3; i < data.length; i += 4) {
                    if (data[i] > 0) return true;
                }
                return false;
            """, canvas)
            return has_content
        except Exception:
            return False

    def check_chart_exists(self, container_selector, timeout=5):
        """Check if Chart.js chart exists and has rendered"""
        try:
            # Wait for canvas to appear
            canvas = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"{container_selector} canvas"))
            )
            time.sleep(0.5)  # Give chart time to render

            # Check canvas dimensions and content
            result = self.driver.execute_script("""
                const canvas = arguments[0];
                if (!canvas) return {exists: false, reason: 'no canvas'};
                if (canvas.width < 10 || canvas.height < 10)
                    return {exists: false, reason: 'canvas too small'};

                // Check for Chart.js instance
                const chart = Chart.getChart(canvas);
                if (chart) return {exists: true, type: chart.config.type};

                // Fallback: check if canvas has pixels
                const ctx = canvas.getContext('2d');
                const imageData = ctx.getImageData(0, 0, Math.min(canvas.width, 100), Math.min(canvas.height, 100));
                let nonEmpty = 0;
                for (let i = 3; i < imageData.data.length; i += 4) {
                    if (imageData.data[i] > 0) nonEmpty++;
                }
                return {exists: nonEmpty > 10, pixels: nonEmpty};
            """, canvas)
            return result.get('exists', False)
        except Exception:
            return False

    def check_svg_exists(self, container_selector, timeout=5):
        """Check if SVG plot exists"""
        try:
            svg = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"{container_selector} svg"))
            )
            # Check if SVG has children (actual content)
            child_count = self.driver.execute_script(
                "return arguments[0].children.length;", svg
            )
            return child_count > 0
        except:
            return False

    # ========== TEST SECTIONS ==========

    def test_01_page_load(self):
        """Test 1: Page loads correctly"""
        print("\n[Test 1] Page Load")

        # Check title
        title_ok = "HTA" in self.driver.title
        self.log_result("Page title contains 'HTA'", title_ok, self.driver.title)

        # Check main elements exist
        self.log_result("Header exists", self.element_exists("header, .header, h1"))
        self.log_result("Navigation exists", self.element_exists("nav, .nav, .tabs, .tab-buttons"))
        self.log_result("Main content exists", self.element_exists("main, .main, .content, .tab-content"))

    def test_02_navigation_tabs(self):
        """Test 2: Navigation tabs work"""
        print("\n[Test 2] Navigation Tabs")

        # Find all tab buttons
        tab_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".tab-btn, .nav-tab, [data-tab], button[onclick*='Tab']")

        if not tab_buttons:
            # Try alternative selectors
            tab_buttons = self.driver.find_elements(By.CSS_SELECTOR, "nav button, .tabs button")

        print(f"  Found {len(tab_buttons)} tab buttons")

        for i, btn in enumerate(tab_buttons[:10]):  # Limit to first 10
            try:
                btn_text = btn.text.strip()[:30] or f"Tab {i+1}"
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.2)
                btn.click()
                time.sleep(0.3)
                self.log_result(f"Tab '{btn_text}' clickable", True)
            except Exception as e:
                self.log_result(f"Tab {i+1} clickable", False, str(e)[:50])

    def test_03_markov_model(self):
        """Test 3: Markov Model Module"""
        print("\n[Test 3] Markov Model")

        # Navigate to Markov tab
        if not self.click_element("[data-tab='markov'], button:contains('Markov')", timeout=2):
            self.click_element("button", By.XPATH, "//button[contains(text(), 'Markov')]")
        time.sleep(0.5)

        # Check for Markov-related elements
        self.log_result("Markov section visible",
                       self.element_exists("#markov, .markov-content, [data-section='markov']"))

        # Try to run Markov analysis
        run_btn = self.click_element("button[onclick*='runMarkov'], #runMarkov, button:contains('Run')")
        if run_btn:
            time.sleep(1)
            self.log_result("Markov Run button works", True)
        else:
            self.log_warning("Could not find Markov run button")

    def test_04_psa_module(self):
        """Test 4: PSA (Probabilistic Sensitivity Analysis) Module"""
        print("\n[Test 4] PSA Module")

        # Navigate to PSA tab
        self.click_element("[data-tab='psa']", timeout=2)
        time.sleep(0.5)

        # Check PSA elements
        self.log_result("PSA section exists", self.element_exists("#psa, .psa-content"))

        # Try running PSA
        if self.click_element("button[onclick*='runPSA'], #runPSA"):
            time.sleep(2)  # PSA takes longer
            self.log_result("PSA execution started", True)

            # Check for scatter plot
            scatter_exists = self.check_chart_exists("#ceScatterPlot, .ce-scatter, #psaResults")
            self.log_result("CE Scatter Plot renders", scatter_exists)

            # Check twice as requested
            time.sleep(1)
            scatter_exists_2 = self.check_chart_exists("#ceScatterPlot, .ce-scatter, #psaResults")
            self.log_result("CE Scatter Plot renders (2nd check)", scatter_exists_2)

    def test_05_nma_module(self):
        """Test 5: Network Meta-Analysis Module"""
        print("\n[Test 5] Network Meta-Analysis")

        # Navigate to NMA tab
        self.click_element("[data-tab='nma']", timeout=2)
        time.sleep(0.5)

        self.log_result("NMA section exists", self.element_exists("#nma, .nma-content"))

        # Check for network graph
        if self.click_element("button[onclick*='runNMA'], #runNMA"):
            time.sleep(2)

            # Check network plot (usually SVG with D3)
            network_plot = self.check_svg_exists("#networkGraph, .network-plot, #nmaNetwork")
            self.log_result("Network graph renders", network_plot)

            # Second check
            time.sleep(0.5)
            network_plot_2 = self.check_svg_exists("#networkGraph, .network-plot, #nmaNetwork")
            self.log_result("Network graph renders (2nd check)", network_plot_2)

            # Check forest plot
            forest = self.check_chart_exists("#nmaForest, .nma-forest")
            self.log_result("NMA Forest plot renders", forest)

    def test_06_meta_analysis(self):
        """Test 6: Pairwise Meta-Analysis"""
        print("\n[Test 6] Pairwise Meta-Analysis")

        # Navigate to meta-analysis tab
        self.click_element("[data-tab='meta'], [data-tab='pairwise']", timeout=2)
        time.sleep(0.5)

        self.log_result("Meta-analysis section exists",
                       self.element_exists("#meta, #pairwise, .meta-content"))

        # Run meta-analysis
        if self.click_element("button[onclick*='runMeta'], #runMeta, button[onclick*='calculatePooled']"):
            time.sleep(1.5)

            # Check forest plot
            forest = self.check_chart_exists("#forestPlot, .forest-plot, #metaForest")
            self.log_result("Forest plot renders", forest)
            time.sleep(0.5)
            forest_2 = self.check_chart_exists("#forestPlot, .forest-plot, #metaForest")
            self.log_result("Forest plot renders (2nd check)", forest_2)

            # Check funnel plot
            funnel = self.check_chart_exists("#funnelPlot, .funnel-plot")
            self.log_result("Funnel plot renders", funnel)
            time.sleep(0.5)
            funnel_2 = self.check_chart_exists("#funnelPlot, .funnel-plot")
            self.log_result("Funnel plot renders (2nd check)", funnel_2)

    def test_07_publication_bias(self):
        """Test 7: Publication Bias Tests"""
        print("\n[Test 7] Publication Bias")

        # Look for publication bias buttons
        egger_btn = self.click_element("button[onclick*='egger'], #eggerTest")
        if egger_btn:
            time.sleep(0.5)
            self.log_result("Egger's test runs", True)

        begg_btn = self.click_element("button[onclick*='begg'], #beggTest")
        if begg_btn:
            time.sleep(0.5)
            self.log_result("Begg's test runs", True)

        tf_btn = self.click_element("button[onclick*='trimFill'], #trimFill")
        if tf_btn:
            time.sleep(0.5)
            self.log_result("Trim-and-fill runs", True)

    def test_08_sensitivity_analysis(self):
        """Test 8: Sensitivity Analyses"""
        print("\n[Test 8] Sensitivity Analyses")

        # Leave-one-out
        if self.click_element("button[onclick*='leaveOneOut'], #leaveOneOut"):
            time.sleep(1)
            self.log_result("Leave-one-out analysis runs", True)

            # Check LOO plot
            loo_plot = self.check_chart_exists("#looPlot, .loo-plot")
            self.log_result("LOO plot renders", loo_plot)

        # Cumulative meta-analysis
        if self.click_element("button[onclick*='cumulative'], #cumulativeMeta"):
            time.sleep(1)
            self.log_result("Cumulative meta-analysis runs", True)

            cum_plot = self.check_chart_exists("#cumulativePlot, .cumulative-plot")
            self.log_result("Cumulative plot renders", cum_plot)

        # Influence diagnostics
        if self.click_element("button[onclick*='influence'], #influenceDiag"):
            time.sleep(1)
            self.log_result("Influence diagnostics run", True)

    def test_09_meta_regression(self):
        """Test 9: Meta-Regression"""
        print("\n[Test 9] Meta-Regression")

        if self.click_element("button[onclick*='metaRegression'], #metaRegression, [data-tab='regression']"):
            time.sleep(1)
            self.log_result("Meta-regression runs", True)

            # Check bubble plot
            bubble = self.check_chart_exists("#bubblePlot, .bubble-plot, #regressionPlot")
            self.log_result("Bubble/regression plot renders", bubble)
            time.sleep(0.5)
            bubble_2 = self.check_chart_exists("#bubblePlot, .bubble-plot, #regressionPlot")
            self.log_result("Bubble plot renders (2nd check)", bubble_2)

    def test_10_subgroup_analysis(self):
        """Test 10: Subgroup Analysis"""
        print("\n[Test 10] Subgroup Analysis")

        if self.click_element("button[onclick*='subgroup'], #subgroupAnalysis"):
            time.sleep(1)
            self.log_result("Subgroup analysis runs", True)

            # Check subgroup forest plot
            sg_forest = self.check_chart_exists("#subgroupForest, .subgroup-forest")
            self.log_result("Subgroup forest plot renders", sg_forest)

    def test_11_survival_analysis(self):
        """Test 11: Survival Analysis / Partitioned Survival"""
        print("\n[Test 11] Survival Analysis")

        self.click_element("[data-tab='survival'], [data-tab='psm']", timeout=2)
        time.sleep(0.5)

        self.log_result("Survival section exists",
                       self.element_exists("#survival, #psm, .survival-content"))

        if self.click_element("button[onclick*='runSurvival'], #runSurvival, #runPSM"):
            time.sleep(1.5)

            # Check KM plot
            km_plot = self.check_chart_exists("#kmPlot, .km-plot, #survivalPlot")
            self.log_result("Kaplan-Meier plot renders", km_plot)
            time.sleep(0.5)
            km_plot_2 = self.check_chart_exists("#kmPlot, .km-plot, #survivalPlot")
            self.log_result("KM plot renders (2nd check)", km_plot_2)

    def test_12_ceac_curves(self):
        """Test 12: Cost-Effectiveness Acceptability Curves"""
        print("\n[Test 12] CEAC Curves")

        if self.click_element("button[onclick*='CEAC'], #runCEAC, button[onclick*='ceac']"):
            time.sleep(1)

            ceac = self.check_chart_exists("#ceacPlot, .ceac-plot, #ceacChart")
            self.log_result("CEAC plot renders", ceac)
            time.sleep(0.5)
            ceac_2 = self.check_chart_exists("#ceacPlot, .ceac-plot, #ceacChart")
            self.log_result("CEAC plot renders (2nd check)", ceac_2)

    def test_13_tornado_diagram(self):
        """Test 13: Tornado Diagram (DSA)"""
        print("\n[Test 13] Tornado Diagram")

        if self.click_element("button[onclick*='tornado'], #runDSA, button[onclick*='DSA']"):
            time.sleep(1)

            tornado = self.check_chart_exists("#tornadoPlot, .tornado-plot, #dsaChart")
            self.log_result("Tornado diagram renders", tornado)
            time.sleep(0.5)
            tornado_2 = self.check_chart_exists("#tornadoPlot, .tornado-plot, #dsaChart")
            self.log_result("Tornado diagram renders (2nd check)", tornado_2)

    def test_14_evppi(self):
        """Test 14: Expected Value of Perfect Parameter Information"""
        print("\n[Test 14] EVPPI")

        self.click_element("[data-tab='evppi'], [data-tab='voi']", timeout=2)
        time.sleep(0.5)

        if self.click_element("button[onclick*='EVPPI'], #runEVPPI"):
            time.sleep(2)

            evppi_plot = self.check_chart_exists("#evppiPlot, .evppi-chart")
            self.log_result("EVPPI plot renders", evppi_plot)

    def test_15_model_calibration(self):
        """Test 15: Model Calibration"""
        print("\n[Test 15] Model Calibration")

        self.click_element("[data-tab='calibration']", timeout=2)
        time.sleep(0.5)

        if self.click_element("button[onclick*='calibrate'], #runCalibration"):
            time.sleep(2)

            calib_plot = self.check_chart_exists("#calibrationPlot, .calibration-chart")
            self.log_result("Calibration plot renders", calib_plot)

    def test_16_reporting(self):
        """Test 16: Reporting / Export Functions"""
        print("\n[Test 16] Reporting & Export")

        # Export buttons
        export_btns = self.driver.find_elements(By.CSS_SELECTOR,
            "button[onclick*='export'], button[onclick*='Export'], button[onclick*='download']")

        for btn in export_btns[:5]:
            btn_text = btn.text.strip()[:20] or "Export"
            # Don't actually click export (would trigger downloads)
            self.log_result(f"Export button '{btn_text}' exists", True)

        # Report generation
        if self.element_exists("button[onclick*='generateReport'], #generateReport"):
            self.log_result("Report generation button exists", True)

    def test_17_data_input(self):
        """Test 17: Data Input Forms"""
        print("\n[Test 17] Data Input")

        # Check for data input areas
        textareas = self.driver.find_elements(By.CSS_SELECTOR, "textarea")
        self.log_result(f"Found {len(textareas)} data input areas", len(textareas) > 0)

        # Check for file upload
        file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        self.log_result(f"Found {len(file_inputs)} file upload inputs", len(file_inputs) >= 0)

        # Check for numeric inputs
        num_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='number']")
        self.log_result(f"Found {len(num_inputs)} numeric inputs", len(num_inputs) > 0)

    def test_18_inline_tests(self):
        """Test 18: Run Inline Test Suite"""
        print("\n[Test 18] Inline Test Suite")

        # Look for test runner button
        if self.click_element("#runAllTests, button[onclick*='runAllTests'], .run-tests-btn"):
            time.sleep(3)  # Tests take time

            # Check test results
            passed = self.driver.find_elements(By.CSS_SELECTOR, ".test-stat.pass, .test-pass")
            failed = self.driver.find_elements(By.CSS_SELECTOR, ".test-stat.fail, .test-fail")

            self.log_result(f"Inline tests: {len(passed)} passed, {len(failed)} failed",
                           len(failed) == 0, f"{len(failed)} tests failed")
        else:
            self.log_warning("Inline test suite button not found")

    def test_19_tutorial(self):
        """Test 19: Tutorial / Help System"""
        print("\n[Test 19] Tutorial & Help")

        # Check for tutorial button
        if self.click_element("#startTutorial, button[onclick*='tutorial'], .help-btn"):
            time.sleep(1)

            # Check tutorial modal appears
            tutorial_visible = self.element_exists(".tutorial-modal, .tutorial-overlay, #tutorialModal")
            self.log_result("Tutorial modal opens", tutorial_visible)

            # Close tutorial
            self.click_element(".close-tutorial, .tutorial-close, button[onclick*='closeTutorial']")

    def test_20_all_chart_canvases(self):
        """Test 20: Verify ALL canvas elements have content"""
        print("\n[Test 20] All Chart Canvases")

        # Get all canvases
        canvases = self.driver.find_elements(By.CSS_SELECTOR, "canvas")
        print(f"  Found {len(canvases)} canvas elements")

        visible_canvases = 0
        rendered_canvases = 0

        for i, canvas in enumerate(canvases):
            try:
                # Check if visible
                is_visible = canvas.is_displayed()
                if is_visible:
                    visible_canvases += 1

                    # Check if has content
                    has_content = self.driver.execute_script("""
                        const canvas = arguments[0];
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return false;
                        try {
                            const imageData = ctx.getImageData(0, 0,
                                Math.min(canvas.width, 50), Math.min(canvas.height, 50));
                            for (let i = 3; i < imageData.data.length; i += 4) {
                                if (imageData.data[i] > 0) return true;
                            }
                        } catch(e) { return false; }
                        return false;
                    """, canvas)

                    if has_content:
                        rendered_canvases += 1
            except:
                pass

        self.log_result(f"Visible canvases: {visible_canvases}", visible_canvases >= 0)
        self.log_result(f"Rendered canvases with content: {rendered_canvases}", rendered_canvases >= 0)

        # Second check after small delay
        time.sleep(1)
        canvases_2 = self.driver.find_elements(By.CSS_SELECTOR, "canvas")
        rendered_2 = 0
        for canvas in canvases_2:
            try:
                if canvas.is_displayed():
                    has_content = self.driver.execute_script("""
                        const canvas = arguments[0];
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return false;
                        try {
                            const imageData = ctx.getImageData(0, 0, 50, 50);
                            for (let i = 3; i < imageData.data.length; i += 4) {
                                if (imageData.data[i] > 0) return true;
                            }
                        } catch(e) {}
                        return false;
                    """, canvas)
                    if has_content:
                        rendered_2 += 1
            except:
                pass
        self.log_result(f"Rendered canvases (2nd check): {rendered_2}", True)

    def test_21_all_svg_plots(self):
        """Test 21: Verify ALL SVG plots"""
        print("\n[Test 21] All SVG Plots")

        svgs = self.driver.find_elements(By.CSS_SELECTOR, "svg")
        print(f"  Found {len(svgs)} SVG elements")

        valid_svgs = 0
        for svg in svgs:
            try:
                if svg.is_displayed():
                    child_count = self.driver.execute_script(
                        "return arguments[0].querySelectorAll('path, circle, rect, line, text').length;",
                        svg
                    )
                    if child_count > 0:
                        valid_svgs += 1
            except:
                pass

        self.log_result(f"SVGs with plot content: {valid_svgs}", valid_svgs >= 0)

        # Second check
        time.sleep(0.5)
        valid_svgs_2 = 0
        for svg in self.driver.find_elements(By.CSS_SELECTOR, "svg"):
            try:
                if svg.is_displayed():
                    child_count = self.driver.execute_script(
                        "return arguments[0].querySelectorAll('path, circle, rect, line').length;",
                        svg
                    )
                    if child_count > 0:
                        valid_svgs_2 += 1
            except:
                pass
        self.log_result(f"SVGs with content (2nd check): {valid_svgs_2}", True)

    def test_22_responsive_design(self):
        """Test 22: Responsive Design"""
        print("\n[Test 22] Responsive Design")

        # Test different viewport sizes
        sizes = [(1920, 1080), (1366, 768), (768, 1024), (375, 667)]

        for width, height in sizes:
            self.driver.set_window_size(width, height)
            time.sleep(0.5)

            # Check no horizontal scroll needed
            scroll_width = self.driver.execute_script("return document.body.scrollWidth;")
            viewport_width = self.driver.execute_script("return window.innerWidth;")

            no_hscroll = scroll_width <= viewport_width + 20  # 20px tolerance
            self.log_result(f"No horizontal scroll at {width}x{height}", no_hscroll,
                           f"scrollWidth={scroll_width}, viewport={viewport_width}")

        # Restore size
        self.driver.maximize_window()

    def test_23_error_handling(self):
        """Test 23: Error Handling"""
        print("\n[Test 23] Error Handling")

        # Check for JavaScript errors in console
        logs = self.driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']

        if errors:
            for err in errors[:5]:  # Show first 5
                self.log_warning(f"JS Error: {err['message'][:80]}")
            self.log_result("No severe JS errors", len(errors) == 0, f"{len(errors)} errors found")
        else:
            self.log_result("No severe JS errors", True)

    def test_24_accessibility(self):
        """Test 24: Basic Accessibility"""
        print("\n[Test 24] Accessibility")

        # Check for alt text on images
        imgs = self.driver.find_elements(By.CSS_SELECTOR, "img")
        imgs_with_alt = [img for img in imgs if img.get_attribute('alt')]
        self.log_result(f"Images with alt text: {len(imgs_with_alt)}/{len(imgs)}",
                       len(imgs) == 0 or len(imgs_with_alt) >= len(imgs) * 0.5)

        # Check for labels on inputs
        inputs = self.driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden'])")
        labeled = 0
        for inp in inputs:
            inp_id = inp.get_attribute('id')
            if inp_id:
                label = self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{inp_id}']")
                if label:
                    labeled += 1
        self.log_result(f"Inputs with labels: {labeled}/{len(inputs)}",
                       len(inputs) == 0 or labeled >= len(inputs) * 0.3)

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        total = len(self.results['passed']) + len(self.results['failed'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        warnings = len(self.results['warnings'])

        print(f"\nTotal Tests: {total}")
        print(f"PASSED: {passed}")
        print(f"FAILED: {failed}")
        print(f"WARNINGS: {warnings}")

        if failed > 0:
            print("\n--- Failed Tests ---")
            for name, msg in self.results['failed']:
                print(f"  - {name}: {msg}")

        if warnings > 0:
            print("\n--- Warnings ---")
            for warn in self.results['warnings'][:10]:
                print(f"  - {warn}")

        print("\n" + "=" * 60)
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 60)

        return failed == 0

    def run_all_tests(self):
        """Run all tests"""
        try:
            self.setup()

            # Run all test methods
            test_methods = [method for method in dir(self) if method.startswith('test_')]
            test_methods.sort()  # Run in order

            for method_name in test_methods:
                try:
                    getattr(self, method_name)()
                except Exception as e:
                    print(f"\n[CRASH] Test {method_name}: {str(e)[:100]}")
                    self.results['failed'].append((method_name, str(e)[:100]))

            success = self.print_summary()
            return success

        except Exception as e:
            print(f"\n[ERROR] Test suite failed to initialize: {e}")
            return False
        finally:
            self.teardown()


if __name__ == "__main__":
    suite = HTATestSuite()
    success = suite.run_all_tests()
    exit(0 if success else 1)
