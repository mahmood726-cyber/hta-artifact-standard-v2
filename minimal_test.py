"""Minimal browser smoke script for HTA Artifact Standard."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time

from _hta_url import hta_index_url
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _build_driver() -> webdriver.Edge:
    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    temp = tempfile.mkdtemp(prefix="hta_min_")
    options.add_argument(f"--user-data-dir={temp}")
    return webdriver.Edge(options=options)


def run_smoke() -> bool:
    subprocess.run(
        ["taskkill", "/F", "/IM", "msedgedriver.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        ["taskkill", "/F", "/IM", "msedge.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    time.sleep(2)

    print("Starting Edge...")
    driver = _build_driver()
    try:
        driver.get(hta_index_url())
        time.sleep(2)

        print("\n=== Quick Verification ===\n")

        driver.execute_script("document.getElementById('btn-demo').click()")
        time.sleep(2)
        demo_loaded = driver.execute_script(
            "return window.htaModel && window.htaModel.states && window.htaModel.states.length > 0"
        )
        print(f"Demo loads: {'PASS' if demo_loaded else 'FAIL'}")

        core_funcs = ["runAnalysis", "runPSA", "runEVPPI", "runCalibration"]
        core_ok = all(driver.execute_script(f"return typeof window.{name} === 'function'") for name in core_funcs)
        print(f"Core functions: {'PASS' if core_ok else 'FAIL'}")

        new_classes = [
            "HKSJAdjustment",
            "CopasSelectionModel",
            "ProfileLikelihoodCI",
            "RoystonParmarSurvival",
            "MCMCDiagnostics",
            "MultivariateMetaAnalysis",
            "NetworkMetaRegression",
            "MixtureCureModel",
            "GRADEAssessment",
            "ValidationReport",
        ]
        adv_ok = all(driver.execute_script(f"return typeof window.{name} === 'function'") for name in new_classes)
        print(f"Advanced enhancements (10 classes): {'PASS' if adv_ok else 'FAIL'}")

        hksj_result = driver.execute_script(
            """
            try {
                const h = new HKSJAdjustment();
                const r = h.adjust([{effect:0.5,se:0.1},{effect:0.3,se:0.2},{effect:0.4,se:0.15}], 0.01, 0.4);
                return r.ci_lower < r.effect && r.effect < r.ci_upper;
            } catch(e) { return false; }
            """
        )
        print(f"HKSJ adjustment: {'PASS' if hksj_result else 'FAIL'}")

        mcmc_result = driver.execute_script(
            """
            try {
                const m = new MCMCDiagnostics();
                const chains = [Array.from({length:100}, () => Math.random()),
                               Array.from({length:100}, () => Math.random())];
                const r = m.analyze(chains);
                return r.gelmanRubin && r.effectiveSampleSize && r.geweke;
            } catch(e) { return false; }
            """
        )
        print(f"MCMC diagnostics: {'PASS' if mcmc_result else 'FAIL'}")

        grade_result = driver.execute_script(
            """
            try {
                const g = new GRADEAssessment();
                const r = g.assess({studyDesign:'RCT', riskOfBias:{overall:'low'}});
                return r.overallCertainty && r.score !== undefined;
            } catch(e) { return false; }
            """
        )
        print(f"GRADE assessment: {'PASS' if grade_result else 'FAIL'}")

        logs = driver.get_log("browser")
        errors = [entry for entry in logs if entry["level"] == "SEVERE" and "Error" in entry["message"]]
        print(f"\nConsole errors: {len(errors)}")

        all_pass = demo_loaded and core_ok and adv_ok and hksj_result and mcmc_result and grade_result
        print("\n" + "=" * 50)
        print(f"OVERALL: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
        print("=" * 50)
        return bool(all_pass)
    finally:
        driver.quit()


def main() -> int:
    return 0 if run_smoke() else 1


if __name__ == "__main__":
    raise SystemExit(main())
