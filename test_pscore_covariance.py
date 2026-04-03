"""Test P-score covariance structure fix"""
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
temp = tempfile.mkdtemp(prefix="hta_pscore_")
options.add_argument(f"--user-data-dir={temp}")

print("Starting Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.get("file:///C:/Users/user/Downloads/HTA/index.html")
    time.sleep(2)

    print("\n=== Testing P-Score Covariance Fix ===\n")

    result = driver.execute_script("""
        try {
            const nma = new NetworkMetaAnalysis({
                model: 'random',
                method: 'frequentist',
                seed: 12345
            });

            // Arm-level data forming a network (A-B, A-C, B-C comparisons)
            const data = [
                { study: 'S1', treatment: 'A', n: 100, events: 20 },
                { study: 'S1', treatment: 'B', n: 100, events: 15 },
                { study: 'S2', treatment: 'A', n: 120, events: 25 },
                { study: 'S2', treatment: 'B', n: 120, events: 18 },
                { study: 'S3', treatment: 'A', n: 80, events: 15 },
                { study: 'S3', treatment: 'C', n: 80, events: 10 },
                { study: 'S4', treatment: 'B', n: 90, events: 20 },
                { study: 'S4', treatment: 'C', n: 90, events: 12 },
                { study: 'S5', treatment: 'B', n: 110, events: 22 },
                { study: 'S5', treatment: 'C', n: 110, events: 14 }
            ];

            nma.setData(data, 'binary');
            const results = nma.runFrequentistNMA();

            // Check that varCov matrix is in results
            const hasVarCov = results.varCov !== undefined;
            const varCovDim = results.varCov ? results.varCov.length : 0;

            // Check off-diagonal elements (covariances)
            let hasNonZeroCovariance = false;
            if (results.varCov && results.varCov.length > 1) {
                for (let i = 0; i < results.varCov.length; i++) {
                    for (let j = 0; j < results.varCov[0].length; j++) {
                        if (i !== j && Math.abs(results.varCov[i][j]) > 1e-10) {
                            hasNonZeroCovariance = true;
                            break;
                        }
                    }
                }
            }

            // Get P-scores - need to call the method after setting results
            nma.results = results;
            const pScores = nma.calculatePScores() || [];

            return {
                hasVarCov: hasVarCov,
                varCovDimension: varCovDim,
                hasNonZeroCovariance: hasNonZeroCovariance,
                varCovSample: results.varCov ? [
                    [results.varCov[0][0], results.varCov[0][1]],
                    [results.varCov[1][0], results.varCov[1][1]]
                ] : null,
                nPScores: pScores.length,
                pScores: pScores.map(p => ({
                    treatment: p.treatment,
                    pScore: p.pScore?.toFixed(1)
                }))
            };
        } catch(e) {
            return { error: e.message, stack: e.stack };
        }
    """)

    if result.get('error'):
        print(f"ERROR: {result['error']}")
        print(f"Stack: {result.get('stack', 'N/A')[:500]}")
    else:
        print(f"Variance-covariance matrix present: {result['hasVarCov']}")
        print(f"Matrix dimension: {result['varCovDimension']}x{result['varCovDimension']}")
        print(f"Has non-zero covariances: {result['hasNonZeroCovariance']}")

        if result['varCovSample']:
            print(f"\nVariance-Covariance matrix (first 2x2):")
            for row in result['varCovSample']:
                print(f"  [{row[0]:.6f}, {row[1]:.6f}]")

        print(f"\nP-Scores calculated: {result['nPScores']}")
        for ps in result['pScores']:
            print(f"  {ps['treatment']}: {ps['pScore']}%")

        # Validation
        passed = (result['hasVarCov'] and
                  result['varCovDimension'] >= 2 and
                  result['nPScores'] >= 3)
        print(f"\nP-SCORE COVARIANCE FIX: {'PASS' if passed else 'FAIL'}")

finally:
    driver.quit()
