# Nova Hub Documentation

Central index for setup guides and tutorials.

---

## Tutorials

| Document | Purpose |
|----------|---------|
| [cloudflare-workers-and-kv.md](tutorials/cloudflare-workers-and-kv.md) | KV namespaces, Workers, migration to Cloudflare, Pages build config |
| [r2-games-bucket.md](tutorials/r2-games-bucket.md) | R2 bucket setup, `semag/` layout, upload commands, local R2 testing |
| [admin-panel-setup.md](tutorials/admin-panel-setup.md) | Admin panel, credentials import, analytics, API endpoints |
| [add-admin-accounts.md](tutorials/add-admin-accounts.md) | Adding new admin users |
| [seo.md](seo.md) | SEO configuration, meta tags, structured data |

---

## Quick reference

### Config files

| File | Purpose |
|------|---------|
| `wrangler.toml` | Cloudflare bindings (KV, R2) |
| `data/games.json` | Game catalog (source of truth) |
| `package.json` | Scripts: `dev`, `build`, `dev:r2` |

### Key paths

| Path | Serves |
|-----|--------|
| `/non-semag/games/*` | Static games (from repo) |
| `/semag/*` | R2 games (via Worker) |
| `/api/*` | API endpoints (suggestions, admin) |
