"""
Comprehensive Selenium Test for HTA Meta-Analysis Engine
Tests all major features and statistical methods
"""

import time
import json
import sys
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile
from _hta_url import hta_index_url, hta_index_path

# Reconfigure stdout for Unicode support
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def create_driver():
    """Create headless Edge driver"""
    options = EdgeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--remote-debugging-port=9222')
    temp = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={temp}')

    try:
        return webdriver.Edge(options=options)
    except:
        # Fallback to Chrome if Edge fails
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        temp2 = tempfile.mkdtemp()
        chrome_options.add_argument(f'--user-data-dir={temp2}')
        return webdriver.Chrome(options=chrome_options)

def test_section(name):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print('='*60)

def test_result(name, passed, details=""):
    """Print test result"""
    status = "PASS" if passed else "FAIL"
    icon = "[OK]" if passed else "[X]"
    print(f"  {icon} {name}: {status}")
    if details:
        print(f"      {details}")
    return passed

def run_tests():
    print("\n" + "="*60)
    print("  HTA META-ANALYSIS ENGINE - COMPREHENSIVE SELENIUM TEST")
    print("="*60)

    driver = create_driver()
    driver.get(hta_index_url())
    time.sleep(3)

    passed = 0
    failed = 0

    # ================================================================
    # SECTION 1: PAGE LOAD AND INITIALIZATION
    # ================================================================
    test_section("1. PAGE LOAD & INITIALIZATION")

    # Check page title
    try:
        title = driver.title
        if test_result("Page loads", bool(title), f"Title: {title[:50]}..."):
            passed += 1
        else:
            failed += 1
    except Exception as e:
        test_result("Page loads", False, str(e))
        failed += 1

    # Check main classes exist
    classes_to_check = [
        ('MetaAnalysisMethods', 'Core pairwise MA'),
        ('NetworkMetaAnalysis', 'Network MA'),
        ('HKSJAdjustment', 'HKSJ adjustment'),
        ('CopasSelectionModel', 'Copas selection')
    ]

    for cls, desc in classes_to_check:
        try:
            exists = driver.execute_script(f'return typeof {cls} !== "undefined"')
            if test_result(f"{desc} class exists", exists):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            test_result(f"{desc} class exists", False, str(e))
            failed += 1

    # ================================================================
    # SECTION 2: PAIRWISE META-ANALYSIS
    # ================================================================
    test_section("2. PAIRWISE META-ANALYSIS")

    # Test pooled effect calculation
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods({ method: 'DL' });
            const studies = [
                { effect: 0.5, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.4, se: 0.12 },
                { effect: 0.7, se: 0.2 },
                { effect: 0.55, se: 0.11 }
            ];
            return ma.calculatePooledEffect(studies);
        ''')

        if result and 'fixed' in result and 'random' in result:
            test_result("Pooled effect calculation", True,
                f"Fixed: {result['fixed']['effect']:.4f}, Random: {result['random']['effect']:.4f}")
            passed += 1

            # Check heterogeneity
            if 'heterogeneity' in result:
                het = result['heterogeneity']
                test_result("Heterogeneity statistics", True,
                    f"Q={het['Q']:.2f}, I2={het['I2']:.1f}%, tau2={het['tauSquared']:.4f}")
                passed += 1
            else:
                test_result("Heterogeneity statistics", False)
                failed += 1
        else:
            test_result("Pooled effect calculation", False)
            failed += 1
    except Exception as e:
        test_result("Pooled effect calculation", False, str(e))
        failed += 1

    # Test different estimators
    for method in ['DL', 'REML', 'PM', 'EB']:
        try:
            result = driver.execute_script(f'''
                const ma = new MetaAnalysisMethods({{ method: '{method}' }});
                const studies = [
                    {{ effect: 0.5, se: 0.1 }},
                    {{ effect: 0.6, se: 0.15 }},
                    {{ effect: 0.4, se: 0.12 }}
                ];
                const r = ma.calculatePooledEffect(studies);
                return {{ effect: r.random.effect, tau2: r.heterogeneity.tauSquared }};
            ''')
            if test_result(f"{method} estimator", result is not None,
                f"effect={result['effect']:.4f}, tau2={result['tau2']:.6f}"):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            test_result(f"{method} estimator", False, str(e))
            failed += 1

    # ================================================================
    # SECTION 3: PUBLICATION BIAS TESTS
    # ================================================================
    test_section("3. PUBLICATION BIAS METHODS")

    # Egger's test
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.8, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.9, se: 0.08 },
                { effect: 0.5, se: 0.2 },
                { effect: 0.7, se: 0.12 }
            ];
            return ma.eggerTest(studies);
        ''')
        if result and 'intercept' in result:
            test_result("Egger's test", True,
                f"intercept={result['intercept']:.3f}, p={result['pValue']:.4f}")
            passed += 1
        else:
            test_result("Egger's test", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Egger's test", False, str(e))
        failed += 1

    # Begg's test
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.8, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.9, se: 0.08 },
                { effect: 0.5, se: 0.2 },
                { effect: 0.7, se: 0.12 }
            ];
            return ma.beggTest(studies);
        ''')
        if result and 'tau' in result:
            test_result("Begg's test", True,
                f"tau={result['tau']:.3f}, p={result['pValue']:.4f}")
            passed += 1
        else:
            test_result("Begg's test", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Begg's test", False, str(e))
        failed += 1

    # Trim and Fill
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.8, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.9, se: 0.08 },
                { effect: 0.5, se: 0.2 },
                { effect: 0.7, se: 0.12 }
            ];
            return ma.trimAndFill(studies);
        ''')
        if result and 'nMissing' in result:
            test_result("Trim-and-Fill", True,
                f"missing={result['nMissing']}, adjusted={result['adjusted']['effect']:.4f}")
            passed += 1
        else:
            test_result("Trim-and-Fill", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Trim-and-Fill", False, str(e))
        failed += 1

    # Selection model
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.8, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.9, se: 0.08 },
                { effect: 0.5, se: 0.2 },
                { effect: 0.7, se: 0.12 },
                { effect: 0.65, se: 0.18 }
            ];
            return ma.selectionModel(studies);
        ''')
        if result and 'adjusted' in result:
            test_result("Selection model", True,
                f"adjusted={result['adjusted']['effect']:.4f}, weights: sig={result['selectionWeights']['significant']:.2f}")
            passed += 1
        else:
            test_result("Selection model", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Selection model", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 4: SENSITIVITY ANALYSES
    # ================================================================
    test_section("4. SENSITIVITY ANALYSES")

    # Leave-one-out
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.5, se: 0.1, label: 'Study 1' },
                { effect: 0.6, se: 0.15, label: 'Study 2' },
                { effect: 0.4, se: 0.12, label: 'Study 3' },
                { effect: 0.7, se: 0.2, label: 'Study 4' }
            ];
            return ma.leaveOneOut(studies);
        ''')
        if result and 'results' in result:
            test_result("Leave-one-out analysis", True,
                f"n_results={len(result['results'])}, robust={result['isRobust']}")
            passed += 1
        else:
            test_result("Leave-one-out analysis", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Leave-one-out analysis", False, str(e))
        failed += 1

    # Influence diagnostics
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.5, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.4, se: 0.12 },
                { effect: 0.7, se: 0.2 },
                { effect: 0.55, se: 0.11 }
            ];
            return ma.influenceDiagnostics(studies);
        ''')
        if result and 'diagnostics' in result:
            test_result("Influence diagnostics", True,
                f"outliers={result['summary']['nOutliers']}, influential={result['summary']['nInfluential']}")
            passed += 1
        else:
            test_result("Influence diagnostics", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Influence diagnostics", False, str(e))
        failed += 1

    # Cumulative MA
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.5, se: 0.1, year: 2010 },
                { effect: 0.6, se: 0.15, year: 2012 },
                { effect: 0.4, se: 0.12, year: 2015 },
                { effect: 0.7, se: 0.2, year: 2018 }
            ];
            return ma.cumulativeMetaAnalysis(studies, 'year');
        ''')
        if result and 'results' in result:
            test_result("Cumulative meta-analysis", True,
                f"n_steps={len(result['results'])}")
            passed += 1
        else:
            test_result("Cumulative meta-analysis", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Cumulative meta-analysis", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 5: META-REGRESSION & SUBGROUPS
    # ================================================================
    test_section("5. META-REGRESSION & SUBGROUPS")

    # Meta-regression
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.5, se: 0.1, moderator: 1 },
                { effect: 0.6, se: 0.15, moderator: 2 },
                { effect: 0.4, se: 0.12, moderator: 1.5 },
                { effect: 0.7, se: 0.2, moderator: 3 },
                { effect: 0.55, se: 0.11, moderator: 2.5 }
            ];
            return ma.metaRegression(studies, ['moderator']);
        ''')
        if result and 'coefficients' in result and len(result['coefficients']) >= 2:
            # coefficients is an array: [intercept, moderator, ...]
            intercept = result['coefficients'][0]
            moderator = result['coefficients'][1]
            test_result("Meta-regression", True,
                f"intercept={intercept['estimate']:.4f}, slope={moderator['estimate']:.4f}")
            passed += 1
        else:
            test_result("Meta-regression", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Meta-regression", False, str(e))
        failed += 1

    # Subgroup analysis
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            const studies = [
                { effect: 0.5, se: 0.1, group: 'A' },
                { effect: 0.6, se: 0.15, group: 'A' },
                { effect: 0.8, se: 0.12, group: 'B' },
                { effect: 0.9, se: 0.2, group: 'B' }
            ];
            return ma.subgroupAnalysis(studies, 'group');
        ''')
        if result and 'subgroups' in result and 'betweenGroupHeterogeneity' in result:
            bg = result['betweenGroupHeterogeneity']
            test_result("Subgroup analysis", True,
                f"Q_between={bg['Q']:.4f}, p={bg['pValue']:.4f}")
            passed += 1
        else:
            test_result("Subgroup analysis", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Subgroup analysis", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 6: HKSJ ADJUSTMENT
    # ================================================================
    test_section("6. HKSJ ADJUSTMENT")

    try:
        result = driver.execute_script('''
            const hksj = new HKSJAdjustment();
            const studies = [
                { effect: 0.5, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.4, se: 0.12 },
                { effect: 0.7, se: 0.2 }
            ];
            const tauSq = 0.01;
            const pooled = 0.55;
            return hksj.adjust(studies, tauSq, pooled);
        ''')
        if result and 'ci_lower' in result:
            test_result("HKSJ adjustment", True,
                f"CI=[{result['ci_lower']:.4f}, {result['ci_upper']:.4f}], df={result['df']}")
            passed += 1
        else:
            test_result("HKSJ adjustment", False, str(result))
            failed += 1
    except Exception as e:
        test_result("HKSJ adjustment", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 7: COPAS SELECTION MODEL
    # ================================================================
    test_section("7. COPAS SELECTION MODEL")

    try:
        result = driver.execute_script('''
            const copas = new CopasSelectionModel();
            const studies = [
                { effect: 0.8, se: 0.1 },
                { effect: 0.6, se: 0.15 },
                { effect: 0.9, se: 0.08 },
                { effect: 0.5, se: 0.2 },
                { effect: 0.7, se: 0.12 },
                { effect: 0.65, se: 0.18 }
            ];
            return copas.fit(studies, { gridPoints: 10 });
        ''')
        if result and 'adjusted' in result:
            test_result("Copas model fit", True,
                f"adjusted={result['adjusted']['effect']:.4f}, missing~{result['missingStudies']['estimated']}")

            # Check t-distribution CI
            if 'df' in result['adjusted']:
                test_result("Copas uses t-distribution", True,
                    f"df={result['adjusted']['df']}")
                passed += 1
            else:
                test_result("Copas uses t-distribution", False)
                failed += 1
            passed += 1
        else:
            test_result("Copas model fit", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Copas model fit", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 8: NETWORK META-ANALYSIS
    # ================================================================
    test_section("8. NETWORK META-ANALYSIS")

    # NMA setup
    try:
        result = driver.execute_script('''
            const nma = new NetworkMetaAnalysis({ method: 'frequentist' });
            const data = [
                { study: 'S1', treatment: 'A', n: 100, events: 20 },
                { study: 'S1', treatment: 'B', n: 100, events: 15 },
                { study: 'S2', treatment: 'B', n: 150, events: 30 },
                { study: 'S2', treatment: 'C', n: 150, events: 40 },
                { study: 'S3', treatment: 'A', n: 120, events: 25 },
                { study: 'S3', treatment: 'C', n: 120, events: 35 }
            ];
            nma.setData(data, 'binary');
            return {
                treatments: nma.treatments,
                studies: nma.studies,
                nContrasts: nma.contrasts ? nma.contrasts.length : 0
            };
        ''')
        if result and len(result['treatments']) == 3:
            test_result("NMA data setup", True,
                f"treatments={result['treatments']}, studies={len(result['studies'])}")
            passed += 1
        else:
            test_result("NMA data setup", False, str(result))
            failed += 1
    except Exception as e:
        test_result("NMA data setup", False, str(e))
        failed += 1

    # NMA run (async)
    try:
        result = driver.execute_async_script('''
            const callback = arguments[arguments.length - 1];
            const nma = new NetworkMetaAnalysis({ method: 'frequentist' });
            const data = [
                { study: 'S1', treatment: 'A', n: 100, events: 20 },
                { study: 'S1', treatment: 'B', n: 100, events: 15 },
                { study: 'S2', treatment: 'B', n: 150, events: 30 },
                { study: 'S2', treatment: 'C', n: 150, events: 40 },
                { study: 'S3', treatment: 'A', n: 120, events: 25 },
                { study: 'S3', treatment: 'C', n: 120, events: 35 }
            ];
            nma.setData(data, 'binary');
            nma.run().then(() => {
                callback({
                    hasResults: nma.results !== null,
                    nEffects: nma.results ? nma.results.effects.length : 0,
                    tau: nma.results ? nma.results.tau : null
                });
            }).catch(e => callback({ error: e.message }));
        ''')
        if result and result['hasResults']:
            test_result("NMA run (frequentist)", True,
                f"effects={result['nEffects']}, tau={result['tau']:.4f}" if result['tau'] else f"effects={result['nEffects']}")
            passed += 1
        else:
            test_result("NMA run (frequentist)", False, str(result))
            failed += 1
    except Exception as e:
        test_result("NMA run (frequentist)", False, str(e))
        failed += 1

    # League table (async)
    try:
        result = driver.execute_async_script('''
            const callback = arguments[arguments.length - 1];
            const nma = new NetworkMetaAnalysis({ method: 'frequentist' });
            const data = [
                { study: 'S1', treatment: 'A', n: 100, events: 20 },
                { study: 'S1', treatment: 'B', n: 100, events: 15 },
                { study: 'S2', treatment: 'B', n: 150, events: 30 },
                { study: 'S2', treatment: 'C', n: 150, events: 40 },
                { study: 'S3', treatment: 'A', n: 120, events: 25 },
                { study: 'S3', treatment: 'C', n: 120, events: 35 }
            ];
            nma.setData(data, 'binary');
            nma.run().then(() => {
                const league = nma.generateLeagueTable();
                callback({
                    hasTable: league !== null,
                    size: league ? league.length : 0
                });
            }).catch(e => callback({ error: e.message }));
        ''')
        if result and result['hasTable']:
            test_result("NMA league table", True, f"size={result['size']}x{result['size']}")
            passed += 1
        else:
            test_result("NMA league table", False, str(result))
            failed += 1
    except Exception as e:
        test_result("NMA league table", False, str(e))
        failed += 1

    # SUCRA/P-scores (async)
    try:
        result = driver.execute_async_script('''
            const callback = arguments[arguments.length - 1];
            const nma = new NetworkMetaAnalysis({ method: 'frequentist' });
            const data = [
                { study: 'S1', treatment: 'A', n: 100, events: 20 },
                { study: 'S1', treatment: 'B', n: 100, events: 15 },
                { study: 'S2', treatment: 'B', n: 150, events: 30 },
                { study: 'S2', treatment: 'C', n: 150, events: 40 },
                { study: 'S3', treatment: 'A', n: 120, events: 25 },
                { study: 'S3', treatment: 'C', n: 120, events: 35 }
            ];
            nma.setData(data, 'binary');
            nma.run().then(() => {
                const sucra = nma.calculateSUCRA();
                const pscores = nma.calculatePScores();
                // Return rankings with both SUCRA and P-scores
                callback(sucra.map((s, i) => ({ ...s, pScore: pscores[i]?.pScore })));
            }).catch(e => callback({ error: e.message }));
        ''')
        if result and len(result) > 0:
            top = result[0]
            test_result("SUCRA/P-scores", True,
                f"Best: {top['treatment']} (SUCRA={top.get('sucra', top.get('pScore', 'N/A'))})")
            passed += 1
        else:
            test_result("SUCRA/P-scores", False, str(result))
            failed += 1
    except Exception as e:
        test_result("SUCRA/P-scores", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 9: NMA CONSISTENCY TESTS
    # ================================================================
    test_section("9. NMA CONSISTENCY TESTS")

    # Node-splitting (checkConsistency is async)
    try:
        result = driver.execute_async_script('''
            const callback = arguments[arguments.length - 1];
            const nma = new NetworkMetaAnalysis({ method: 'frequentist' });
            const data = [
                { study: 'S1', treatment: 'A', n: 100, events: 20 },
                { study: 'S1', treatment: 'B', n: 100, events: 15 },
                { study: 'S2', treatment: 'B', n: 150, events: 30 },
                { study: 'S2', treatment: 'C', n: 150, events: 40 },
                { study: 'S3', treatment: 'A', n: 120, events: 25 },
                { study: 'S3', treatment: 'C', n: 120, events: 35 },
                { study: 'S4', treatment: 'A', n: 80, events: 18 },
                { study: 'S4', treatment: 'B', n: 80, events: 12 }
            ];
            nma.setData(data, 'binary');
            nma.run();
            nma.checkConsistency().then(callback).catch(e => callback({ error: e.message }));
        ''')
        if result and 'nodeSplitting' in result:
            ns = result['nodeSplitting']
            gt = result['globalTest']
            test_result("Node-splitting", True,
                f"comparisons={len(ns)}, global Q={gt['Q']:.2f}, p={gt['pValue']:.4f}")
            passed += 1

            # Check correlation adjustment
            if gt.get('method') == 'correlation-adjusted':
                test_result("Correlation-adjusted global test", True)
                passed += 1
            else:
                test_result("Correlation-adjusted global test", False, gt.get('method'))
                failed += 1
        else:
            test_result("Node-splitting", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Node-splitting", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 10: INPUT VALIDATION
    # ================================================================
    test_section("10. INPUT VALIDATION")

    # Test invalid input handling
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            try {
                ma.calculatePooledEffect("not an array");
                return { caught: false };
            } catch (e) {
                return { caught: true, message: e.message };
            }
        ''')
        if result['caught']:
            test_result("Rejects non-array input", True, result['message'][:50])
            passed += 1
        else:
            test_result("Rejects non-array input", False)
            failed += 1
    except Exception as e:
        test_result("Rejects non-array input", False, str(e))
        failed += 1

    # Test invalid SE
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            try {
                ma.calculatePooledEffect([{ effect: 0.5, se: -0.1 }]);
                return { caught: false };
            } catch (e) {
                return { caught: true, message: e.message };
            }
        ''')
        if result['caught']:
            test_result("Rejects negative SE", True, result['message'][:50])
            passed += 1
        else:
            test_result("Rejects negative SE", False)
            failed += 1
    except Exception as e:
        test_result("Rejects negative SE", False, str(e))
        failed += 1

    # Test NMA validation
    try:
        result = driver.execute_script('''
            const nma = new NetworkMetaAnalysis();
            try {
                nma.setData([{ study: 'S1' }], 'binary');  // Missing treatment
                return { caught: false };
            } catch (e) {
                return { caught: true, message: e.message };
            }
        ''')
        if result['caught']:
            test_result("NMA validates data format", True, result['message'][:50])
            passed += 1
        else:
            test_result("NMA validates data format", False)
            failed += 1
    except Exception as e:
        test_result("NMA validates data format", False, str(e))
        failed += 1

    # ================================================================
    # SECTION 11: STATISTICAL FUNCTIONS
    # ================================================================
    test_section("11. STATISTICAL FUNCTIONS")

    # t-distribution
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            return {
                t_0975_10: ma.tQuantile(0.975, 10),
                t_0975_5: ma.tQuantile(0.975, 5),
                normal_0975: ma.normalQuantile(0.975)
            };
        ''')
        # t(10, 0.975) should be ~2.228, t(5, 0.975) should be ~2.571
        t10_ok = abs(result['t_0975_10'] - 2.228) < 0.01
        t5_ok = abs(result['t_0975_5'] - 2.571) < 0.05
        z_ok = abs(result['normal_0975'] - 1.96) < 0.01

        if t10_ok and t5_ok and z_ok:
            test_result("t-distribution quantiles", True,
                f"t(10)={result['t_0975_10']:.3f}, t(5)={result['t_0975_5']:.3f}, z={result['normal_0975']:.3f}")
            passed += 1
        else:
            test_result("t-distribution quantiles", False,
                f"t(10)={result['t_0975_10']:.3f}, t(5)={result['t_0975_5']:.3f}")
            failed += 1
    except Exception as e:
        test_result("t-distribution quantiles", False, str(e))
        failed += 1

    # Chi-squared
    try:
        result = driver.execute_script('''
            const ma = new MetaAnalysisMethods();
            return {
                chi2_cdf_5_4: ma.chiSquaredCDF(5, 4),
                chi2_cdf_10_5: ma.chiSquaredCDF(10, 5)
            };
        ''')
        # chi2(5, df=4) CDF should be ~0.713
        if result['chi2_cdf_5_4'] > 0.7 and result['chi2_cdf_5_4'] < 0.75:
            test_result("Chi-squared CDF", True,
                f"chi2(5,4)={result['chi2_cdf_5_4']:.4f}")
            passed += 1
        else:
            test_result("Chi-squared CDF", False, str(result))
            failed += 1
    except Exception as e:
        test_result("Chi-squared CDF", False, str(e))
        failed += 1

    # ================================================================
    # SUMMARY
    # ================================================================
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"\n  Total Tests: {passed + failed}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Success Rate: {passed/(passed+failed)*100:.1f}%")
    print("\n" + "="*60)

    if failed == 0:
        print("  ALL TESTS PASSED!")
    else:
        print(f"  {failed} TEST(S) FAILED")
    print("="*60 + "\n")

    driver.quit()
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
