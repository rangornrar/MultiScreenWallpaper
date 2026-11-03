# Google Search Console Setup

## Recommended property
- Preferred URL-prefix property: `https://wallcraft.archi-it.fr/`
- Main multilingual site URL: `https://wallcraft.archi-it.fr/`
- Sitemap to submit: `https://wallcraft.archi-it.fr/sitemap.xml`

## What is included
- `sitemap.xml` with all FR / EN / ES / DE pages
- `hreflang` alternates on every generated page
- `canonical` tags on every generated page
- `robots.txt`
- JSON-LD metadata for Google-rich understanding

## Verification
If Google gives you a meta-tag token, put it in `GOOGLE_SITE_VERIFICATION` inside `site_builder.py`, then rebuild the site.

## Hosting note
This project is designed for a GitHub Pages project site under a subpath. The sitemap is the most important file to submit manually in Search Console.
If you later move to a custom domain, keep the same sitemap URL pattern and place `robots.txt` at the domain root.
