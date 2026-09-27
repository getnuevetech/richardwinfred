#!/usr/bin/env python3
"""Accept consultation bookings and email them to the company."""

import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8787
TO = os.environ.get("CONSULT_TO", "info@richardwinfred.com")
STORE = Path(os.environ.get("CONSULT_STORE", "/var/lib/richardwinfred/consultations"))
DELIVER = os.environ.get("CONSULT_DELIVER", "formsubmit")
MAX_BODY = 32_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HITS = {}

THANK_YOU = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Request received</title>
<meta http-equiv="refresh" content="4;url=/#contact"></head>
<body style="font-family:sans-serif;padding:48px">
<p>Your consultation request is on its way to Richard Winfred Esi, LLC.</p>
<p><a href="/#contact">Back to the site</a></p>
</body></html>
"""


def clean(value, limit):
    text = " ".join(str(value or "").split())
    return text[:limit]


def client_ip(handler):
    forwarded = handler.headers.get("X-Real-IP", "")
    return forwarded.split(",")[0].strip() or handler.client_address[0]


def limited(ip):
    now = time.time()
    recent = [stamp for stamp in HITS.get(ip, []) if now - stamp < 3600]
    if len(recent) >= 5:
        HITS[ip] = recent
        return True
    recent.append(now)
    HITS[ip] = recent
    return False


def parse_body(handler):
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0 or length > MAX_BODY:
        raise ValueError("Request is empty or too large.")
    raw = handler.rfile.read(length)
    ctype = handler.headers.get("Content-Type", "")
    if "application/json" in ctype:
        data = json.loads(raw.decode("utf-8"))
        return {k: data.get(k, "") for k in ("name", "email", "phone", "company", "message", "website")}
    pairs = urllib.parse.parse_qs(raw.decode("utf-8"), keep_blank_values=True)
    return {k: pairs.get(k, [""])[0] for k in ("name", "email", "phone", "company", "message", "website")}


def booking_from(fields):
    if clean(fields.get("website"), 200):
        return None
    name = clean(fields.get("name"), 80)
    email = clean(fields.get("email"), 120)
    phone = clean(fields.get("phone"), 40)
    company = clean(fields.get("company"), 80)
    message = clean(fields.get("message"), 2000)
    if len(name) < 2 or not EMAIL_RE.match(email) or len(message) < 5:
        raise ValueError("Add your name, a valid email, and a short note about what you need.")
    return {"name": name, "email": email, "phone": phone, "company": company, "message": message}


def save(booking):
    STORE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = STORE / f"{stamp}-{booking['email'].replace('@', '_at_')}.json"
    path.write_text(json.dumps(booking, indent=2), encoding="utf-8")
    return path


def send_formsubmit(booking):
    payload = json.dumps({
        "name": booking["name"],
        "email": booking["email"],
        "phone": booking["phone"],
        "company": booking["company"],
        "message": booking["message"],
        "_subject": "Consultation request from the website",
        "_template": "table",
        "_captcha": "false",
        "_replyto": booking["email"],
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://formsubmit.co/ajax/" + urllib.parse.quote(TO),
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", "replace")
        if response.status >= 400:
            raise RuntimeError(body[:300])
        return body


def deliver(booking):
    if DELIVER == "file":
        return "saved"
    if DELIVER == "formsubmit":
        return send_formsubmit(booking)
    raise RuntimeError("Mail delivery is not configured.")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.split("?", 1)[0] != "/consultation":
            self.reply(404, {"ok": False, "error": "Not found"})
            return
        if limited(client_ip(self)):
            self.reply(429, {"ok": False, "error": "Please wait a while before sending another request."})
            return
        try:
            fields = parse_body(self)
            booking = booking_from(fields)
        except (ValueError, json.JSONDecodeError, UnicodeError) as exc:
            self.reply(400, {"ok": False, "error": str(exc) or "Check the form and try again."})
            return
        if booking is None:
            self.reply(200, {"ok": True})
            return
        try:
            save(booking)
            deliver(booking)
        except (OSError, urllib.error.URLError, RuntimeError):
            self.reply(502, {"ok": False, "error": "We could not send that just now. Email info@richardwinfred.com or call +1 281 213 0055."})
            return
        self.reply(200, {"ok": True})

    def reply(self, status, payload):
        wants_json = "application/json" in self.headers.get("Accept", "")
        if wants_json:
            body = json.dumps(payload).encode("utf-8")
            kind = "application/json"
        elif status == 200 and payload.get("ok"):
            body = THANK_YOU.encode("utf-8")
            kind = "text/html; charset=utf-8"
        else:
            message = html.escape(payload.get("error") or "Something went wrong.")
            body = (
                "<!DOCTYPE html><html lang=\"en\"><body style=\"font-family:sans-serif;padding:48px\">"
                f"<p>{message}</p><p><a href=\"/#contact\">Back to the site</a></p></body></html>"
            ).encode("utf-8")
            kind = "text/html; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def main():
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
