"""Test editorial review fixes - MPSRF and Exchangeable Interactions"""
from _hta_url import hta_index_url, hta_index_path
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
temp = tempfile.mkdtemp(prefix="hta_test_")
options.add_argument(f"--user-data-dir={temp}")

print("Starting Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.get(hta_index_url())
    time.sleep(2)

    print("\n=== Testing Editorial Review Fixes ===\n")

    # Test 1: MPSRF for multivariate MCMC diagnostics
    print("1. MPSRF (Multivariate Potential Scale Reduction Factor)")
    mpsrf_result = driver.execute_script("""
        try {
            const mcmc = new MCMCDiagnostics();

            // Create multivariate chains (2 parameters, 2 chains each)
            const chains = {
                mu: [
                    Array.from({length: 200}, () => Math.random() * 0.5 + 0.3),
                    Array.from({length: 200}, () => Math.random() * 0.5 + 0.3)
                ],
                tau: [
                    Array.from({length: 200}, () => Math.random() * 0.2 + 0.1),
                    Array.from({length: 200}, () => Math.random() * 0.2 + 0.1)
                ]
            };

            const result = mcmc.analyze(chains);

            return {
                hasMPSRF: result.mpsrf !== undefined,
                mpsrfValue: result.mpsrf?.mpsrf,
                hasEigenvalues: result.mpsrf?.eigenvalues?.length > 0,
                hasIndividualRhats: Object.keys(result.individualRhats || {}).length > 0,
                hasConvergenceSummary: result.convergenceSummary !== undefined,
                interpretation: result.mpsrf?.interpretation
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    if mpsrf_result.get('error'):
        print(f"   FAIL: {mpsrf_result['error']}")
    else:
        print(f"   Has MPSRF: {mpsrf_result['hasMPSRF']}")
        print(f"   MPSRF value: {mpsrf_result['mpsrfValue']:.4f}" if mpsrf_result['mpsrfValue'] else "   MPSRF: N/A")
        print(f"   Has eigenvalues: {mpsrf_result['hasEigenvalues']}")
        print(f"   Has individual R-hats: {mpsrf_result['hasIndividualRhats']}")
        print(f"   Interpretation: {mpsrf_result['interpretation']}")
        print(f"   PASS" if mpsrf_result['hasMPSRF'] else "   FAIL")

    # Test 2: Exchangeable interactions in NMA regression
    print("\n2. Exchangeable Interaction in NMA Regression")
    exchg_result = driver.execute_script("""
        try {
            const nmr = new NetworkMetaRegression({ nIterations: 500, nBurnin: 100 });

            // Create test NMA data with covariate
            const data = [
                { study: 'S1', treatment: 'A', effect: 0, se: 0.1, covariates: { year: 2010 } },
                { study: 'S1', treatment: 'B', effect: 0.3, se: 0.12, covariates: { year: 2010 } },
                { study: 'S2', treatment: 'A', effect: 0, se: 0.15, covariates: { year: 2015 } },
                { study: 'S2', treatment: 'C', effect: 0.5, se: 0.14, covariates: { year: 2015 } },
                { study: 'S3', treatment: 'B', effect: 0, se: 0.11, covariates: { year: 2020 } },
                { study: 'S3', treatment: 'C', effect: 0.2, se: 0.13, covariates: { year: 2020 } },
                { study: 'S4', treatment: 'A', effect: 0, se: 0.1, covariates: { year: 2018 } },
                { study: 'S4', treatment: 'B', effect: 0.25, se: 0.12, covariates: { year: 2018 } }
            ];

            const result = nmr.fit(data, ['year'], { interactionType: 'exchangeable' });

            return {
                hasInteractionType: result.interactionType === 'exchangeable',
                hasExchangeablePrior: result.exchangeablePrior !== undefined,
                sigmaGammaMean: result.exchangeablePrior?.sigmaGamma?.mean,
                hasShrinkage: result.shrinkageFactor !== undefined,
                shrinkageFactor: result.shrinkageFactor?.factor,
                shrinkageInterpretation: result.shrinkageFactor?.interpretation,
                nInteractions: result.interactions?.length,
                interactionsHaveTreatment: result.interactions?.[0]?.treatment !== undefined
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    if exchg_result.get('error'):
        print(f"   FAIL: {exchg_result['error']}")
    else:
        print(f"   Interaction type is exchangeable: {exchg_result['hasInteractionType']}")
        print(f"   Has exchangeable prior: {exchg_result['hasExchangeablePrior']}")
        print(f"   Sigma gamma (prior SD): {exchg_result['sigmaGammaMean']:.4f}" if exchg_result['sigmaGammaMean'] else "   N/A")
        print(f"   Has shrinkage factor: {exchg_result['hasShrinkage']}")
        print(f"   Shrinkage: {exchg_result['shrinkageFactor']:.3f}" if exchg_result['shrinkageFactor'] else "   N/A")
        print(f"   Shrinkage interpretation: {exchg_result['shrinkageInterpretation']}")
        print(f"   Number of treatment-specific interactions: {exchg_result['nInteractions']}")
        print(f"   PASS" if exchg_result['hasInteractionType'] and exchg_result['hasExchangeablePrior'] else "   FAIL")

    # Test 3: Compare common vs exchangeable
    print("\n3. Common vs Independent vs Exchangeable Comparison")
    compare_result = driver.execute_script("""
        try {
            const nmr = new NetworkMetaRegression({ nIterations: 300, nBurnin: 50 });

            const data = [
                { study: 'S1', treatment: 'A', effect: 0, se: 0.1, covariates: { x: 0 } },
                { study: 'S1', treatment: 'B', effect: 0.3, se: 0.12, covariates: { x: 0 } },
                { study: 'S2', treatment: 'A', effect: 0, se: 0.15, covariates: { x: 1 } },
                { study: 'S2', treatment: 'C', effect: 0.5, se: 0.14, covariates: { x: 1 } },
                { study: 'S3', treatment: 'B', effect: 0, se: 0.11, covariates: { x: 2 } },
                { study: 'S3', treatment: 'C', effect: 0.2, se: 0.13, covariates: { x: 2 } }
            ];

            const common = nmr.fit(data, ['x'], { interactionType: 'common' });
            const indep = nmr.fit(data, ['x'], { interactionType: 'independent' });
            const exch = nmr.fit(data, ['x'], { interactionType: 'exchangeable' });

            return {
                commonType: common.interactionType,
                commonNInteractions: common.interactions.length,
                indepType: indep.interactionType,
                indepNInteractions: indep.interactions.length,
                exchType: exch.interactionType,
                exchNInteractions: exch.interactions.length,
                exchHasPrior: exch.exchangeablePrior !== undefined
            };
        } catch(e) {
            return { error: e.message };
        }
    """)

    if compare_result.get('error'):
        print(f"   FAIL: {compare_result['error']}")
    else:
        print(f"   Common: {compare_result['commonNInteractions']} interaction(s)")
        print(f"   Independent: {compare_result['indepNInteractions']} interaction(s)")
        print(f"   Exchangeable: {compare_result['exchNInteractions']} interaction(s) + hierarchical prior")
        all_ok = (compare_result['commonType'] == 'common' and
                  compare_result['indepType'] == 'independent' and
                  compare_result['exchType'] == 'exchangeable' and
                  compare_result['exchHasPrior'])
        print(f"   PASS" if all_ok else "   FAIL")

    # Summary
    print("\n" + "=" * 50)
    all_pass = (not mpsrf_result.get('error') and mpsrf_result.get('hasMPSRF') and
                not exchg_result.get('error') and exchg_result.get('hasInteractionType') and
                not compare_result.get('error'))
    print(f"EDITORIAL FIXES: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    print("=" * 50)

finally:
    driver.quit()
