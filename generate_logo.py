"""Generate BLE Security System app logo."""
from PIL import Image, ImageDraw, ImageFont
import math, os

SIZE = 512
CENTER = SIZE // 2
img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# ── Background: rounded dark circle with subtle gradient feel ──
for r in range(SIZE // 2, 0, -1):
    frac = r / (SIZE // 2)
    # Dark center to slightly lighter edge
    c = int(12 + 8 * (1 - frac))
    alpha = 255
    draw.ellipse(
        [CENTER - r, CENTER - r, CENTER + r, CENTER + r],
        fill=(c, c, int(c * 1.2), alpha))

# ── Outer glow ring ──
ring_r = SIZE // 2 - 4
for i in range(6):
    rr = ring_r - i
    alpha = int(60 - i * 10)
    draw.ellipse(
        [CENTER - rr, CENTER - rr, CENTER + rr, CENTER + rr],
        outline=(0, 220, 220, alpha), width=2)

# ── Inner accent ring ──
inner_ring = int(SIZE * 0.42)
draw.ellipse(
    [CENTER - inner_ring, CENTER - inner_ring,
     CENTER + inner_ring, CENTER + inner_ring],
    outline=(0, 180, 200, 45), width=2)

# ── Shield shape ──
shield_w = int(SIZE * 0.32)
shield_h = int(SIZE * 0.40)
shield_top = CENTER - int(shield_h * 0.52)

# Shield path points
pts = []
steps = 40
# Top-left curve to top-right
for i in range(steps + 1):
    t = i / steps
    x = CENTER - shield_w + t * 2 * shield_w
    # Slight curve at top
    y_off = -int(shield_h * 0.05 * math.sin(math.pi * t))
    pts.append((x, shield_top + y_off))
# Right side curving down to bottom point
for i in range(1, steps + 1):
    t = i / steps
    x = CENTER + shield_w * (1 - t * t)
    y = shield_top + t * shield_h
    pts.append((int(x), int(y)))
# Bottom point
pts.append((CENTER, shield_top + shield_h + int(shield_h * 0.15)))
# Left side curving up
for i in range(1, steps + 1):
    t = i / steps
    x = CENTER - shield_w * (1 - (1 - t) * (1 - t))
    y = shield_top + (1 - t) * shield_h
    pts.append((int(x), int(y)))

# Shield fill with gradient effect (draw multiple smaller shields)
for offset in range(12, 0, -1):
    frac = offset / 12
    r_col = int(0 + 10 * frac)
    g_col = int(60 + 100 * (1 - frac))
    b_col = int(70 + 120 * (1 - frac))
    shrunk = []
    for px, py in pts:
        dx = px - CENTER
        dy = py - (shield_top + shield_h * 0.5)
        factor = 1 - offset * 0.008
        shrunk.append((CENTER + dx * factor, shield_top + shield_h * 0.5 + dy * factor))
    draw.polygon(shrunk, fill=(r_col, g_col, b_col, 200 - offset * 8))

# Shield outline
draw.polygon(pts, outline=(0, 220, 220, 200), fill=None)

# ── Bluetooth symbol ──
bt_cx, bt_cy = CENTER, CENTER + 5
bt_h = int(SIZE * 0.22)
bt_w = int(SIZE * 0.10)
line_w = int(SIZE * 0.022)

# Bluetooth rune: vertical line + two chevrons
# Vertical line
draw.line([(bt_cx, bt_cy - bt_h), (bt_cx, bt_cy + bt_h)],
          fill=(220, 240, 255, 240), width=line_w)

# Top-right chevron (forms the B shape top)
draw.line([(bt_cx, bt_cy - bt_h), (bt_cx + bt_w, bt_cy - bt_h // 2)],
          fill=(220, 240, 255, 240), width=line_w)
draw.line([(bt_cx + bt_w, bt_cy - bt_h // 2), (bt_cx - bt_w, bt_cy + bt_h // 2)],
          fill=(220, 240, 255, 240), width=line_w)

# Bottom-right chevron
draw.line([(bt_cx, bt_cy + bt_h), (bt_cx + bt_w, bt_cy + bt_h // 2)],
          fill=(220, 240, 255, 240), width=line_w)
draw.line([(bt_cx + bt_w, bt_cy + bt_h // 2), (bt_cx - bt_w, bt_cy - bt_h // 2)],
          fill=(220, 240, 255, 240), width=line_w)

# ── Small lock icon at bottom of shield ──
lock_cx = CENTER
lock_cy = CENTER + int(SIZE * 0.22)
lock_w = int(SIZE * 0.05)
lock_h = int(SIZE * 0.04)

# Lock body
draw.rounded_rectangle(
    [lock_cx - lock_w, lock_cy, lock_cx + lock_w, lock_cy + lock_h],
    radius=3, fill=(0, 200, 200, 180))
# Lock shackle
draw.arc(
    [lock_cx - lock_w + 4, lock_cy - lock_h + 2,
     lock_cx + lock_w - 4, lock_cy + 4],
    start=180, end=0, fill=(0, 200, 200, 180), width=3)

# ── Decorative scan arcs (left & right of shield) ──
for side in [-1, 1]:
    for i, (r, a) in enumerate([(180, 40), (200, 30), (220, 20)]):
        alpha = int(80 - i * 25)
        arc_x = CENTER + side * int(SIZE * 0.02)
        draw.arc(
            [arc_x - r, CENTER - r, arc_x + r, CENTER + r],
            start=(-30 + 180) if side == 1 else -30,
            end=(30 + 180) if side == 1 else 30,
            fill=(0, 220, 220, alpha), width=3)

# ── Save outputs ──
out_dir = os.path.dirname(os.path.abspath(__file__))

# PNG (512x512)
png_path = os.path.join(out_dir, 'app_icon.png')
img.save(png_path, 'PNG')
print(f"Saved: {png_path}")

# ICO (multi-size)
ico_path = os.path.join(out_dir, 'app_icon.ico')
sizes = [16, 32, 48, 64, 128, 256]
ico_images = [img.resize((s, s), Image.LANCZOS) for s in sizes]
ico_images[0].save(ico_path, format='ICO',
                   sizes=[(s, s) for s in sizes],
                   append_images=ico_images[1:])
print(f"Saved: {ico_path}")
print("Done!")
