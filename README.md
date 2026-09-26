# Richard Winfred Esi, LLC — Website

Production-ready static site. No build step, no dependencies, no server-side code required.

## Structure
richardwinfred-site/
  index.html            Homepage (fully responsive)
  assets/css/style.css  All styles (charcoal #1F1F1F + gold #B8932F/#C19A36 system)
  assets/js/main.js     Scroll-reveal animations
  assets/img/           Brand images (logo, logo-white, photography from company brochure)

## Deploy
Upload the ENTIRE folder contents to any static web host:

1. cPanel / traditional hosting (e.g., GoDaddy, HostGator):
   - Upload all files/folders to public_html (or your domain root) via File Manager or FTP.
   - index.html must sit at the domain root: https://yourdomain.com/ should load it directly.

2. Netlify / Vercel / Cloudflare Pages:
   - Drag-and-drop the folder onto the dashboard, or connect a git repo.
   - No build command needed; publish directory = the site root.

3. GitHub Pages:
   - Push these files to a repo, enable Pages on the main branch root.

## Notes
- Fonts load from Google Fonts (Fraunces + Inter). Site degrades gracefully to system fonts offline.
- To edit text, open index.html in any text editor — all copy is plain HTML.
- Colors are CSS variables at the top of style.css (--cobalt is the charcoal brand base, --gold is the accent) — change once, updates everywhere.
- Replace images in assets/img/ with same filenames to update photos.
- Contact CTAs currently point to mailto:info@richardwinfred.com and tel:+12812130055.
