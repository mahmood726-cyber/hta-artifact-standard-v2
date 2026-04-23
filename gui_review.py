"""
GUI Review Script for HTA Artifact Standard
Analyzes visual design, layout, and UX elements
"""

import time
import sys
import tempfile
from pathlib import Path
from _hta_url import hta_index_url, hta_index_path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

def setup_driver():
    """Setup Edge browser"""
    edge_options = EdgeOptions()
    edge_temp = tempfile.mkdtemp(prefix="hta_gui_review_")
    edge_options.add_argument(f"--user-data-dir={edge_temp}")
    edge_options.add_argument("--window-size=1920,1080")
    edge_options.add_argument("--disable-gpu")
    driver = webdriver.Edge(options=edge_options)
    return driver

def analyze_colors(driver):
    """Analyze color scheme and consistency"""
    print("\n" + "="*60)
    print("COLOR SCHEME ANALYSIS")
    print("="*60)

    issues = []

    # Check CSS variables
    css_vars = driver.execute_script("""
        const style = getComputedStyle(document.documentElement);
        return {
            primary: style.getPropertyValue('--primary'),
            secondary: style.getPropertyValue('--secondary'),
            success: style.getPropertyValue('--success'),
            warning: style.getPropertyValue('--warning'),
            danger: style.getPropertyValue('--danger'),
            bg: style.getPropertyValue('--bg'),
            bgCard: style.getPropertyValue('--bg-card'),
            text: style.getPropertyValue('--text'),
            textMuted: style.getPropertyValue('--text-muted'),
            border: style.getPropertyValue('--border')
        };
    """)

    print("\nCSS Variables defined:")
    for name, value in css_vars.items():
        if value.strip():
            print(f"  --{name}: {value.strip()}")
        else:
            issues.append(f"Missing CSS variable: --{name}")

    # Check for inline styles that override theme
    inline_styles = driver.execute_script("""
        const elements = document.querySelectorAll('[style*="color"], [style*="background"]');
        let count = 0;
        elements.forEach(el => {
            if (el.style.color || el.style.backgroundColor) count++;
        });
        return count;
    """)

    if inline_styles > 50:
        issues.append(f"Many inline color styles ({inline_styles}) - consider using CSS classes")

    # Check contrast
    header_bg = driver.execute_script("""
        const header = document.querySelector('.header');
        return header ? getComputedStyle(header).backgroundColor : null;
    """)

    print(f"\nHeader background: {header_bg}")

    return issues

def analyze_typography(driver):
    """Analyze typography and readability"""
    print("\n" + "="*60)
    print("TYPOGRAPHY ANALYSIS")
    print("="*60)

    issues = []

    # Check font families
    fonts = driver.execute_script("""
        const body = getComputedStyle(document.body);
        const h1 = document.querySelector('h1');
        const h2 = document.querySelector('h2');
        return {
            bodyFont: body.fontFamily,
            bodySize: body.fontSize,
            h1Size: h1 ? getComputedStyle(h1).fontSize : 'N/A',
            h2Size: h2 ? getComputedStyle(h2).fontSize : 'N/A'
        };
    """)

    print(f"\nBody font: {fonts['bodyFont']}")
    print(f"Body size: {fonts['bodySize']}")
    print(f"H1 size: {fonts['h1Size']}")
    print(f"H2 size: {fonts['h2Size']}")

    # Check for very small text
    small_text = driver.execute_script("""
        const elements = document.querySelectorAll('*');
        let smallCount = 0;
        elements.forEach(el => {
            const size = parseFloat(getComputedStyle(el).fontSize);
            if (size < 12 && el.textContent.trim().length > 0) smallCount++;
        });
        return smallCount;
    """)

    if small_text > 10:
        issues.append(f"Found {small_text} elements with font-size < 12px (readability concern)")

    return issues

