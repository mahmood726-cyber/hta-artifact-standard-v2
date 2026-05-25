from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HTA_ROOT = Path(__file__).resolve().parents[1]
APPS_ROOT = HTA_ROOT.parent
ICON_DIR = HTA_ROOT / "icons"
SCREENSHOT_DIR = HTA_ROOT / "screenshots"


def ensure_dirs():
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def vertical_gradient(size, top_color, bottom_color):
    width, height = size
    base = Image.new("RGBA", size, top_color)
    draw = ImageDraw.Draw(base)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            int(top_color[i] + (bottom_color[i] - top_color[i]) * ratio)
            for i in range(3)
        ) + (255,)
        draw.line((0, y, width, y), fill=color)
    return base


def draw_centered_text(draw, box, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = box[0] + (box[2] - box[0] - text_w) / 2
    y = box[1] + (box[3] - box[1] - text_h) / 2 - 2
    draw.text((x, y), text, font=font, fill=fill)


def make_icon(size, label="HTA", accent=(37, 99, 235), card=(255, 255, 255)):
    img = vertical_gradient((size, size), (15, 23, 42), accent)
    img = img.filter(ImageFilter.GaussianBlur(radius=max(1, size // 64)))
    img = img.resize((size, size))
    draw = ImageDraw.Draw(img)

    outer_pad = max(10, size // 10)
    inner_box = (outer_pad, outer_pad, size - outer_pad, size - outer_pad)
    draw.rounded_rectangle(inner_box, radius=size // 5, fill=card)

    band_h = max(32, size // 4)
    band_box = (inner_box[0], inner_box[1], inner_box[2], inner_box[1] + band_h)
    draw.rounded_rectangle(band_box, radius=size // 5, fill=accent)
    draw.rectangle((band_box[0], band_box[1] + band_h // 2, band_box[2], band_box[3]), fill=accent)

    mono_font = load_font(max(18, size // 4), bold=True)
    sub_font = load_font(max(10, size // 10), bold=True)
    draw_centered_text(draw, band_box, label, mono_font, (255, 255, 255, 255))
    draw_centered_text(
        draw,
        (inner_box[0], inner_box[1] + band_h + size // 16, inner_box[2], inner_box[3] - size // 16),
        "MODEL",
        sub_font,
        (71, 85, 105, 255),
    )

    return img


def make_maskable(size):
    canvas = vertical_gradient((size, size), (2, 6, 23), (29, 78, 216))
    icon = make_icon(int(size * 0.72))
    offset = (size - icon.width) // 2
    canvas.paste(icon, (offset, offset), icon)
    return canvas


def make_shortcut_icon(label, accent):
    return make_icon(96, label=label, accent=accent)


def make_badge():
    size = 72
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((6, 6, size - 6, size - 6), fill=(37, 99, 235, 255))
    draw.ellipse((18, 18, size - 18, size - 18), fill=(255, 255, 255, 255))
    font = load_font(22, bold=True)
    draw_centered_text(draw, (0, 0, size, size), "H", font, (37, 99, 235, 255))
    return img


def draw_mock_card(draw, box, title, body, accent):
    draw.rounded_rectangle(box, radius=22, fill=(255, 255, 255, 255))
    draw.rounded_rectangle((box[0], box[1], box[2], box[1] + 46), radius=22, fill=accent)
    draw.rectangle((box[0], box[1] + 23, box[2], box[1] + 46), fill=accent)
    title_font = load_font(24, bold=True)
    body_font = load_font(16, bold=False)
    draw.text((box[0] + 20, box[1] + 10), title, font=title_font, fill=(255, 255, 255, 255))
    draw.text((box[0] + 20, box[1] + 70), body, font=body_font, fill=(51, 65, 85, 255))


def make_screenshot(size, wide):
    img = vertical_gradient(size, (241, 245, 249), (226, 232, 240))
    draw = ImageDraw.Draw(img)
    width, height = size

    header_h = 92
    draw.rounded_rectangle((24, 24, width - 24, header_h + 24), radius=28, fill=(255, 255, 255, 255))
    badge = make_icon(64)
    img.paste(badge, (42, 38), badge)
    title_font = load_font(28, bold=True)
    sub_font = load_font(16, bold=False)
    draw.text((128, 46), "HTA Artifact Standard", font=title_font, fill=(15, 23, 42, 255))
    draw.text((128, 80), "Meta-analysis, economic modeling, and decision support", font=sub_font, fill=(71, 85, 105, 255))

    sidebar_w = 280 if wide else width - 80
    content_x = 40 if not wide else sidebar_w + 64
    sidebar_box = (40, 150, 40 + sidebar_w, height - 40 if wide else 420)
    draw.rounded_rectangle(sidebar_box, radius=28, fill=(255, 255, 255, 230))
    sidebar_title = load_font(18, bold=True)
    draw.text((sidebar_box[0] + 20, sidebar_box[1] + 24), "FIND SECTION", font=sidebar_title, fill=(71, 85, 105, 255))
    draw.rounded_rectangle((sidebar_box[0] + 20, sidebar_box[1] + 64, sidebar_box[2] - 20, sidebar_box[1] + 114), radius=18, fill=(241, 245, 249, 255))
    draw.text((sidebar_box[0] + 36, sidebar_box[1] + 80), "Search sections (/)", font=sub_font, fill=(100, 116, 139, 255))
    draw.text((sidebar_box[0] + 20, sidebar_box[1] + 150), "RECENT", font=sidebar_title, fill=(71, 85, 105, 255))
    draw.rounded_rectangle((sidebar_box[0] + 20, sidebar_box[1] + 186, sidebar_box[0] + 152, sidebar_box[1] + 228), radius=18, fill=(239, 246, 255, 255))
    draw.text((sidebar_box[0] + 38, sidebar_box[1] + 198), "Summary", font=sub_font, fill=(30, 64, 175, 255))

    main_box = (
        content_x,
        150 if wide else 470,
        width - 40,
        height - 40,
    )
    draw.rounded_rectangle(main_box, radius=28, fill=(255, 255, 255, 245))
    draw.text((main_box[0] + 28, main_box[1] + 24), "Model Summary", font=load_font(30, bold=True), fill=(15, 23, 42, 255))

    card_w = (main_box[2] - main_box[0] - 84) // 3
    card_y = main_box[1] + 84
    accents = [(219, 234, 254, 255), (220, 252, 231, 255), (254, 242, 242, 255)]
    titles = [("Model Type", "markov_cohort"), ("Parameters", "9"), ("Time Horizon", "40 years")]
    for index, (title, value) in enumerate(titles):
        left = main_box[0] + 28 + index * (card_w + 14)
        draw.rounded_rectangle((left, card_y, left + card_w, card_y + 120), radius=22, fill=accents[index])
        draw.text((left + 20, card_y + 18), title, font=load_font(15, bold=False), fill=(71, 85, 105, 255))
        draw.text((left + 20, card_y + 54), value, font=load_font(28, bold=True), fill=(15, 23, 42, 255))

    draw_mock_card(draw, (main_box[0] + 28, card_y + 150, main_box[2] - 28, card_y + 310), "Model Structure", "Stable -> Progress -> Dead", (37, 99, 235, 255))
    return img


def save_icon_set():
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    base_512 = make_icon(512)
    for size in sizes:
        resized = base_512.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(ICON_DIR / f"icon-{size}x{size}.png")

    make_maskable(512).save(ICON_DIR / "maskable-icon-512x512.png")
    make_shortcut_icon("MA", (37, 99, 235)).save(ICON_DIR / "meta-analysis-96x96.png")
    make_shortcut_icon("LD", (14, 165, 233)).save(ICON_DIR / "load-model-96x96.png")
    make_shortcut_icon("LB", (168, 85, 247)).save(ICON_DIR / "library-96x96.png")
    make_shortcut_icon("RP", (249, 115, 22)).save(ICON_DIR / "report-96x96.png")
    make_badge().save(ICON_DIR / "badge-72x72.png")

    favicon = base_512.resize((64, 64), Image.Resampling.LANCZOS)
    favicon.save(HTA_ROOT / "favicon.ico", sizes=[(64, 64), (32, 32), (16, 16)])
    favicon.save(APPS_ROOT / "favicon.ico", sizes=[(64, 64), (32, 32), (16, 16)])


def save_screenshots():
    make_screenshot((1280, 720), wide=True).save(SCREENSHOT_DIR / "desktop-wide.png")
    make_screenshot((750, 1334), wide=False).save(SCREENSHOT_DIR / "desktop-narrow.png")


def main():
    ensure_dirs()
    save_icon_set()
    save_screenshots()
    print(f"Generated PWA assets in {HTA_ROOT}")


if __name__ == "__main__":
    main()
