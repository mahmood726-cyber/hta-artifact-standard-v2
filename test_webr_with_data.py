"""Test WebR with BCG data injected via JS"""
import sys, io, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from selenium import webdriver
from selenium.webdriver.edge.options import Options

options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1440,900')
options.add_argument('--disable-gpu')

print("Starting Edge...")
driver = webdriver.Edge(options=options)
driver.set_page_load_timeout(60)
os.makedirs("Submission", exist_ok=True)

try:
    print("Loading app...")
    driver.get("http://localhost:8768/index.html")
    time.sleep(5)

    # Navigate to Meta-Analysis tab
    driver.execute_script("""
        var tabs = document.querySelectorAll('[data-section], button');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].textContent.indexOf('Meta-Analysis') >= 0 &&
                tabs[i].textContent.indexOf('IPD') < 0 &&
                tabs[i].textContent.indexOf('DTA') < 0 &&
                tabs[i].textContent.indexOf('MR') < 0) {
                tabs[i].click(); break;
            }
        }
    """)
    time.sleep(2)

    # Try to load demo data or inject BCG data
    print("Injecting BCG vaccine data...")
    driver.execute_script("""
        // BCG vaccine data: 6 largest studies (log OR and SE)
        var bcgData = [
            {name: 'Aronson 1948', yi: -0.9387, se: 0.5976},
            {name: 'Ferguson 1949', yi: -1.6662, se: 0.4562},
            {name: 'Rosenthal 1960', yi: -1.3863, se: 0.6583},
            {name: 'Hart 1977', yi: -1.4564, se: 0.1425},
            {name: 'Frimodt-Moller 1973', yi: -0.2191, se: 0.2279},
            {name: 'Comstock 1974', yi: -0.6815, se: 0.0914}
        ];

        // Try to find and populate the MA data table
        var tbody = document.getElementById('ma-data-body');
        if (tbody) {
            tbody.innerHTML = '';
            bcgData.forEach(function(d, i) {
                var tr = document.createElement('tr');
                tr.innerHTML = '<td>' + (i+1) + '</td><td><input class="ma-study-name" value="' + d.name + '"></td><td><input class="ma-yi" type="number" step="any" value="' + d.yi + '"></td><td><input class="ma-sei" type="number" step="any" value="' + d.se + '"></td><td><button onclick="this.closest(\\\"tr\\\").remove()">x</button></td>';
                tbody.appendChild(tr);
            });
            console.log('BCG data injected: ' + bcgData.length + ' studies');
        } else {
            console.log('ma-data-body not found');
        }
    """)
    time.sleep(1)

    rows = driver.execute_script("return document.querySelectorAll('#ma-data-body tr').length;")
    print(f"Data rows after injection: {rows}")

    # Navigate to validation tab
    print("Going to Validation tab...")
    driver.execute_script("""
        var tabs = document.querySelectorAll('[data-section], button');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].textContent.indexOf('Validation') >= 0) { tabs[i].click(); break; }
        }
    """)
    time.sleep(2)

    webr_exists = driver.execute_script("return !!document.getElementById('webrRunBtn');")
    print(f"WebR button: {webr_exists}")

    if webr_exists and rows > 0:
        driver.execute_script("document.getElementById('webrRunBtn').scrollIntoView({block: 'center'});")
        time.sleep(1)

        print("Clicking WebR... (30-90s for metafor install)")
        driver.execute_script("document.getElementById('webrRunBtn').click();")

        for i in range(20):
            time.sleep(5)
            status = driver.execute_script("""
                var badge = document.getElementById('webrBadge');
                var prog = document.getElementById('webrProgressText') || document.querySelector('[id*="webrProgress"]');
                var res = document.getElementById('webrResults') || document.getElementById('webrResultsContainer');
                return {
                    badge: badge ? badge.textContent.trim() : '',
                    progress: prog ? prog.textContent.trim() : '',
                    hasResults: res ? res.innerHTML.length > 50 : false,
                    resultPreview: res ? res.textContent.substring(0, 100) : ''
                };
            """)
            print(f"  [{(i+1)*5}s] badge='{status['badge']}' prog='{status['progress']}' hasResults={status['hasResults']}")

            if status['badge'] and ('GOLD' in status['badge'].upper() or 'FALLBACK' in status['badge'].upper() or 'VALIDATED' in status['badge'].upper() or 'ERROR' in status['badge'].upper()):
                print(f"  Completed! Badge: {status['badge']}")
                break
            if status['hasResults'] and status['badge']:
                print(f"  Has results! Badge: {status['badge']}")
                break

        # Screenshot the results
        driver.execute_script("""
            var r = document.getElementById('webrResults') || document.getElementById('webrResultsContainer');
            if (r) r.scrollIntoView({block: 'start'});
        """)
        time.sleep(1)
        driver.save_screenshot("Submission/Figure_5_WebR_Results.png")
        print("-> Figure_5_WebR_Results.png")

        full = driver.execute_script("""
            var r = document.getElementById('webrResults') || document.getElementById('webrResultsContainer');
            return r ? r.textContent : 'empty';
        """)
        print(f"\nWebR Results:\n{full[:600]}")
    else:
        print(f"Cannot test WebR: button={webr_exists}, rows={rows}")

    # Check console errors
    logs = driver.get_log('browser')
    errors = [l for l in logs if l['level'] == 'SEVERE']
    warnings = [l for l in logs if l['level'] == 'WARNING' and 'webr' in l['message'].lower()]
    print(f"\nConsole: {len(errors)} errors, {len(warnings)} webr warnings")
    for e in errors[:3]:
        print(f"  ERR: {e['message'][:120]}")
    for w in warnings[:3]:
        print(f"  WARN: {w['message'][:120]}")

    print(f"\n=== DONE ===\nFiles: {os.listdir('Submission/')}")

finally:
    driver.quit()
