# Nova Hub

**The better unblocked games website.** A web-based game hub with 900+ games, deployable to Cloudflare Pages, Railway, Render, and more.

---

## Quick Start

| I want to… | Go here |
|------------|---------|
| **Understand the project** | [What is this?](#what-is-this) |
| **Know where games live** | [Where are games stored?](#where-are-games-stored) |
| **Run it locally** | [Local development](#local-development) |
| **Deploy to Cloudflare** | [docs/tutorials/cloudflare-workers-and-kv.md](docs/tutorials/cloudflare-workers-and-kv.md) |
| **Add or serve R2 games** | [docs/tutorials/r2-games-bucket.md](docs/tutorials/r2-games-bucket.md) |
| **Set up admin panel** | [docs/tutorials/admin-panel-setup.md](docs/tutorials/admin-panel-setup.md) |

---

## What is this?

Nova Hub is a game portal that:

1. **Lists games** from `data/games.json` (name, cover, URL, source)
2. **Shows a catalog** at `/projects.html` and `/games-list.html`
3. **Loads games** in `loader.html` inside an iframe (blur overlay → Play → fullscreen)
4. **Serves games** from two places:
   - **Static (in repo):** `non-semag/games/` — HTML wrappers + covers
   - **Cloudflare R2:** `/semag/*` — served by a Worker from the `nova-hub` bucket

Games can be **starred**, have **recommended games**, and use various themes.

---

## Where are games stored?

### Static games (in the repo)

| Path | Description |
|------|-------------|
| `non-semag/games/` | ~550 games. Each game has a wrapper (e.g. `bowmasters.html`) and cover in `covers/`. |
| `non-semag/games/covers/` | Thumbnail images for each game. |
| `non-semag/geometry-dash-lite/` | Geometry Dash Lite (Turbowarp). |

**`games.json` entry for static games:**
```json
{
  "name": "Bowmasters",
  "directory": "bowmasters",
  "image": "covers/bowmasters.png",
  "source": "non-semag",
  "gameUrl": "/non-semag/games/bowmasters.html",
  "imagePath": "/non-semag/games/covers/bowmasters.png"
}
```

### R2 games (Cloudflare bucket)

| Path | Description |
|------|-------------|
| R2 bucket `nova-hub` | Stores games under `semag/` prefix |
| `/semag/*` URLs | Served by `functions/semag/[[path]].js` which fetches from R2 |

**`games.json` entry for R2 games:**
```json
{
  "name": "Happy Wheels",
  "directory": "happywheels",
  "image": "Untitled.jpeg",
  "source": "semag",
  "gameUrl": "/semag/happywheels/index.html",
  "imagePath": "/semag/happywheels/Untitled.jpeg"
}
```

### Oversized games (excluded from Pages deploy)

Cloudflare Pages has a **25 MiB per file** limit. These folders are excluded from the build:

- `non-semag/EscapeRoad`
- `non-semag/EscapeRoad2`
- `non-semag/EscapeRoadCity`

They work locally but are **not** deployed to Pages; they would need R2 or another host.

---

## Repo layout

```
nova-hub/
├── index.html              # Homepage
├── projects.html           # Game catalog hub
├── games-list.html         # Full game grid
├── loader.html             # Game iframe + Play button + fullscreen
├── starred-games.html      # Starred games
├── suggest.html            # Suggestion form
├── admin.html              # Admin panel
│
├── data/                   # JSON data
│   ├── games.json          # Game catalog (source of truth)
│   ├── apps.json
│   ├── suggestions.json
│   ├── admin-credentials.json
│   └── ...
│
├── non-semag/              # Static assets
│   ├── games/              # Static games (HTML + covers)
│   └── geometry-dash-lite/
│
├── functions/              # Cloudflare Workers
│   ├── api/[[path]].js     # API (suggestions, admin, analytics)
│   ├── semag/[[path]].js   # Serves /semag/* from R2
│   ├── apps/[[path]].js
│   └── d/[id].js
│
├── js/                     # Frontend scripts
│   ├── games.js            # Game catalog logic
│   ├── main.js
│   ├── admin.js
│   └── ...
│
├── css/                    # Styles
├── img/                    # Site images
├── sppa/                   # Scratch/emulator tools
├── scramjet/               # Scramjet games
│
├── scripts/                # Build & maintenance
│   ├── pages-build.js      # Cloudflare Pages build (excludes oversized games)
│   ├── migrate-to-kv.js    # Migrate JSON data to KV
│   ├── import-admins-simple.js  # Add admin credentials
│   └── *.py                # Scrapers, matchers, fixes (gn-math, lagged, etc.)
│
├── wrangler.toml           # Cloudflare config (KV, R2 bindings)
├── sitemap.xml             # SEO sitemap (static; build overwrites in dist/)
├── robots.txt              # Crawler directives
├── _headers                # Security + cache headers
├── _redirects               # URL redirects ( moved paths )
├── hacks/                  # Hack source/docs (Big Ideas Math Bot, etc.)
├── admin/                  # Admin tools (git-scanner, deployer, git-fetcher)
├── tools/                  # Dev tools (dev-tools, backgrounds)
├── legal/                  # Legal (dmca)
└── docs/                   # Documentation
    ├── README.md           # Docs index
    └── tutorials/         # Setup guides
        ├── cloudflare-workers-and-kv.md
        ├── r2-games-bucket.md
        ├── admin-panel-setup.md
        └── add-admin-accounts.md
```

---

## How it works (tutorial)

### 1. User visits the site

- **Homepage** (`index.html`): Terminal-style UI, links to games, apps, settings
- **Games** (`projects.html`): Grid of categories; “Browse All” → `games-list.html`

### 2. Game catalog loads

- `games-list.html` + `js/games.js` fetch `/data/games.json`
- Each game shows: cover image, name, star button
- Clicking a game goes to: `loader.html#<base64-encoded-game-data>`

### 3. Loader page

- **loader.html** decodes the hash and loads `gameUrl` into an iframe
- **Blur overlay** shows the cover; user clicks **Play**
- Iframe loads the game; fullscreen button is available
- **Last game** is stored in a cookie for “resume”

### 4. Where the game is served from

- **`source: "non-semag"`** → `/non-semag/games/<slug>.html` or similar (static from repo)
- **`source: "semag"`** → `/semag/<directory>/index.html` (served by Worker from R2)

### 5. API & admin

- **`/api/*`** → `functions/api/[[path]].js` (suggestions, admin login, analytics)
- Uses KV for suggestions, credentials, tokens
- Admin panel at `/admin.html`

---

## Local development

```bash
# Install dependencies
npm install

# Static server (games from repo)
npm run dev
# → http://localhost:3000

# Build for Pages, then run with R2 (semag from bucket)
npm run dev:r2
```

---

## Build & deploy

### Cloudflare Pages

- **Build command:** `node scripts/pages-build.js`
- **Output directory:** `dist`
- **Build script** copies the site into `dist/`, omits Escape Road folders, and generates `sitemap.xml`
- Set `SITE_URL` env var (e.g. `https://your-domain.com`) to customize sitemap URLs
- Connect the repo to Cloudflare Pages; deployment is automatic on push

### Other hosts (Railway, Render, etc.)

- Use `npm start` (Express server in `index.js`) or serve static files
- R2 games require the `semag` Worker; for non-Cloudflare hosts you may need an alternative setup

---

## Setup guides

| Document | Purpose |
|----------|---------|
| [cloudflare-workers-and-kv.md](docs/tutorials/cloudflare-workers-and-kv.md) | KV namespaces, Workers, migration, Pages config |
| [r2-games-bucket.md](docs/tutorials/r2-games-bucket.md) | R2 bucket, `semag/` layout, upload commands, local R2 testing |
| [admin-panel-setup.md](docs/tutorials/admin-panel-setup.md) | Admin panel, credentials, analytics, API endpoints |
| [add-admin-accounts.md](docs/tutorials/add-admin-accounts.md) | Adding new admin accounts |
| [docs/README.md](docs/README.md) | Documentation index |

---

## Deploy buttons

[![Deploy on Railway](https://binbashbanana.github.io/deploy-buttons/buttons/remade/railway.svg)](https://railway.app/new/template?template=https://gitlab.com/skysthelimit.dev/selenite)  
[![Deploy to Cyclic](https://binbashbanana.github.io/deploy-buttons/buttons/remade/cyclic.svg)](https://app.cyclic.sh/api/app/deploy/selenite-cc/selenite-old)  
[![Deploy to Koyeb](https://binbashbanana.github.io/deploy-buttons/buttons/remade/koyeb.svg)](https://app.koyeb.com/deploy?type=git&repository=gitlab.com/skysthelimit.dev/selenite&branch=main&name=selenite)  
[![Deploy to Render](https://binbashbanana.github.io/deploy-buttons/buttons/remade/render.svg)](https://render.com/deploy?repo=https://gitlab.com/skysthelimit.dev/selenite)  
[![Deploy to Vercel](https://binbashbanana.github.io/deploy-buttons/buttons/remade/vercel.svg)](https://vercel.com/new/clone?repository-url=https://gitlab.com/skysthelimit.dev/selenite)

---

## Contributors

- [Sky](https://github.com/skysthelimitt)
- [LEGALISE_PIRACY](https://codeberg.org/LEGALISE_PIRACY)
- [Astralogical](https://github.com/a456pur)

## Support

[Join our Discord](https://discord.gg/WDZhkdFyF4) for support 24/7.
