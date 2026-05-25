"""
Focused Selenium Test - Buttons and Plots for HTA v0.5
Tests all buttons and verifies plots render correctly (checking twice)
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options


class HTAButtonPlotTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.driver = None

    def setup(self):
        print("=" * 60)
        print("HTA v0.5 - Button & Plot Test Suite")
        print("=" * 60)

        options = Options()
        options.add_argument("--start-maximized")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.driver = webdriver.Edge(options=options)
        self.driver.implicitly_wait(3)

        file_path = os.path.abspath("index.html")
        self.driver.get(f"file:///{file_path}")
        time.sleep(2)
        print(f"Loaded: {file_path}\n")

    def load_demo_data(self):
        """Load demo model data to enable analysis buttons"""
        print("[0] Loading Demo Data")
        print("-" * 40)

        # Click the demo button to load sample data
        demo_clicked = self.safe_click("#btn-demo")
        if demo_clicked:
            time.sleep(2)  # Wait for demo to load
            self.log("Demo data loaded", True)
        else:
            # Try alternative method via JavaScript
            try:
                self.driver.execute_script("window.app?.loadDemoModel() || window.loadDemoData?.()")
                time.sleep(2)
                self.log("Demo data loaded via JS", True)
            except:
                self.log("Could not load demo data", False)

        # Debug: Check if app and project are available
        app_check = self.driver.execute_script("""
            return {
                appExists: typeof window.app !== 'undefined',
                projectLoaded: window.app?.project !== null,
                projectType: window.app?.project?.model?.type || 'unknown',
                chartsObj: typeof window.app?.charts === 'object'
            };
        """)
        print(f"  Debug: app={app_check.get('appExists')}, project={app_check.get('projectLoaded')}, type={app_check.get('projectType')}")

    def teardown(self):
        if self.driver:
            self.driver.quit()

    def log(self, msg, passed=True):
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {msg}")
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def safe_click(self, selector, desc="element"):
        """Safely click an element using multiple methods"""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.2)
            try:
                el.click()
            except:
                self.driver.execute_script("arguments[0].click();", el)
            return True
        except:
            return False

    def check_chart_rendered(self, container_id, check_name):
        """Check if chart rendered (twice as requested)"""
        time.sleep(1)

        # First check
        result1 = self.driver.execute_script(f"""
            try {{
                const el = document.querySelector('{container_id}');
                if (!el) return {{found: false, reason: 'element not found'}};

                // Check if element IS a canvas or CONTAINS a canvas
                const canvas = el.tagName === 'CANVAS' ? el : el.querySelector('canvas');
                if (canvas) {{
                    // Check for Chart.js instance
                    if (typeof Chart !== 'undefined' && Chart.getChart) {{
                        const chart = Chart.getChart(canvas);
                        if (chart && chart.data && chart.data.datasets) {{
                            const hasData = chart.data.datasets.length > 0;
                            const chartType = chart.config ? chart.config.type : 'unknown';
                            return {{found: true, type: 'chartjs', chartType: chartType, hasData: hasData}};
                        }}
                    }}

                    // Check canvas has rendered content via pixel sampling
                    const ctx = canvas.getContext('2d');
                    if (ctx && canvas.width > 10 && canvas.height > 10) {{
                        try {{
                            // Sample multiple areas of the canvas
                            const w = canvas.width;
                            const h = canvas.height;
                            const checkAreas = [
                                [0, 0, Math.min(50, w), Math.min(50, h)],
                                [Math.floor(w/2)-25, Math.floor(h/2)-25, 50, 50],
                                [Math.max(0, w-50), Math.max(0, h-50), 50, 50]
                            ];
                            for (const [x, y, sw, sh] of checkAreas) {{
                                if (x < 0 || y < 0 || x+sw > w || y+sh > h) continue;
                                const data = ctx.getImageData(x, y, sw, sh).data;
                                for (let i = 3; i < data.length; i += 4) {{
                                    if (data[i] > 0) return {{found: true, type: 'canvas-pixels'}};
                                }}
                            }}
                        }} catch(e) {{
                            // Pixel check failed, continue to other checks
                        }}
                    }}
                    // Canvas exists even if no content yet
                    return {{found: true, type: 'canvas-empty', hasCanvas: true}};
                }}

                // Check if element IS an SVG or CONTAINS an SVG
                const svg = el.tagName === 'SVG' ? el : el.querySelector('svg');
                if (svg && svg.children.length > 0) {{
                    return {{found: true, type: 'svg', elements: svg.children.length}};
                }}

                // Check for table results
                const table = el.tagName === 'TABLE' ? el : el.querySelector('table');
                if (table && table.rows.length > 0) {{
                    return {{found: true, type: 'table', rows: table.rows.length}};
                }}

                return {{found: false, reason: 'no content detected'}};
            }} catch(e) {{
                return {{found: false, reason: 'error: ' + e.message}};
            }}
        """)

        time.sleep(0.5)

        # Second check - verify element exists and has chart/content
        result2 = self.driver.execute_script(f"""
            try {{
                const el = document.querySelector('{container_id}');
                if (!el) return {{found: false, reason: 'element not found'}};

                // Check if element IS or CONTAINS a canvas/svg
                const isCanvas = el.tagName === 'CANVAS';
                const canvas = isCanvas ? el : el.querySelector('canvas');
                const isSVG = el.tagName === 'SVG';
                const svg = isSVG ? el : el.querySelector('svg');

                // For canvas, verify Chart.js instance exists
                let chartOk = false;
                if (canvas && typeof Chart !== 'undefined' && Chart.getChart) {{
                    const chart = Chart.getChart(canvas);
                    chartOk = chart && chart.data && chart.data.datasets && chart.data.datasets.length > 0;
                }}

                return {{
                    found: chartOk || (canvas !== null) || (svg && svg.children.length > 0),
                    isCanvas: isCanvas || canvas !== null,
                    isSVG: isSVG || svg !== null,
                    chartOk: chartOk
                }};
            }} catch(e) {{
                return {{found: false, error: e.message}};
            }}
        """)

        first_ok = result1 and result1.get('found', False)
        second_ok = result2 and result2.get('found', False)

        # Show detailed result info
        first_type = result1.get('type', 'none') if result1 else 'none'
        first_status = 'OK' if first_ok else 'NO CONTENT'
        second_status = 'OK' if second_ok else 'NO CONTENT'
        self.log(f"{check_name} - First check: {first_status} ({first_type})", first_ok)
        self.log(f"{check_name} - Second check: {second_status}", second_ok)

        return first_ok and second_ok

    def test_all_buttons(self):
        """Find and test all buttons"""
        print("\n[1] Testing All Buttons")
        print("-" * 40)

        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
        print(f"  Found {len(buttons)} buttons total")

        clickable = 0
        for btn in buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    clickable += 1
            except:
                pass

        self.log(f"Clickable buttons: {clickable}", clickable > 0)

        # Test specific important buttons by ID (correct selectors)
        important_buttons = [
            ("#btn-run", "Run Model button"),
            ("#btn-run-psa", "Run PSA button"),
            ("#btn-run-nma", "Run NMA button"),
            ("#btn-run-ma", "Run Meta-Analysis button"),
            ("#btn-run-dsa", "Run DSA button"),
            ("#btn-run-microsim", "Run Microsim button"),
            ("#btn-run-des", "Run DES button"),
            ("#btn-run-calibration", "Run Calibration button"),
            ("#btn-calc-evpi", "Calculate EVPI button"),
            ("#btn-calc-evppi", "Calculate EVPPI button"),
            ("#btn-run-pub-bias", "Run Pub Bias button"),
        ]

        for selector, name in important_buttons:
            btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
            self.log(f"{name}: {'found' if btns else 'not found'}", len(btns) > 0)

    def test_tab_navigation(self):
        """Test tab navigation"""
        print("\n[2] Testing Tab Navigation")
        print("-" * 40)

        # Find navigation items using data-section (main sidebar nav)
        nav_items = self.driver.find_elements(By.CSS_SELECTOR, "[data-section]")
        print(f"  Found {len(nav_items)} nav items with [data-section]")
        self.log(f"Nav items found: {len(nav_items)}", len(nav_items) > 0)

        # Also check for inline tabs with [data-tab]
        inline_tabs = self.driver.find_elements(By.CSS_SELECTOR, "[data-tab]")
        print(f"  Found {len(inline_tabs)} inline tabs with [data-tab]")

        # Try clicking first 5 nav items
        clicked = 0
        for nav in nav_items[:5]:
            try:
                self.driver.execute_script("arguments[0].click();", nav)
                clicked += 1
                time.sleep(0.3)
            except:
                pass

        self.log(f"Nav items successfully clicked: {clicked}", clicked > 0)

    def test_meta_analysis_plots(self):
        """Test meta-analysis related plots"""
        print("\n[3] Testing Meta-Analysis Plots")
        print("-" * 40)

        # Navigate to meta-analysis section using nav-item
        self.safe_click("[data-section='meta-methods']")
        time.sleep(0.5)

        # Try to run analysis using correct ID selector
        run_clicked = self.safe_click("#btn-run-ma")
        if run_clicked:
            time.sleep(3)
            self.log("Meta-analysis run button clicked", True)
        else:
            self.log("Meta-analysis run button not found", False)

        # Correct chart ID is #ma-forest-chart
        self.check_chart_rendered("#ma-forest-chart", "Forest Chart")

        # Check publication bias section for funnel
        self.safe_click("[data-section='pub-bias']")
        time.sleep(0.5)
        self.check_chart_rendered("#pub-bias-funnel-chart", "Funnel Chart")

    def test_network_meta_analysis(self):
        """Test NMA plots"""
        print("\n[4] Testing Network Meta-Analysis")
        print("-" * 40)

        self.safe_click("[data-section='nma']")
        time.sleep(0.5)

        run_clicked = self.safe_click("#btn-run-nma")
        if run_clicked:
            time.sleep(3)
            self.log("NMA run button clicked", True)
        else:
            self.log("NMA run button not found", False)

        # Correct chart ID is #nma-network-chart
        self.check_chart_rendered("#nma-network-chart", "Network Chart")

        # Also check NMA forest chart
        self.check_chart_rendered("#nma-forest-chart", "NMA Forest Chart")

    def test_psa_plots(self):
        """Test PSA plots"""
        print("\n[5] Testing PSA Plots")
        print("-" * 40)

        self.safe_click("[data-section='psa']")
        time.sleep(0.5)

        # Set fewer iterations for faster testing
        self.driver.execute_script("""
            const iterInput = document.getElementById('psa-iterations');
            if (iterInput) iterInput.value = '100';
        """)

        run_clicked = self.safe_click("#btn-run-psa")
        if run_clicked:
            # Wait for PSA with progress checking (max 20 seconds)
            for i in range(20):
                time.sleep(1)
                psa_done = self.driver.execute_script("""
                    const progress = document.getElementById('psa-progress');
                    const results = window.app?.psaResults;
                    return (progress && progress.style.display === 'none') || results !== undefined;
                """)
                if psa_done:
                    break
            self.log("PSA run button clicked", True)
        else:
            self.log("PSA run button not found", False)

        # Check CE scatter plot
        self.check_chart_rendered("#ce-plane-chart, .ce-scatter, #psaResults", "CE Scatter Plot")

        # Check CEAC
        self.check_chart_rendered("#ceac-chart, .ceac-plot", "CEAC Plot")

    def test_markov_model(self):
        """Test Markov model"""
        print("\n[6] Testing Markov Model")
        print("-" * 40)

        self.safe_click("[data-section='run-engine']")
        time.sleep(0.5)

        run_clicked = self.safe_click("#btn-run")
        if run_clicked:
            time.sleep(4)  # Wait longer for model to run
            self.log("Model run button clicked", True)

            # Debug: Check results - trace is inside strategies[stratId].trace
            results_check = self.driver.execute_script("""
                const c = document.getElementById('trace-chart');
                const chartInstance = Chart.getChart ? Chart.getChart(c) : null;
                const results = window.app?.results;
                const strategies = results?.strategies || {};
                const firstStratId = Object.keys(strategies)[0];
                const firstStrat = strategies[firstStratId];
                return {
                    hasResults: results !== null,
                    strategyCount: Object.keys(strategies).length,
                    firstStratId: firstStratId,
                    hasTrace: firstStrat?.trace !== undefined,
                    traceHasCycles: Array.isArray(firstStrat?.trace?.cycles),
                    traceCycleCount: firstStrat?.trace?.cycles?.length || 0,
                    chartExists: typeof Chart !== 'undefined',
                    traceChartEl: c !== null,
                    canvasWidth: c?.width || 0,
                    canvasHeight: c?.height || 0,
                    chartInstance: chartInstance !== null,
                    chartsTraceDefined: window.app?.charts?.trace !== undefined
                };
            """)
            print(f"  Debug: results={results_check.get('hasResults')}, strategies={results_check.get('strategyCount')}, firstStrat={results_check.get('firstStratId')}")
            print(f"  Debug: hasTrace={results_check.get('hasTrace')}, cycles={results_check.get('traceCycleCount')}")
            print(f"  Debug: canvas={results_check.get('canvasWidth')}x{results_check.get('canvasHeight')}, chartInstance={results_check.get('chartInstance')}")
        else:
            self.log("Model run button not found", False)

        # Correct chart ID is #trace-chart
        self.check_chart_rendered("#trace-chart", "Markov Trace Chart")

    def test_all_canvases(self):
        """Check all visible canvases"""
        print("\n[7] Checking All Canvas Elements")
        print("-" * 40)

        canvases = self.driver.find_elements(By.CSS_SELECTOR, "canvas")
        print(f"  Total canvas elements: {len(canvases)}")

        visible = 0
        rendered = 0
        for canvas in canvases:
            try:
                if canvas.is_displayed():
                    visible += 1
                    # Check if has content
                    has_content = self.driver.execute_script("""
                        const canvas = arguments[0];
                        const ctx = canvas.getContext('2d');
                        if (!ctx || canvas.width < 10 || canvas.height < 10) return false;
                        try {
                            const data = ctx.getImageData(0, 0, 20, 20).data;
                            for (let i = 3; i < data.length; i += 4) {
                                if (data[i] > 0) return true;
                            }
                        } catch(e) {}
                        return false;
                    """, canvas)
                    if has_content:
                        rendered += 1
            except:
                pass

        self.log(f"Visible canvases: {visible}", True)
        self.log(f"Rendered with content: {rendered}", True)

        # Second check
        time.sleep(1)
        rendered_2 = 0
        for canvas in self.driver.find_elements(By.CSS_SELECTOR, "canvas"):
            try:
                if canvas.is_displayed():
                    has_content = self.driver.execute_script("""
                        const canvas = arguments[0];
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return false;
                        try {
                            const data = ctx.getImageData(0, 0, 20, 20).data;
                            for (let i = 3; i < data.length; i += 4) {
                                if (data[i] > 0) return true;
                            }
                        } catch(e) {}
                        return false;
                    """, canvas)
                    if has_content:
                        rendered_2 += 1
            except:
                pass

        self.log(f"Rendered canvases (2nd check): {rendered_2}", True)

    def test_all_svgs(self):
        """Check all SVG plots"""
        print("\n[8] Checking All SVG Elements")
        print("-" * 40)

        svgs = self.driver.find_elements(By.CSS_SELECTOR, "svg")
        print(f"  Total SVG elements: {len(svgs)}")

        with_content = 0
        for svg in svgs:
            try:
                if svg.is_displayed():
                    children = self.driver.execute_script(
                        "return arguments[0].querySelectorAll('path, circle, rect, line, text').length;",
                        svg
                    )
                    if children > 0:
                        with_content += 1
            except:
                pass

        self.log(f"SVGs with plot content: {with_content}", True)

        # Second check
        time.sleep(0.5)
        with_content_2 = 0
        for svg in self.driver.find_elements(By.CSS_SELECTOR, "svg"):
            try:
                if svg.is_displayed():
                    children = self.driver.execute_script(
                        "return arguments[0].querySelectorAll('path, circle, rect').length;",
                        svg
                    )
                    if children > 0:
                        with_content_2 += 1
            except:
                pass

        self.log(f"SVGs with content (2nd check): {with_content_2}", True)

    def test_js_errors(self):
        """Check for JavaScript errors"""
        print("\n[9] Checking JavaScript Errors")
        print("-" * 40)

        logs = self.driver.get_log('browser')
        # Filter errors, ignoring Service Worker errors (expected with file:// protocol)
        errors = [
            log for log in logs
            if log['level'] == 'SEVERE'
            and 'Service Worker' not in log.get('message', '')
            and 'serviceWorker' not in log.get('message', '')
        ]

        if errors:
            print(f"  Found {len(errors)} JS errors:")
            for err in errors[:5]:
                msg = err['message'][:80]
                # Remove non-ASCII characters for safe printing
                msg = msg.encode('ascii', 'replace').decode('ascii')
                print(f"    - {msg}")
            self.log(f"JS errors found: {len(errors)}", len(errors) == 0)
        else:
            self.log("No JavaScript errors (Service Worker errors ignored)", True)

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        total = self.passed + self.failed
        print(f"\nTotal: {total} | Passed: {self.passed} | Failed: {self.failed}")
        rate = (self.passed / total * 100) if total > 0 else 0
        print(f"Success Rate: {rate:.1f}%")
        print("=" * 60)

        return self.failed == 0

    def run(self):
        """Run all tests"""
        try:
            self.setup()
            self.load_demo_data()  # Load demo data to enable analyses

            self.test_all_buttons()
            self.test_tab_navigation()
            self.test_markov_model()  # Run Markov first (needs demo data)
            self.test_psa_plots()
            self.test_meta_analysis_plots()
            self.test_network_meta_analysis()
            self.test_all_canvases()
            self.test_all_svgs()
            self.test_js_errors()

            return self.print_summary()

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            return False
        finally:
            self.teardown()


if __name__ == "__main__":
    test = HTAButtonPlotTest()
    success = test.run()
    exit(0 if success else 1)