def analyze_spacing(driver):
    """Analyze spacing and layout"""
    print("\n" + "="*60)
    print("SPACING & LAYOUT ANALYSIS")
    print("="*60)

    issues = []

    # Check card spacing
    cards = driver.find_elements(By.CLASS_NAME, "card")
    print(f"\nTotal cards: {len(cards)}")

    if cards:
        card_style = driver.execute_script("""
            const card = document.querySelector('.card');
            const style = getComputedStyle(card);
            return {
                padding: style.padding,
                margin: style.margin,
                borderRadius: style.borderRadius
            };
        """)
        print(f"Card padding: {card_style['padding']}")
        print(f"Card margin: {card_style['margin']}")
        print(f"Card border-radius: {card_style['borderRadius']}")

    # Check sidebar width
    sidebar = driver.execute_script("""
        const sidebar = document.querySelector('.sidebar');
        return sidebar ? {
            width: getComputedStyle(sidebar).width,
            padding: getComputedStyle(sidebar).padding
        } : null;
    """)

    if sidebar:
        print(f"\nSidebar width: {sidebar['width']}")
        print(f"Sidebar padding: {sidebar['padding']}")

    # Check for overlapping elements
    overflow = driver.execute_script("""
        let overflowCount = 0;
        document.querySelectorAll('*').forEach(el => {
            const style = getComputedStyle(el);
            if (style.overflow === 'visible' && el.scrollWidth > el.clientWidth) {
                overflowCount++;
            }
        });
        return overflowCount;
    """)

    if overflow > 5:
        issues.append(f"Found {overflow} elements with content overflow")

    return issues

def analyze_buttons(driver):
    """Analyze button styles and consistency"""
    print("\n" + "="*60)
    print("BUTTON ANALYSIS")
    print("="*60)

    issues = []

    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\nTotal buttons: {len(buttons)}")

    # Check button classes
    btn_classes = driver.execute_script("""
        const buttons = document.querySelectorAll('button');
        const classes = {};
        buttons.forEach(btn => {
            btn.classList.forEach(cls => {
                classes[cls] = (classes[cls] || 0) + 1;
            });
        });
        return classes;
    """)

    print("\nButton class distribution:")
    for cls, count in sorted(btn_classes.items(), key=lambda x: -x[1])[:10]:
        print(f"  .{cls}: {count}")

    # Check for buttons without proper styling
    unstyled = driver.execute_script("""
        const buttons = document.querySelectorAll('button');
        let unstyled = 0;
        buttons.forEach(btn => {
            if (!btn.classList.contains('btn') &&
                !btn.classList.contains('btn-primary') &&
                !btn.classList.contains('btn-secondary')) {
                unstyled++;
            }
        });
        return unstyled;
    """)

    if unstyled > 0:
        issues.append(f"Found {unstyled} buttons without standard btn class")

    # Check button sizes
    btn_sizes = driver.execute_script("""
        const buttons = document.querySelectorAll('button.btn');
        const sizes = [];
        buttons.forEach(btn => {
            const style = getComputedStyle(btn);
            sizes.push({
                text: btn.textContent.trim().substring(0, 20),
                padding: style.padding,
                fontSize: style.fontSize
            });
        });
        return sizes.slice(0, 5);
    """)

    print("\nSample button styles:")
    for btn in btn_sizes:
        print(f"  '{btn['text']}': padding={btn['padding']}, font={btn['fontSize']}")

    return issues

def analyze_forms(driver):
    """Analyze form elements"""
    print("\n" + "="*60)
    print("FORM ELEMENTS ANALYSIS")
    print("="*60)

    issues = []

    # Check inputs
    inputs = driver.find_elements(By.TAG_NAME, "input")
    selects = driver.find_elements(By.TAG_NAME, "select")

    print(f"\nTotal inputs: {len(inputs)}")
    print(f"Total selects: {len(selects)}")

    # Check for labels
    labels = driver.find_elements(By.TAG_NAME, "label")
    print(f"Total labels: {len(labels)}")

    if len(labels) < len(inputs) + len(selects):
        issues.append("Some form elements may be missing labels (accessibility concern)")

    # Check input styling consistency
    input_styles = driver.execute_script("""
        const inputs = document.querySelectorAll('input[type="text"], input[type="number"]');
        const styles = new Set();
        inputs.forEach(input => {
            const style = getComputedStyle(input);
            styles.add(`${style.padding}|${style.borderRadius}|${style.border}`);
        });
        return styles.size;
    """)

    if input_styles > 3:
        issues.append(f"Inconsistent input styling ({input_styles} different styles)")

    return issues

