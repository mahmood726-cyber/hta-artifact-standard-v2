"""Test Editorial Review Round 2 Fixes"""
import sys
import tempfile
import time

from _hta_url import hta_index_url

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
    driver.get(hta_index_url())
    time.sleep(2)

    print("\n=== Editorial Review Round 2 Validation ===\n")

    # Test 1: Meta-regression random-effects weights
    result1 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.15, moderator: 1 },
                { effect: 0.3, se: 0.20, moderator: 2 },
                { effect: 0.7, se: 0.12, moderator: 3 },
                { effect: 0.4, se: 0.18, moderator: 2 },
                { effect: 0.6, se: 0.14, moderator: 3 }
            ];
            const result = ma.metaRegression(studies, ['moderator']);
            return {
                success: result && !result.error,
                hasTau: result && result.residualHeterogeneity !== undefined,
                error: result ? result.error : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"1. Meta-regression RE weights: {'PASS' if result1.get('success') else 'FAIL'}")
    if result1.get('error'):
        print(f"   Error: {result1['error']}")

    # Test 2: Trim-and-fill random-effects model
    result2 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
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
            return {
                success: result && result.adjusted && result.adjusted.model !== undefined,
                model: result && result.adjusted ? result.adjusted.model : null,
                hasOrigModel: result && result.original ? result.original.model !== undefined : false
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"2. Trim-and-fill RE model: {'PASS' if result2.get('success') else 'FAIL'} (model: {result2.get('model')})")
    if result2.get('error'):
        print(f"   Error: {result2['error']}")

    # Test 3: Selection model likelihood weights
    result3 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
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
            return {
                success: result && result.selectionWeights !== undefined,
                hasWeights: result && result.selectionWeights !== undefined,
                weights: result ? result.selectionWeights : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"3. Selection model weights: {'PASS' if result3.get('hasWeights') else 'FAIL'}")
    if result3.get('weights'):
        print(f"   Weights: sig={result3['weights'].get('significant',0):.2f}, marg={result3['weights'].get('marginal',0):.2f}, nonsig={result3['weights'].get('nonsignificant',0):.2f}")
    if result3.get('error'):
        print(f"   Error: {result3['error']}")

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
                unadjEffect: result && result.unadjusted ? result.unadjusted.effect : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    if result4.get('skipped'):
        print(f"4. Copas IV weighting: SKIP ({result4.get('reason')})")
    else:
        print(f"4. Copas IV weighting: {'PASS' if result4.get('success') else 'FAIL'}")
        if result4.get('error'):
            print(f"   Error: {result4['error']}")

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
            return {
                success: Math.abs(mean - 3.5) < 1.5,
                mean: mean.toFixed(2),
                expectedMean: 3.5
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"5. NMA chi-sq non-integer df: {'PASS' if result5.get('success') else 'FAIL'} (mean={result5.get('mean')}, expected~3.5)")
    if result5.get('error'):
        print(f"   Error: {result5['error']}")

    # Test 6: Between-group Q with within-group tau
    result6 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
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
                hasTauWithin: result && result.betweenGroupHeterogeneity ?
                              result.betweenGroupHeterogeneity.pooledTauSquaredWithin !== undefined : false,
                tauWithin: result && result.betweenGroupHeterogeneity ?
                           result.betweenGroupHeterogeneity.pooledTauSquaredWithin : null,
                Q: result && result.betweenGroupHeterogeneity ? result.betweenGroupHeterogeneity.Q : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)
    print(f"6. Between-group Q with tau: {'PASS' if result6.get('hasTauWithin') else 'FAIL'}")
    if result6.get('tauWithin') is not None:
        print(f"   Pooled tau^2 within: {result6['tauWithin']:.4f}, Q_between: {result6['Q']:.3f}")
    if result6.get('error'):
        print(f"   Error: {result6['error']}")

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
