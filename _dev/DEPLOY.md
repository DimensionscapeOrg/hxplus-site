# Deploying the hx+ site

Static HTML and CSS, no build step. Copy the folder to any host.

## Files that ship

```
index.html          the site
assets/style.css
assets/logo.svg     the mark
assets/favicon.svg  the mark on a dark tile
assets/og-image.png the social card, rendered from og-image.html
robots.txt
sitemap.xml
CNAME               only for GitHub Pages custom domains
```

Working files live in `_dev/`. GitHub Pages builds with Jekyll, which never publishes a folder whose name starts with an underscore, so nothing in `_dev/` goes live. Do not add a `.nojekyll` file, or it will.

## Before launch

1. **Fill the placeholder links.** In `index.html`, the two whitepaper-section buttons are marked
   `aria-disabled="true"` and read "link at launch": point them at the whitepaper and the repo,
   and remove the `aria-disabled` attributes.
2. **Check the haxe.run links.** The header, the browser section, the FAQ and the footer link to
   `https://haxe.run`. They assume the playground is live when this site goes up.
3. **Update the status box** in the roadmap if anything has moved, and keep the 4M+ downloads
   figure in the spec strip current.
4. **Confirm the domain** in `robots.txt`, `sitemap.xml`, the `canonical` link, and the `og:`/
   `twitter:` URLs if the site lands anywhere other than `https://hxplus.org/`.

## Regenerating the social card

`assets/og-image.png` is already rendered. If you change `og-image.html` (or the diagram it
shares with the hero), regenerate it at exactly 1200x630 with any Chromium browser:

```bash
msedge --headless=new --hide-scrollbars --force-device-scale-factor=1 --window-size=1200,630 --screenshot=assets/og-image.png _dev/og-image.html
```

`chrome` takes the same flags.

## GitHub Pages

```bash
git init && git add . && git commit -m "hx+ site"
git branch -M main
git remote add origin git@github.com:hxplus/hxplus.github.io.git
git push -u origin main
```

Then in the repository settings, Pages, set the source to `main` and the root folder. Add a file
named `CNAME` containing one line, `hxplus.org`, and point DNS at GitHub:

```
A     @    185.199.108.153
A     @    185.199.109.153
A     @    185.199.110.153
A     @    185.199.111.153
CNAME www  hxplus.github.io
```

Enable "Enforce HTTPS" once the certificate provisions, usually within an hour.

## Any other host

Netlify, Cloudflare Pages, Vercel, or plain nginx all work with zero configuration: the site is
static files with no dependencies, no JavaScript framework, and no external requests.

## Local preview

```bash
python -m http.server 8377 --directory hxplus-site
```