def analyze_navigation(driver):
    """Analyze navigation UX"""
    print("\n" + "="*60)
    print("NAVIGATION ANALYSIS")
    print("="*60)

    issues = []

    nav_items = driver.find_elements(By.CLASS_NAME, "nav-item")
    print(f"\nTotal nav items: {len(nav_items)}")

    # Check nav item styling
    nav_style = driver.execute_script("""
        const navItem = document.querySelector('.nav-item');
        if (!navItem) return null;
        const style = getComputedStyle(navItem);
        return {
            padding: style.padding,
            color: style.color,
            fontSize: style.fontSize,
            gap: style.gap
        };
    """)

    if nav_style:
        print(f"\nNav item style:")
        print(f"  Padding: {nav_style['padding']}")
        print(f"  Color: {nav_style['color']}")
        print(f"  Font size: {nav_style['fontSize']}")

    # Check active state
    active_style = driver.execute_script("""
        const active = document.querySelector('.nav-item.active');
        if (!active) return null;
        const style = getComputedStyle(active);
        return {
            background: style.backgroundColor,
            color: style.color
        };
    """)

    if active_style:
        print(f"\nActive nav item:")
        print(f"  Background: {active_style['background']}")
        print(f"  Color: {active_style['color']}")

    # Check if sidebar is scrollable
    sidebar_scroll = driver.execute_script("""
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return null;
        return {
            scrollHeight: sidebar.scrollHeight,
            clientHeight: sidebar.clientHeight,
            overflow: getComputedStyle(sidebar).overflowY
        };
    """)

    if sidebar_scroll:
        print(f"\nSidebar scrolling:")
        print(f"  Content height: {sidebar_scroll['scrollHeight']}px")
        print(f"  Visible height: {sidebar_scroll['clientHeight']}px")
        print(f"  Overflow: {sidebar_scroll['overflow']}")

        if sidebar_scroll['scrollHeight'] > sidebar_scroll['clientHeight'] and sidebar_scroll['overflow'] == 'visible':
            issues.append("Sidebar content overflows but may not be scrollable")

    return issues

def analyze_charts(driver):
    """Analyze chart presentation"""
    print("\n" + "="*60)
    print("CHART PRESENTATION ANALYSIS")
    print("="*60)

    issues = []

    canvases = driver.find_elements(By.TAG_NAME, "canvas")
    print(f"\nTotal chart canvases: {len(canvases)}")

    # Check chart container sizing
    chart_containers = driver.execute_script("""
        const containers = document.querySelectorAll('.chart-container');
        return Array.from(containers).slice(0, 5).map(c => ({
            height: getComputedStyle(c).height,
            width: getComputedStyle(c).width,
            id: c.querySelector('canvas')?.id || 'unknown'
        }));
    """)

    print("\nSample chart container sizes:")
    for container in chart_containers:
        print(f"  {container['id']}: {container['width']} x {container['height']}")

    return issues

def analyze_responsiveness(driver):
    """Check responsive design elements"""
    print("\n" + "="*60)
    print("RESPONSIVENESS ANALYSIS")
    print("="*60)

    issues = []

    # Check for media queries in stylesheets
    media_queries = driver.execute_script("""
        let mqCount = 0;
        for (const sheet of document.styleSheets) {
            try {
                for (const rule of sheet.cssRules) {
                    if (rule.type === CSSRule.MEDIA_RULE) mqCount++;
                }
            } catch (e) {}
        }
        return mqCount;
    """)

    print(f"\nMedia queries found: {media_queries}")

    if media_queries < 3:
        issues.append("Limited media queries - may not be fully responsive")

    # Check viewport meta tag
    viewport = driver.execute_script("""
        const meta = document.querySelector('meta[name="viewport"]');
        return meta ? meta.content : null;
    """)

    print(f"Viewport meta: {viewport}")

    if not viewport:
        issues.append("Missing viewport meta tag")

    return issues

def analyze_accessibility(driver):
    """Basic accessibility checks"""
    print("\n" + "="*60)
    print("ACCESSIBILITY ANALYSIS")
    print("="*60)

    issues = []

    # Check for alt text on images
    images = driver.execute_script("""
        const imgs = document.querySelectorAll('img');
        let missingAlt = 0;
        imgs.forEach(img => {
            if (!img.alt) missingAlt++;
        });
        return { total: imgs.length, missingAlt };
    """)

    print(f"\nImages: {images['total']} total, {images['missingAlt']} missing alt text")

    if images['missingAlt'] > 0:
        issues.append(f"{images['missingAlt']} images missing alt text")

    # Check for ARIA labels
    aria_labels = driver.execute_script("""
        return document.querySelectorAll('[aria-label]').length;
    """)

    print(f"Elements with aria-label: {aria_labels}")

    # Check focus styles
    focus_styles = driver.execute_script("""
        const style = document.createElement('style');
        document.head.appendChild(style);
        const sheet = style.sheet;
        let hasFocusStyles = false;
        for (const s of document.styleSheets) {
            try {
                for (const rule of s.cssRules) {
                    if (rule.selectorText && rule.selectorText.includes(':focus')) {
                        hasFocusStyles = true;
                        break;
                    }
                }
            } catch (e) {}
        }
        return hasFocusStyles;
    """)

    print(f"Focus styles defined: {focus_styles}")

    if not focus_styles:
        issues.append("No :focus styles found (keyboard navigation concern)")

    return issues

