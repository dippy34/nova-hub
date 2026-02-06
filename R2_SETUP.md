# R2 Bucket Setup for Nova Hub Games

This guide walks you through setting up Cloudflare R2 to serve games for Nova Hub.

## Overview

- **gn-math games**: Served from static files in `non-semag/gn-math/` (deployed with Pages)
- **R2 games**: Served from R2 bucket via `functions/semag/[[path]].js` at `/semag/*` URLs

When a user visits `/semag/happywheels/index.html`, the Pages Function fetches `semag/happywheels/index.html` from your R2 bucket and serves it.

---

## Step 1: Create the R2 Bucket

If you don't have the bucket yet:

```bash
npx wrangler r2 bucket create nova-hub
```

Or create it in the [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2** → **Create bucket** → name it `nova-hub`.

---

## Step 2: Bind R2 to Your Pages Project

Your `wrangler.toml` already has the R2 binding:

```toml
[[r2_buckets]]
binding = "semag"
bucket_name = "nova-hub"
```

**If using Git-connected Pages**, Cloudflare reads `wrangler.toml` from your repo. The binding should work automatically on deploy.

**If it doesn't work**, add it manually in the dashboard:
1. Go to [Workers & Pages](https://dash.cloudflare.com/?to=/:account/workers-and-pages)
2. Select your Nova Hub Pages project
3. **Settings** → **Functions** → **R2 bucket bindings** → **Add**
4. Variable name: `semag`
5. R2 bucket: `nova-hub`
6. Save and redeploy

---

## Step 3: Upload Games to R2

Games must be stored under the `semag/` prefix. Structure:

```
nova-hub (bucket)
└── semag/
    ├── happywheels/
    │   ├── index.html
    │   ├── Untitled.jpeg
    │   └── ... (all game files)
    ├── fnaf2/
    │   ├── index.html
    │   ├── project/
    │   │   └── splash.webp
    │   └── ...
    └── ...
```

### Option A: Upload via Wrangler CLI

For a single game folder (e.g. from local `semag/happywheels/`):

```bash
# Upload entire folder - each file gets key semag/happywheels/filename
npx wrangler r2 object put nova-hub/semag/happywheels/index.html --file=./semag/happywheels/index.html
# Repeat for each file, or use the upload script below
```

### Option B: Use the Upload Script

Upload all games from semag (after cloning from [GitLab](https://gitlab.com/skysthelimit.dev/selenite)):

```bash
node scripts/upload-game-to-r2.js semag
```

Or upload a single game:

```bash
node scripts/upload-game-to-r2.js semag/happywheels
```

### Option C: Upload via Dashboard

1. Go to **R2** → **nova-hub** bucket
2. Click **Upload**
3. Create folder `semag/` and upload your game folders inside it

---

## Step 4: Add Games to games.json

Each R2 game needs an entry in `data/games.json`:

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

- `source`: `"semag"` (tells the loader to use `/semag/*` URLs)
- `gameUrl`: `/semag/{directory}/index.html` (or the main HTML file)
- `imagePath`: `/semag/{directory}/{cover-image}`

---

## Step 5: Deploy

Push your changes and let Cloudflare Pages deploy. The `functions/semag/[[path]].js` handler will serve files from R2 for any `/semag/*` request.

---

## Local Development

**Option 1: Static server (semag from local folder)**  
Requires `semag/` folder locally (clone from GitLab or copy from semag-gitlab).

```bash
npm run dev
```

Serves from project root. Opens http://localhost:3000. Both gn-math and semag games work (semag served from local files).

**Option 2: Wrangler (semag from R2)**  
Tests the deployed setup locally. Uses R2 even if semag folder is missing.

```bash
npm run dev:r2
```

Builds to dist/, then runs `wrangler pages dev` with R2 binding. Semag games load from your R2 bucket.

---

## Verify It Works

1. Deploy your site
2. Visit `https://your-site.pages.dev/semag/{game-name}/index.html`
3. If you see 404, check:
   - R2 bucket has the file at `semag/{game-name}/index.html`
   - R2 binding is set (Settings → Functions → R2 bucket bindings)
   - You redeployed after adding the binding

---

## Local Development

To test R2 locally:

```bash
npx wrangler pages dev dist --r2=semag
```

(Requires `dist/` to exist — run `npm run build` first.)
