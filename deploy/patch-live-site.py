#!/usr/bin/env python3
"""Resize the logos and add the consultation form on an already deployed site."""

import re
import struct
import zlib
from pathlib import Path

ROOT = Path("/var/www/richardwinfred")

FORM = """<section class="cta" id="contact"><div class="wrap cta-in">
  <div class="reveal"><h2>Let's talk about your technology environment.</h2><p>Project, incident, multi-site, or ongoing support — tell us what you're solving.</p><p class="cta-phone"><a class="tel" href="tel:+12812130055">+1 281 213 0055</a></p></div>
  <form class="book reveal" id="consult-form" action="/api/consultation" method="post">
    <label for="consult-name">Name</label>
    <input id="consult-name" name="name" required maxlength="80" autocomplete="name">
    <label for="consult-email">Email</label>
    <input id="consult-email" name="email" type="email" required maxlength="120" autocomplete="email">
    <label for="consult-phone">Phone</label>
    <input id="consult-phone" name="phone" type="tel" maxlength="40" autocomplete="tel">
    <label for="consult-company">Company</label>
    <input id="consult-company" name="company" maxlength="80" autocomplete="organization">
    <label for="consult-message">What do you need?</label>
    <textarea id="consult-message" name="message" required maxlength="2000"></textarea>
    <div class="hp"><label for="consult-website">Website</label><input id="consult-website" name="website" tabindex="-1" autocomplete="off"></div>
    <button class="btn btn-w" type="submit">Book a consultation</button>
    <p class="form-status" id="form-status" role="status"></p>
  </form>
</div></section>"""

CSS = """
.logo img{height:32px;width:auto;max-width:200px;object-fit:contain;object-position:left center;display:block}
.fb-logo{height:26px;width:auto;max-width:170px;object-fit:contain;object-position:left center;display:block;background:transparent}
.cta-phone{margin-top:18px}
.cta a.tel{margin-left:0}
.book{width:min(100%,420px);display:grid;gap:6px}
.book label{font-size:13px;font-weight:600;color:#fff;margin-top:6px}
.book input,.book textarea{width:100%;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.08);color:#fff;border-radius:10px;padding:12px 14px;font:inherit}
.book textarea{min-height:108px;resize:vertical}
.book .btn{justify-self:start;margin-top:8px}
.form-status{min-height:1.2em;font-size:14px;color:#fff}
.hp{position:absolute;left:-9999px;height:0;overflow:hidden}
"""

JS = """
const consultForm = document.getElementById('consult-form');
const formStatus = document.getElementById('form-status');
if (consultForm && formStatus) {
  consultForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submit = consultForm.querySelector('button[type="submit"]');
    submit.disabled = true;
    formStatus.textContent = 'Sending…';
    try {
      const response = await fetch(consultForm.action, {
        method: 'POST',
        headers: { Accept: 'application/json', 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(new FormData(consultForm)),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload.ok) throw new Error(payload.error || 'Please try again.');
      consultForm.reset();
      formStatus.textContent = 'Request received. We will reply by email.';
    } catch (error) {
      formStatus.textContent = error.message || 'Please try again, or email info@richardwinfred.com.';
    } finally {
      submit.disabled = false;
    }
  });
}
"""


