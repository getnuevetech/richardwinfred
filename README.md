# Richard Winfred Esi, LLC — Website

Production-ready static site. No build step, no dependencies, no server-side code required.

## Structure
richardwinfred-site/
  index.html            Homepage (fully responsive)
  assets/css/style.css  All styles (charcoal #1F1F1F + gold #B8932F/#C19A36 system)
  assets/js/main.js     Scroll-reveal animations
  assets/img/           Brand images (logo, logo-white, photography from company brochure)

## Deploy on AWS Lightsail

This is a static site. The server is a small Ubuntu Lightsail instance running nginx. There is no build step, database, or Node process. `deploy/lightsail-setup.sh` installs nginx into Ubuntu's normal paths (`/etc/nginx`, `/var/www`), so the instance has to be the OS-only Ubuntu blueprint.

Do the steps in this order. The certificate request fails if DNS is not already pointing at the static IP, or if ports 80 and 443 are still closed.

### 1. Create the instance

1. Open the [Lightsail console](https://lightsail.aws.amazon.com/).
2. Choose **Create instance**.
3. Pick the region closest to the audience. For a Houston site, US East (Ohio) or US East (N. Virginia) is the usual choice. The region cannot be changed later.
4. Platform: **Linux/Unix**.
5. Blueprint: open the **OS Only** tab and choose **Ubuntu 24.04 LTS**.
6. Leave the launch script empty. Keep the default SSH key.
7. Name the instance `richardwinfred-web`.
8. Choose the smallest plan. The site is static files, so extra memory is unused.
9. Choose **Create instance** and wait until the state is **Running**.

### 2. Attach a static IP

1. Open the instance, then the **Networking** tab.
2. Under **Public IPv4 address**, choose **Attach static IP**, then **Create static IP**.
3. Name it `richardwinfred-ip` and attach it to `richardwinfred-web`.
4. Copy the address. A static IP stays free while it is attached to a running instance. Releasing it, or leaving it unattached, is what starts the charge.

### 3. Open the firewall

On the same **Networking** tab, under **IPv4 Firewall**, add any of these rules that are missing:

| Application | Protocol | Port |
| --- | --- | --- |
| SSH | TCP | 22 |
| HTTP | TCP | 80 |
| HTTPS | TCP | 443 |

Port 80 has to be open before the certificate request. Restrict SSH to your own IP when you know it.

### 4. Point DNS at that IP

Add the records at the DNS host that already serves the domain. Leave the nameservers and the MX records as they are. This server only answers for the website; mail for `info@richardwinfred.com` stays with the current mail host.

| Type | Host | Value |
| --- | --- | --- |
| A | `@` | the static IP |
| A | `www` | the static IP |

If an `AAAA` record for `@` or `www` points somewhere else, update or remove it. Otherwise some visitors will reach the old address.

Wait until both names resolve to the static IP:

```bash
dig +short richardwinfred.com
dig +short www.richardwinfred.com
```

Canonical, Open Graph, `robots.txt`, and `sitemap.xml` use `https://richardwinfred.com/`. If the live hostname is different, change those before the first publish.

### 5. Copy the site onto the server

The GitHub repo is private, so the instance cannot clone it on its own. From your own machine, in a checkout that contains `deploy/lightsail-setup.sh`:

```bash
rsync -az --exclude '.git/' ./ ubuntu@STATIC_IP:/home/ubuntu/richardwinfred/
```

SSH uses the Lightsail default key for the instance region. Download it from **Account → SSH keys** if you do not already have it, then:

```bash
chmod 400 ~/Downloads/LightsailDefaultKey-REGION.pem
ssh -i ~/Downloads/LightsailDefaultKey-REGION.pem ubuntu@STATIC_IP
```

The browser SSH button on the instance **Connect** tab also works. Use `rsync` or `scp` for the files; the browser session has no convenient upload.

### 6. Install nginx and the certificate

On the server:

```bash
cd /home/ubuntu/richardwinfred
sudo WWW=1 ./deploy/lightsail-setup.sh richardwinfred.com info@richardwinfred.com
```

`WWW=1` includes `www.richardwinfred.com` on the certificate. Omit it when that DNS record does not exist yet:

```bash
sudo ./deploy/lightsail-setup.sh richardwinfred.com info@richardwinfred.com
```

The script installs nginx, Certbot, and rsync, publishes the public files to `/var/www/richardwinfred`, and requests a Let's Encrypt certificate. HTTP then redirects to HTTPS. If the certificate step fails, fix DNS or the firewall and run the same command again.

Confirm renewal is scheduled:

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

### 7. Check the live site

From your own machine:

```bash
curl -sI https://richardwinfred.com/ | head
curl -sI http://richardwinfred.com/ | head
curl -sI https://richardwinfred.com/not-a-page | head
```

The first response is `200` over HTTPS. The second is a redirect to HTTPS. The third is `404` and still returns the branded not-found page. Then open `https://richardwinfred.com/` and `https://www.richardwinfred.com/` in a browser.

### 8. Later updates

From your own machine, in the site checkout:

```bash
./deploy/push.sh ubuntu@STATIC_IP
```

That replaces the files in `/var/www/richardwinfred` and reloads nginx. The Ubuntu user on Lightsail has passwordless sudo, which the script uses. It does not request a new certificate.

### What the server does

- nginx serves the files. HTML and 404 responses are not cached. Files under `assets/` cache for one day. Asset filenames are not hashed, so rename a file when replacing it if a one-day delay is a problem.
- Response headers set a content security policy, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`. The policy allows Google Fonts and same-origin images, scripts, and styles. It does not allow a contact form post.
- HSTS is off. Turn it on only after HTTPS has been confirmed on the real domain.
- Take a Lightsail snapshot from the instance **Snapshots** tab after the first successful boot, so the finished server can be restored.

### Other static hosts
The same files can still be uploaded to any static host (cPanel `public_html`, Netlify, Cloudflare Pages). `index.html` has to be at the domain root. Those hosts will not apply the nginx headers in `deploy/nginx/`.

## Notes
- Fonts load from Google Fonts (Fraunces + Inter). Site degrades gracefully to system fonts offline.
- To edit text, open index.html in any text editor — all copy is plain HTML.
- Colors are CSS variables at the top of style.css (--cobalt is the charcoal brand base, --gold is the accent) — change once, updates everywhere.
- Replace images in assets/img/ with same filenames to update photos.
- Contact CTAs currently point to mailto:info@richardwinfred.com and tel:+12812130055.
