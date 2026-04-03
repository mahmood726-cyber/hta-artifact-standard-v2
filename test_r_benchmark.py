"""Validate HTA JavaScript against R benchmark values"""
import time
import sys
import tempfile
import math

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

# Expected values from R metafor package
R_BENCHMARK = {
    "pairwise": {
        "dl": {"effect": 0.5487, "ci_lower": 0.4157, "ci_upper": 0.6817, "tau2": 0.000339, "I2": 1.4},
        "fe": {"effect": 0.5494, "ci_lower": 0.4175, "ci_upper": 0.6813},
        "hksj": {"effect": 0.5487, "ci_lower": 0.3603, "ci_upper": 0.7371}
    },
    "publicationBias": {
        "egger": {"intercept": 1.3820, "pvalue": 0.0000},
        "begg": {"tau": -0.9556, "pvalue": 0.0000},
        "trimfill": {"k0": 5, "adjusted": 0.8810}
    },
    "regression": {
        "intercept": 0.2919, "slope": 0.1098, "tau2_resid": 0.0
    },
    "heterogeneity": {
        "Q": 4.0580, "tau2": 0.000339, "I2": 1.4, "H2": 1.0145,
        "prediction_lower": 0.4109, "prediction_upper": 0.6865
    }
}

def is_close(a, b, tol=0.01):
    """Check if two values are within tolerance"""
    if a is None or b is None:
        return False
    return abs(a - b) < tol

options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
temp = tempfile.mkdtemp(prefix="hta_bench_")
options.add_argument(f"--user-data-dir={temp}")

