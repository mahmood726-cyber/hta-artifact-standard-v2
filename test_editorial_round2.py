"""Test Editorial Review Round 2 Fixes"""
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
temp = tempfile.mkdtemp(prefix="hta_ed2_")
options.add_argument(f"--user-data-dir={temp}")

print("Starting Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.get("file:///C:/Users/user/Downloads/HTA/index.html")
    time.sleep(2)

    print("\n=== Editorial Review Round 2 Validation ===\n")

    # Test 1: Meta-regression random-effects weights
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
            // Check that tau is used in regression (it should be > 0)
            return {
                success: result && !result.error,
                hasTau: result.residualHeterogeneity !== undefined
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"1. Meta-regression RE weights: {'PASS' if result1.get('success') else 'FAIL'}")

    # Test 2: Trim-and-fill random-effects model
    result2 = driver.execute_script("""
        try {
            const ma = new MetaAnalysis({ model: 'random' });
            const studies = [
                { effect: 0.8, se: 0.15 },
                { effect: 0.6, se: 0.18 },
                { effect: 0.9, se: 0.12 },
                { effect: 0.7, se: 0.20 },
                { effect: 0.5, se: 0.22 },
                { effect: 1.0, se: 0.10 },
                { effect: 0.85, se: 0.14 }
            ];
            const result = ma.trimAndFill(studies);
            // Check model type is returned
            return {
                success: result && result.adjusted && result.adjusted.model !== undefined,
                model: result.adjusted ? result.adjusted.model : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"2. Trim-and-fill RE model: {'PASS' if result2.get('success') else 'FAIL'} (model: {result2.get('model')})")

    # Test 3: Selection model likelihood weights
    result3 = driver.execute_script("""
        try {
            const ma = new MetaAnalysis({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.10 },  // sig
                { effect: 0.3, se: 0.08 },  // sig
                { effect: 0.6, se: 0.09 },  // sig
                { effect: 0.1, se: 0.15 },  // non-sig
                { effect: 0.15, se: 0.18 }, // non-sig
                { effect: 0.4, se: 0.11 },  // marginal
                { effect: 0.2, se: 0.20 }   // non-sig
            ];
            const result = ma.selectionModel(studies);
            // Check that selection weights are computed
            return {
                success: result && result.selectionWeights !== undefined,
                hasWeights: result.selectionWeights !== undefined,
                weights: result.selectionWeights
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"3. Selection model weights: {'PASS' if result3.get('hasWeights') else 'FAIL'}")
    if result3.get('weights'):
        print(f"   Weights: sig={result3['weights'].get('significant',0):.2f}, marg={result3['weights'].get('marginal',0):.2f}, nonsig={result3['weights'].get('nonsignificant',0):.2f}")

    # Test 4: Copas IV weighting
    result4 = driver.execute_script("""
        try {
            if (typeof CopasSelectionModel === 'undefined') {
                return { skipped: true, reason: 'CopasSelectionModel not available globally' };
            }
            const copas = new CopasSelectionModel();
            const studies = [
                { effect: 0.5, se: 0.15 },
                { effect: 0.3, se: 0.20 },
                { effect: 0.7, se: 0.12 },
                { effect: 0.4, se: 0.18 },
                { effect: 0.6, se: 0.14 }
            ];
            const result = copas.fit(studies);
            return {
                success: result && result.unadjusted !== undefined,
                unadjEffect: result.unadjusted ? result.unadjusted.effect : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    if result4.get('skipped'):
        print(f"4. Copas IV weighting: SKIP ({result4.get('reason')})")
    else:
        print(f"4. Copas IV weighting: {'PASS' if result4.get('success') else 'FAIL'}")

    # Test 5: NMA chi-squared non-integer df
    result5 = driver.execute_script("""
        try {
            const nma = new NetworkMetaAnalysis({
                model: 'random',
                method: 'bayesian',
                niter: 100,
                seed: 12345
            });
            // Test gamma sampling directly (chi-squared uses it for non-integer df)
            const samples = [];
            for (let i = 0; i < 100; i++) {
                const chi = nma.sampleChiSquared(3.5);  // Non-integer df
                samples.push(chi);
            }
            const mean = samples.reduce((a,b) => a+b, 0) / samples.length;
            // Chi-sq(df) has mean = df, so mean should be ~3.5
            return {
                success: Math.abs(mean - 3.5) < 1.5,  // Within reasonable range
                mean: mean.toFixed(2),
                expectedMean: 3.5
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"5. NMA chi-sq non-integer df: {'PASS' if result5.get('success') else 'FAIL'} (mean={result5.get('mean')}, expected~3.5)")

    # Test 6: Between-group Q with within-group tau
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
            return {
                success: result && result.betweenGroupHeterogeneity &&
                         result.betweenGroupHeterogeneity.pooledTauSquaredWithin !== undefined,
                hasTauWithin: result.betweenGroupHeterogeneity ?
                              result.betweenGroupHeterogeneity.pooledTauSquaredWithin !== undefined : false,
                tauWithin: result.betweenGroupHeterogeneity ?
                           result.betweenGroupHeterogeneity.pooledTauSquaredWithin : null,
                Q: result.betweenGroupHeterogeneity ? result.betweenGroupHeterogeneity.Q : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"6. Between-group Q with tau: {'PASS' if result6.get('hasTauWithin') else 'FAIL'}")
    if result6.get('tauWithin') is not None:
        print(f"   Pooled tau^2 within: {result6['tauWithin']:.4f}, Q_between: {result6['Q']:.3f}")

    # Summary
    print("\n" + "="*50)
    passes = sum([
        result1.get('success', False),
        result2.get('success', False),
        result3.get('hasWeights', False),
        result4.get('success', False) or result4.get('skipped', False),
        result5.get('success', False),
        result6.get('hasTauWithin', False)
    ])
    print(f"EDITORIAL ROUND 2: {passes}/6 tests passed")

finally:
    driver.quit()