def read_png(path):
    data = Path(path).read_bytes()
    pos = 8
    width = height = color_type = None
    idat = b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, _, color_type = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
    raw = zlib.decompress(idat)
    bpp = {2: 3, 6: 4}[color_type]
    rows, i, stride, prev = [], 0, width * bpp, bytearray(width * bpp)

    def paeth(a, b, c):
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        return a if pa <= pb and pa <= pc else (b if pb <= pc else c)

    for _y in range(height):
        filt = raw[i]
        i += 1
        row = bytearray(raw[i:i + stride])
        i += stride
        if filt == 1:
            for x in range(stride):
                row[x] = (row[x] + (row[x - bpp] if x >= bpp else 0)) & 255
        elif filt == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 255
        elif filt == 3:
            for x in range(stride):
                left = row[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + ((left + prev[x]) // 2)) & 255
        elif filt == 4:
            for x in range(stride):
                a = row[x - bpp] if x >= bpp else 0
                b, c = prev[x], prev[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + paeth(a, b, c)) & 255
        rows.append(row)
        prev = row
    return width, height, bpp, rows


def write_png(path, w, h, pixels, color_type):
    bpp = 4 if color_type == 6 else 3

    def chunk(tag, payload):
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(pixels[y * w * bpp:(y + 1) * w * bpp])
    ihdr = struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def is_bg(r, g, b):
    return r > 242 and g > 242 and b > 242


def is_gold(r, g, b):
    return r > 130 and r > g + 12 and g > b + 15 and b < 140 and g > 70


def rebuild_logos():
    src = ROOT / "assets/img/logo.png"
    w, h, bpp, rows = read_png(src)
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        row = rows[y]
        for x in range(w):
            r, g, b = row[x * bpp], row[x * bpp + 1], row[x * bpp + 2]
            if not is_bg(r, g, b):
                minx, miny, maxx, maxy = min(minx, x), min(miny, y), max(maxx, x), max(maxy, y)
    pad = 6
    x0, y0 = max(0, minx - pad), max(0, miny - pad)
    x1, y1 = min(w - 1, maxx + pad), min(h - 1, maxy + pad)
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    rgb, rgba = bytearray(cw * ch * 3), bytearray(cw * ch * 4)
    for y in range(ch):
        row = rows[y0 + y]
        for x in range(cw):
            r, g, b = row[(x0 + x) * bpp], row[(x0 + x) * bpp + 1], row[(x0 + x) * bpp + 2]
            rgb[(y * cw + x) * 3:(y * cw + x) * 3 + 3] = bytes((r, g, b))
            if is_bg(r, g, b):
                continue
            i4 = (y * cw + x) * 4
            if is_gold(r, g, b):
                rgba[i4:i4 + 4] = bytes((r, g, b, 255))
            else:
                alpha = max(0, min(255, 255 - (r + g + b) // 3))
                if alpha >= 12:
                    rgba[i4:i4 + 4] = bytes((255, 255, 255, alpha))
    write_png(src, cw, ch, rgb, 2)
    write_png(ROOT / "assets/img/logo-white.png", cw, ch, rgba, 6)
    print(f"logos cropped to {cw}x{ch}")


def patch_html():
    path = ROOT / "index.html"
    html = path.read_text(encoding="utf-8")
    html = re.sub(r'(<img\b[^>]*logo\.png"[^>]*?)(?:\sstyle="[^"]*")?', r"\1", html, count=1)
    html = re.sub(r'(<img\b[^>]*logo-white\.png"[^>]*?)(?:\sstyle="[^"]*")?', r"\1", html, count=1)

    def size(match, width, height):
        tag = re.sub(r'\s(?:width|height)="\d+"', "", match.group(0))
        return tag[:-1] + f' width="{width}" height="{height}">'

    html = re.sub(r'<img\b[^>]*logo\.png"[^>]*>', lambda m: size(m, 213, 32), html, count=1)
    html = re.sub(r'<img\b[^>]*logo-white\.png"[^>]*>', lambda m: size(m, 173, 26), html, count=1)
    if 'id="consult-form"' not in html:
        html, n = re.subn(r'<section class="cta" id="contact"[\s\S]*?</section>', FORM, html, count=1)
        if n != 1:
            raise SystemExit("Could not find the contact section in index.html")
    if "consult-form" not in (ROOT / "assets/js/main.js").read_text(encoding="utf-8"):
        (ROOT / "assets/js/main.js").write_text((ROOT / "assets/js/main.js").read_text(encoding="utf-8") + "\n" + JS, encoding="utf-8")
    path.write_text(html, encoding="utf-8")
    css = ROOT / "assets/css/style.css"
    text = css.read_text(encoding="utf-8")
    if ".book input" not in text:
        css.write_text(text + CSS, encoding="utf-8")
    print("page updated")


if __name__ == "__main__":
    rebuild_logos()
    patch_html()
