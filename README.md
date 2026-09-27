# Richard Winfred Esi, LLC — Website

Production-ready static site. No build step, no dependencies, no server-side code required.

## Structure
richardwinfred-site/
  index.html            Homepage (fully responsive)
  assets/css/style.css  All styles (charcoal #1F1F1F + gold #B8932F/#C19A36 system)
  assets/js/main.js     Scroll-reveal animations
  assets/img/           Brand images (logo, logo-white, photography from company brochure)

## Deploy on AWS Lightsail

This is a static site. Serve it with nginx on an Ubuntu Lightsail instance. No build step, database, or Node process.

The GitHub repo is private, so the instance should not clone it. Copy the files up with `rsync` (or Lightsail's browser SSH upload), then run the setup script on the server.

### Instance
- Blueprint: **Ubuntu 24.04**, OS only. The setup script targets Ubuntu's nginx paths, not a Bitnami stack.
- Size: the smallest plan is enough. There is no application runtime to keep in memory.
- Attach a **static IP** before DNS is pointed here. A static IP is free while it is attached to a running instance.
- Lightsail networking firewall: allow SSH (22) from your IP, plus HTTP (80) and HTTPS (443) from anywhere. Certbot needs port 80.
- Leave existing **MX records** alone. This server only answers for the website. Email for `info@richardwinfred.com` stays with the current mail host.

### DNS
Create these records at the domain registrar, aimed at the static IP:

- `A` `@` → static IP
- `A` `www` → static IP

Wait until they resolve, then request the certificate. Canonical, Open Graph, `robots.txt`, and `sitemap.xml` use `https://richardwinfred.com/`. If the live hostname is different, change those three files before the first publish.

### First boot
Copy this repo onto the instance (for example into `/home/ubuntu/richardwinfred`), then:

```bash
sudo ./deploy/lightsail-setup.sh richardwinfred.com info@richardwinfred.com
```

That installs nginx and Certbot, publishes the site to `/var/www/richardwinfred`, and requests a Let's Encrypt certificate. Add `WWW=1` before the command only after the `www` record resolves:

```bash
sudo WWW=1 ./deploy/lightsail-setup.sh richardwinfred.com info@richardwinfred.com
```

### Later updates
From a machine that can SSH to the instance:

```bash
./deploy/push.sh ubuntu@STATIC_IP
```

The Ubuntu user on Lightsail has passwordless sudo, which the script uses for `rsync`.

### What the server does
- nginx serves the files. HTML is not cached; files under `assets/` cache for one day. Asset filenames are not hashed, so rename a file when replacing it if a one-day delay is a problem.
- HTTP redirects to HTTPS after Certbot runs.
- Response headers set a content security policy, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`. The policy allows Google Fonts and same-origin images, scripts, and styles. It does not allow a contact form post.
- Unknown URLs return `404.html`.

HSTS is not turned on. Add it only after HTTPS has been confirmed on the real domain.

### Other static hosts
The same files can still be uploaded to any static host (cPanel `public_html`, Netlify, Cloudflare Pages). `index.html` has to be at the domain root. Those hosts will not apply the nginx headers in `deploy/nginx/`.

## Notes
- Fonts load from Google Fonts (Fraunces + Inter). Site degrades gracefully to system fonts offline.
- To edit text, open index.html in any text editor — all copy is plain HTML.
- Colors are CSS variables at the top of style.css (--cobalt is the charcoal brand base, --gold is the accent) — change once, updates everywhere.
- Replace images in assets/img/ with same filenames to update photos.
- Contact CTAs currently point to mailto:info@richardwinfred.com and tel:+12812130055.