def analyze_visual_hierarchy(driver):
    """Analyze visual hierarchy and emphasis"""
    print("\n" + "="*60)
    print("VISUAL HIERARCHY ANALYSIS")
    print("="*60)

    issues = []

    # Check heading hierarchy
    headings = driver.execute_script("""
        const headings = {};
        for (let i = 1; i <= 6; i++) {
            headings[`h${i}`] = document.querySelectorAll(`h${i}`).length;
        }
        return headings;
    """)

    print("\nHeading distribution:")
    for tag, count in headings.items():
        if count > 0:
            print(f"  {tag}: {count}")

    # Check for visual emphasis elements
    emphasis = driver.execute_script("""
        return {
            bold: document.querySelectorAll('strong, b').length,
            highlight: document.querySelectorAll('.highlight, .result-highlight').length,
            badges: document.querySelectorAll('.badge, .nav-badge').length,
            alerts: document.querySelectorAll('.alert, .warning, .error').length
        };
    """)

    print("\nEmphasis elements:")
    for elem, count in emphasis.items():
        print(f"  {elem}: {count}")

    return issues

def generate_recommendations(all_issues):
    """Generate improvement recommendations"""
    print("\n" + "="*60)
    print("GUI IMPROVEMENT RECOMMENDATIONS")
    print("="*60)

    recommendations = [
        "1. VISUAL POLISH:",
        "   - Add subtle shadows to cards for depth (box-shadow: 0 2px 8px rgba(0,0,0,0.1))",
        "   - Consider adding hover animations to interactive elements",
        "   - Use consistent border-radius across all components",
        "",
        "2. COLOR REFINEMENTS:",
        "   - Ensure sufficient contrast ratio (4.5:1) for text",
        "   - Add dark mode support using CSS variables",
        "   - Use color to indicate state (success=green, warning=amber, error=red)",
        "",
        "3. TYPOGRAPHY:",
        "   - Ensure minimum 14px font size for body text",
        "   - Use font-weight variations for hierarchy (400, 500, 600, 700)",
        "   - Add letter-spacing to headings for better readability",
        "",
        "4. SPACING:",
        "   - Use consistent spacing scale (8px, 16px, 24px, 32px, 48px)",
        "   - Add more whitespace around major sections",
        "   - Ensure adequate padding in cards and containers",
        "",
        "5. NAVIGATION:",
        "   - Add smooth scroll behavior",
        "   - Consider collapsible nav sections for long menus",
        "   - Add visual indicator for current section (breadcrumb or highlight)",
        "",
        "6. ACCESSIBILITY:",
        "   - Add skip-to-content link",
        "   - Ensure all interactive elements have focus styles",
        "   - Add aria-labels to icon-only buttons",
        "",
        "7. RESPONSIVENESS:",
        "   - Add breakpoints for tablet (768px) and mobile (480px)",
        "   - Make sidebar collapsible on smaller screens",
        "   - Ensure charts resize properly",
    ]

    for rec in recommendations:
        print(rec)

    if all_issues:
        print("\n" + "="*60)
        print("SPECIFIC ISSUES TO ADDRESS")
        print("="*60)
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")

def main():
    print("="*60)
    print("HTA ARTIFACT STANDARD - GUI REVIEW")
    print("="*60)

    file_path = hta_index_path().resolve()
    print(f"\nReviewing: {file_path}")

    driver = setup_driver()
    all_issues = []

    try:
        driver.get(f"file:///{file_path}")
        time.sleep(2)

        # Click demo to load content
        demo_btn = driver.find_element(By.ID, "btn-demo")
        driver.execute_script("arguments[0].click();", demo_btn)
        time.sleep(3)

        # Run all analyses
        all_issues.extend(analyze_colors(driver))
        all_issues.extend(analyze_typography(driver))
        all_issues.extend(analyze_spacing(driver))
        all_issues.extend(analyze_buttons(driver))
        all_issues.extend(analyze_forms(driver))
        all_issues.extend(analyze_navigation(driver))
        all_issues.extend(analyze_charts(driver))
        all_issues.extend(analyze_responsiveness(driver))
        all_issues.extend(analyze_accessibility(driver))
        all_issues.extend(analyze_visual_hierarchy(driver))

        # Generate recommendations
        generate_recommendations(all_issues)

        print("\n" + "="*60)
        print(f"TOTAL ISSUES FOUND: {len(all_issues)}")
        print("="*60)

        print("\nKeeping browser open for 10 seconds for visual inspection...")
        time.sleep(10)

    finally:
        driver.quit()
        print("\nBrowser closed.")

if __name__ == "__main__":
    main()
