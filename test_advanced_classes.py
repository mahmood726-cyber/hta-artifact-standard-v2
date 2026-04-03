"""Test that all advanced enhancement classes are loaded correctly"""
import time
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
temp = tempfile.mkdtemp(prefix="hta_test_")
options.add_argument(f"--user-data-dir={temp}")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

try:
    driver.get("file:///C:/Users/user/Downloads/HTA/index.html")
    time.sleep(2)

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

    print("=== Testing Advanced Enhancement Classes ===\n")

    all_passed = True
    for cls in classes:
        exists = driver.execute_script(f"return typeof window.{cls} !== 'undefined'")
        is_class = driver.execute_script(f"return typeof window.{cls} === 'function'")
        can_instantiate = driver.execute_script(f"""
            try {{
                new window.{cls}();
                return true;
            }} catch(e) {{
                return 'Error: ' + e.message;
            }}
        """)

        status = "PASS" if (exists and is_class and can_instantiate == True) else "FAIL"
        if status == "FAIL":
            all_passed = False

        print(f"  {cls}: {status}")
        if can_instantiate != True:
            print(f"    Instantiation: {can_instantiate}")

    print()

    # Test HKSJ with sample data
    print("=== Testing HKSJ Adjustment ===")
    result = driver.execute_script("""
        try {
            const hksj = new HKSJAdjustment();
            const studies = [
                {effect: 0.5, se: 0.1},
                {effect: 0.3, se: 0.15},
                {effect: 0.6, se: 0.12},
                {effect: 0.4, se: 0.08},
                {effect: 0.55, se: 0.11}
            ];
            const tauSq = 0.01;
            const pooled = 0.47;
            const result = hksj.adjust(studies, tauSq, pooled);
            return {
                success: true,
                effect: result.effect.toFixed(3),
                se: result.se.toFixed(4),
                ci_lower: result.ci_lower.toFixed(3),
                ci_upper: result.ci_upper.toFixed(3),
                df: result.df,
                tCrit: result.tCritical.toFixed(3)
            };
        } catch(e) {
            return {success: false, error: e.message};
        }
    """)
    if result['success']:
        print(f"  Effect: {result['effect']}")
        print(f"  SE (HKSJ): {result['se']}")
        print(f"  95% CI: [{result['ci_lower']}, {result['ci_upper']}]")
        print(f"  df: {result['df']}, t-crit: {result['tCrit']}")
    else:
        print(f"  Error: {result['error']}")

    # Test MCMC Diagnostics
    print("\n=== Testing MCMC Diagnostics ===")
    result = driver.execute_script("""
        try {
            const mcmc = new MCMCDiagnostics();
            // Simulate two chains with slight differences
            const chain1 = Array.from({length: 1000}, () => Math.random() * 2);
            const chain2 = Array.from({length: 1000}, () => Math.random() * 2 + 0.1);
            const result = mcmc.analyze([chain1, chain2], {burnin: 100});
            return {
                success: true,
                rhat: result.gelmanRubin.rhat.toFixed(4),
                converged: result.gelmanRubin.converged,
                ess: result.effectiveSampleSize.ess,
                gewekeZ: result.geweke.z.toFixed(3)
            };
        } catch(e) {
            return {success: false, error: e.message};
        }
    """)
    if result['success']:
        print(f"  R-hat: {result['rhat']} (converged: {result['converged']})")
        print(f"  ESS: {result['ess']}")
        print(f"  Geweke Z: {result['gewekeZ']}")
    else:
        print(f"  Error: {result['error']}")

    # Test GRADE Assessment
    print("\n=== Testing GRADE Assessment ===")
    result = driver.execute_script("""
        try {
            const grade = new GRADEAssessment();
            const evidence = {
                studyDesign: 'RCT',
                riskOfBias: {overall: 'some_concerns'},
                inconsistency: {i2: 30},
                indirectness: {rating: 'low'},
                imprecision: {ciWidth: 0.3, threshold: 0.5},
                publicationBias: {detected: false}
            };
            const result = grade.assess(evidence);
            return {
                success: true,
                certainty: result.overallCertainty,
                score: result.score,
                summary: result.summary
            };
        } catch(e) {
            return {success: false, error: e.message};
        }
    """)
    if result['success']:
        print(f"  Certainty: {result['certainty']}")
        print(f"  Score: {result['score']}")
        print(f"  Summary: {result['summary'][:80]}...")
    else:
        print(f"  Error: {result['error']}")

    # Check for console errors
    print("\n=== Console Errors ===")
    logs = driver.get_log('browser')
    errors = [l for l in logs if l['level'] == 'SEVERE']
    if errors:
        for e in errors[:5]:
            print(f"  ERROR: {e['message'][:100]}")
    else:
        print("  No console errors")

    print()
    print("=" * 50)
    if all_passed:
        print("ALL 10 CLASSES LOADED AND INSTANTIABLE")
    else:
        print("SOME CLASSES FAILED TO LOAD")
    print("=" * 50)

finally:
    driver.quit()
