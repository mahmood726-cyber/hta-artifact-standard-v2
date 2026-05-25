"""Debug exchangeable interaction issue"""
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
temp = tempfile.mkdtemp(prefix="hta_debug_")
options.add_argument(f"--user-data-dir={temp}")

print("Starting Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.get(hta_index_url())
    time.sleep(2)

    print("\n=== Debug Exchangeable Interaction ===\n")

    # Test with more verbose output
    result = driver.execute_script("""
        try {
            const nmr = new NetworkMetaRegression({ nIterations: 300, nBurnin: 50 });

            const data = [
                { study: 'S1', treatment: 'A', effect: 0, se: 0.1, covariates: { year: 2010 } },
                { study: 'S1', treatment: 'B', effect: 0.3, se: 0.12, covariates: { year: 2010 } },
                { study: 'S2', treatment: 'A', effect: 0, se: 0.15, covariates: { year: 2015 } },
                { study: 'S2', treatment: 'C', effect: 0.5, se: 0.14, covariates: { year: 2015 } }
            ];

            // Test fit method
            const result = nmr.fit(data, ['year'], { interactionType: 'exchangeable' });

            return {
                // Raw values
                rawInteractionType: result.interactionType,
                typeOfInteractionType: typeof result.interactionType,
                keys: Object.keys(result),

                // Specific checks
                hasInteractionType: 'interactionType' in result,
                isExchangeable: result.interactionType === 'exchangeable',

                // Other fields
                hasInteractions: result.interactions !== undefined,
                nInteractions: result.interactions?.length,
                interactionsFirst: JSON.stringify(result.interactions?.[0]),

                // Exchangeable specific
                hasExchangeablePrior: result.exchangeablePrior !== undefined,
                exchangeablePriorKeys: result.exchangeablePrior ? Object.keys(result.exchangeablePrior) : null,

                // Shrinkage
                hasShrinkage: result.shrinkageFactor !== undefined
            };
        } catch(e) {
            return { error: e.message, stack: e.stack };
        }
    """)

    if result.get('error'):
        print(f"ERROR: {result['error']}")
        print(f"Stack: {result.get('stack', 'N/A')}")
    else:
        print("Result object keys:", result['keys'])
        print("\ninteractionType field:")
        print(f"  Present in result: {result['hasInteractionType']}")
        print(f"  Raw value: '{result['rawInteractionType']}'")
        print(f"  Type: {result['typeOfInteractionType']}")
        print(f"  === 'exchangeable': {result['isExchangeable']}")

        print("\nInteractions:")
        print(f"  Has interactions: {result['hasInteractions']}")
        print(f"  Count: {result['nInteractions']}")
        print(f"  First: {result['interactionsFirst']}")

        print("\nExchangeable prior:")
        print(f"  Present: {result['hasExchangeablePrior']}")
        print(f"  Keys: {result['exchangeablePriorKeys']}")

        print("\nShrinkage factor:")
        print(f"  Present: {result['hasShrinkage']}")

finally:
    driver.quit()
