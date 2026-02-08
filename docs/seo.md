# SEO Configuration

Base URL for production: `https://nova-labs.pages.dev`

## Meta Tags (per page)

Each page should include:

```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page Title | Nova Hub</title>
<meta name="description" content="50-160 char description">
<meta name="keywords" content="unblocked games, nova hub, free games, chromebook">
<link rel="canonical" href="https://nova-labs.pages.dev/page.html">
<link rel="icon" href="/nova-favicon.ico">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:title" content="Page Title | Nova Hub">
<meta property="og:description" content="...">
<meta property="og:url" content="https://nova-labs.pages.dev/page.html">
<meta property="og:image" content="https://nova-labs.pages.dev/nova-favicon.ico">
<meta property="og:site_name" content="Nova Hub">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Page Title | Nova Hub">
<meta name="twitter:description" content="...">
<meta name="theme-color" content="#c77dff">
```

## Structured Data

- Index: `WebSite` + `Organization`
- Game pages: `VideoGame` (optional)
- See index.html for JSON-LD example

## Sitemap

- Static: `sitemap.xml` at root (for dev)
- Generated: Build script creates `dist/sitemap.xml` with SITE_URL env var
- robots.txt references sitemap