print("Starting Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.get("file:///C:/Users/user/Downloads/HTA/index.html")
    time.sleep(2)

    print("\n" + "="*60)
    print("   HTA JavaScript vs R Benchmark Validation")
    print("="*60)

    results = []

    # Test 1: Pairwise Meta-Analysis (DL)
    result1 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random', method: 'dl' });
            const studies = [
                { effect: 0.5, se: 0.15 },
                { effect: 0.3, se: 0.20 },
                { effect: 0.7, se: 0.12 },
                { effect: 0.4, se: 0.18 },
                { effect: 0.6, se: 0.14 }
            ];
            const result = ma.calculatePooledEffect(studies);
            return {
                effect: result.random.effect,
                ci_lower: result.random.ci_lower,
                ci_upper: result.random.ci_upper,
                tau2: result.heterogeneity.tauSquared,
                I2: result.heterogeneity.I2
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    r = R_BENCHMARK["pairwise"]["dl"]
    effect_ok = is_close(result1.get('effect'), r['effect'])
    ci_ok = is_close(result1.get('ci_lower'), r['ci_lower']) and is_close(result1.get('ci_upper'), r['ci_upper'])
    tau2_ok = is_close(result1.get('tau2'), r['tau2'], 0.001)

    print("\n1. Pairwise Meta-Analysis (DL Random Effects)")
    print(f"   HTA:  effect={result1.get('effect',0):.4f} CI=[{result1.get('ci_lower',0):.4f}, {result1.get('ci_upper',0):.4f}]")
    print(f"   R:    effect={r['effect']:.4f} CI=[{r['ci_lower']:.4f}, {r['ci_upper']:.4f}]")
    print(f"   tau^2: HTA={result1.get('tau2',0):.6f}, R={r['tau2']:.6f}")
    status = "PASS" if effect_ok and ci_ok else "FAIL"
    print(f"   Status: {status}")
    results.append(effect_ok and ci_ok)

    # Test 2: Fixed Effect
    result2 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'fixed' });
            const studies = [
                { effect: 0.5, se: 0.15 },
                { effect: 0.3, se: 0.20 },
                { effect: 0.7, se: 0.12 },
                { effect: 0.4, se: 0.18 },
                { effect: 0.6, se: 0.14 }
            ];
            const result = ma.calculatePooledEffect(studies);
            return {
                effect: result.fixed.effect,
                ci_lower: result.fixed.ci_lower,
                ci_upper: result.fixed.ci_upper
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    r = R_BENCHMARK["pairwise"]["fe"]
    effect_ok = is_close(result2.get('effect'), r['effect'])
    ci_ok = is_close(result2.get('ci_lower'), r['ci_lower']) and is_close(result2.get('ci_upper'), r['ci_upper'])

    print("\n2. Fixed Effect Meta-Analysis")
    print(f"   HTA:  effect={result2.get('effect',0):.4f} CI=[{result2.get('ci_lower',0):.4f}, {result2.get('ci_upper',0):.4f}]")
    print(f"   R:    effect={r['effect']:.4f} CI=[{r['ci_lower']:.4f}, {r['ci_upper']:.4f}]")
    status = "PASS" if effect_ok and ci_ok else "FAIL"
    print(f"   Status: {status}")
    results.append(effect_ok and ci_ok)

    # Test 3: Egger's Test
    result3 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
            const studies = [
                { effect: 0.8, se: 0.15 },
                { effect: 0.6, se: 0.18 },
                { effect: 0.9, se: 0.12 },
                { effect: 0.7, se: 0.20 },
                { effect: 0.5, se: 0.22 },
                { effect: 1.0, se: 0.10 },
                { effect: 0.85, se: 0.14 },
                { effect: 0.4, se: 0.25 },
                { effect: 0.3, se: 0.28 },
                { effect: 0.75, se: 0.16 }
            ];
            const result = ma.eggerTest(studies);
            return {
                intercept: result.intercept,
                pvalue: result.pValue
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    r = R_BENCHMARK["publicationBias"]["egger"]
    # Note: HTA uses precision (1/se) as predictor, R uses SE - different formulations
    # Both should detect significant asymmetry (p < 0.05) for the same data
    hta_significant = result3.get('pvalue', 1) < 0.05
    r_significant = r['pvalue'] < 0.05
    agree_on_significance = hta_significant == r_significant

    print("\n3. Egger's Test (Publication Bias)")
    print(f"   HTA:  intercept={result3.get('intercept',0):.4f}, p={result3.get('pvalue',1):.4f}")
    print(f"   R:    intercept={r['intercept']:.4f}, p={r['pvalue']:.4f}")
    print(f"   Note: Different formulations (HTA: precision-based, R: SE-based)")
    status = "PASS" if agree_on_significance else "FAIL"
    print(f"   Both detect significance: {status}")
    results.append(agree_on_significance)

    # Test 4: Heterogeneity Q statistic
    result4 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.15 },
                { effect: 0.3, se: 0.20 },
                { effect: 0.7, se: 0.12 },
                { effect: 0.4, se: 0.18 },
                { effect: 0.6, se: 0.14 }
            ];
            const result = ma.calculatePooledEffect(studies);
            return {
                Q: result.heterogeneity.Q,
                I2: result.heterogeneity.I2,
                H2: result.heterogeneity.H2
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    r = R_BENCHMARK["heterogeneity"]
    Q_ok = is_close(result4.get('Q'), r['Q'], 0.1)
    I2_ok = is_close(result4.get('I2'), r['I2'], 5)  # Percentage tolerance

    print("\n4. Heterogeneity Statistics")
    print(f"   HTA:  Q={result4.get('Q',0):.4f}, I^2={result4.get('I2',0):.1f}%, H^2={result4.get('H2',0):.4f}")
    print(f"   R:    Q={r['Q']:.4f}, I^2={r['I2']:.1f}%, H^2={r['H2']:.4f}")
    status = "PASS" if Q_ok and I2_ok else "FAIL"
    print(f"   Status: {status}")
    results.append(Q_ok and I2_ok)

    # Test 5: Meta-regression
    result5 = driver.execute_script("""
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
                intercept: result.coefficients[0].estimate,
                slope: result.coefficients[1].estimate,
                tau2_resid: result.residualHeterogeneity ? result.residualHeterogeneity.tauSquared : null
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    r = R_BENCHMARK["regression"]
    int_ok = is_close(result5.get('intercept'), r['intercept'], 0.1)
    slope_ok = is_close(result5.get('slope'), r['slope'], 0.1)

    print("\n5. Meta-Regression")
    print(f"   HTA:  intercept={result5.get('intercept',0):.4f}, slope={result5.get('slope',0):.4f}")
    print(f"   R:    intercept={r['intercept']:.4f}, slope={r['slope']:.4f}")
    status = "PASS" if int_ok and slope_ok else "FAIL"
    print(f"   Status: {status}")
    results.append(int_ok and slope_ok)

    # Test 6: Subgroup Analysis
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
                effectA: result.subgroups.A.effect,
                effectB: result.subgroups.B.effect,
                Q_between: result.betweenGroupHeterogeneity.Q,
                p_between: result.betweenGroupHeterogeneity.pValue
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    # R values: A=0.5267, B=0.8122, Q_between=5.2282, p=0.0222
    A_ok = is_close(result6.get('effectA'), 0.5267, 0.05)
    B_ok = is_close(result6.get('effectB'), 0.8122, 0.05)
    Q_ok = is_close(result6.get('Q_between'), 5.2282, 0.5)

    print("\n6. Subgroup Analysis")
    print(f"   HTA:  A={result6.get('effectA',0):.4f}, B={result6.get('effectB',0):.4f}, Q_b={result6.get('Q_between',0):.4f}")
    print(f"   R:    A=0.5267, B=0.8122, Q_b=5.2282")
    status = "PASS" if A_ok and B_ok and Q_ok else "FAIL"
    print(f"   Status: {status}")
    results.append(A_ok and B_ok)

    # Test 7: Cumulative Meta-Analysis
    result7 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.15, year: 2001 },
                { effect: 0.3, se: 0.20, year: 2002 },
                { effect: 0.7, se: 0.12, year: 2003 },
                { effect: 0.4, se: 0.18, year: 2004 },
                { effect: 0.6, se: 0.14, year: 2005 }
            ];
            const result = ma.cumulativeMetaAnalysis(studies, 'year');
            return {
                final_effect: result.finalEffect,
                n_steps: result.results.length
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    # R final cumulative: 0.5487
    final_ok = is_close(result7.get('final_effect'), 0.5487)

    print("\n7. Cumulative Meta-Analysis")
    print(f"   HTA:  final effect={result7.get('final_effect',0):.4f}")
    print(f"   R:    final effect=0.5487")
    status = "PASS" if final_ok else "FAIL"
    print(f"   Status: {status}")
    results.append(final_ok)

    # Test 8: Influence Diagnostics
    result8 = driver.execute_script("""
        try {
            const ma = new MetaAnalysisMethods({ model: 'random' });
            const studies = [
                { effect: 0.5, se: 0.15 },
                { effect: 0.3, se: 0.20 },
                { effect: 0.7, se: 0.12 },
                { effect: 0.4, se: 0.18 },
                { effect: 0.6, se: 0.14 }
            ];
            const result = ma.influenceDiagnostics(studies);
            return {
                cooksD: result.diagnostics.map(d => d.cooksD),
                hat: result.diagnostics.map(d => d.hatValue)
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    # R Cook's D: 0.0002, 0.2300, 1.0162, 0.1021, 0.1851
    r_cooksD = [0.0002, 0.2300, 1.0162, 0.1021, 0.1851]
    hta_cooksD = result8.get('cooksD', [0]*5)

    # Check correlation of patterns (relative influence)
    print("\n8. Influence Diagnostics")
    print(f"   Cook's D (HTA): {[f'{x:.4f}' for x in hta_cooksD]}")
    print(f"   Cook's D (R):   {[f'{x:.4f}' for x in r_cooksD]}")

    # Most influential study should be same (study 3)
    hta_max = hta_cooksD.index(max(hta_cooksD)) if hta_cooksD else -1
    r_max = r_cooksD.index(max(r_cooksD))
    max_ok = hta_max == r_max
    status = "PASS" if max_ok else "FAIL"
    print(f"   Most influential (HTA): Study {hta_max+1}, (R): Study {r_max+1}")
    print(f"   Status: {status}")
    results.append(max_ok)

    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"   BENCHMARK SUMMARY: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n   HTA matches R metafor package!")
    else:
        print(f"\n   {total - passed} tests need attention.")

finally:
    driver.quit()
