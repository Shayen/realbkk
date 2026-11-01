# Dokploy Docker Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep every existing file, archive only confirmed non-runtime inputs, and provide simple local Docker Compose and Dokploy deployment paths for the static site.

**Architecture:** Preserve the existing site paths and build a single Nginx image containing only runtime HTML, assets, sitemap, and robots files. Production Compose exposes container port 80 internally with an interpolated image tag; a local-only override binds to loopback. Dokploy supplies domains and TLS.

**Tech Stack:** Dockerfile, Nginx Alpine, Docker Compose v2, existing Python standard-library `unittest`.

**Spec:** [`docs/superpowers/specs/2026-11-01-dokploy-docker-design.md`](../specs/2026-11-01-dokploy-docker-design.md)

## Global Constraints

- “Do not delete files; use tracked moves into `do_not_use/`.”
- “No application secrets, certificate files, or host-published production ports.”
- “No extra services, database, external registry, build workflow, or runtime mounts.”
- “Preserve canonical URLs, sitemap/robots files, the three locale routes, and existing configurator/simulator behavior.”
- “The image tag is local to the Compose build. This design does not add GitHub Actions, publish to GHCR, require registry credentials, or claim that a registry tag is created.”
- “Dokploy terminates public HTTPS; Nginx listens on HTTP port 80 inside the container.”

## Review Focus

- **Archived originals remain intact:** test that all paths are moved, plus compare `git show HEAD:<old-path>` hashes with archived file hashes to catch accidental deletion or content changes.
- **Active media stay at existing URLs:** test that `/1587.gif`, `/1885.gif`, optimized gallery images, logos, and scripts remain in the image.
- **Tag interpolation is predictable:** test default `latest` and an alternate `IMAGE_TAG` through `docker compose config`.
- **Production routing does not expose a host port:** test production Compose has only `expose: 80`; local override binds only `127.0.0.1`.
- **Static Nginx routes behave as intended:** smoke-test all 12 HTML routes, `/robots.txt`, `/sitemap.xml`, 404 for an unknown path, and the apex-to-www redirect.

---

### Task 1: Archive non-runtime source and reference files

**Files:**
- Move: `Behind The Production 2025/` → `do_not_use/Behind The Production 2025/`
- Move: `REF/` → `do_not_use/REF/`
- Move: `IMG_7567.png` → `do_not_use/IMG_7567.png`
- Create: `do_not_use/README.md`
- Modify: `css/style.css` (archive-reference comment)
- Modify: `js/gallery-data.js` (archive-source comment)
- Modify: `tests/test_discoverability.py`

**Interfaces:**
- `do_not_use/` is preservation-only; none of its contents are needed at runtime.
- Keep root `1587.gif`, root `1885.gif`, `images/`, `logo/`, `css/`, `js/`, and all locale HTML paths unchanged.

- [ ] **Step 1: Add failing archive tests**

  Extend `tests/test_discoverability.py` with:
  - `test_source_and_reference_files_are_archived`: assert the three specified destinations exist and the old paths no longer exist.
  - `test_runtime_gifs_remain_at_root`: assert `1587.gif` and `1885.gif` remain at root and the simulator/gallery scripts still reference them by their root URLs.
  - `test_archive_comments_use_new_locations`: assert source comments refer to `do_not_use/REF/` and `do_not_use/Behind The Production 2025/`.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: FAIL because the archive paths and updated comment targets do not exist yet.

- [ ] **Step 3: Move files without changing contents**

  Before moving, capture checksums for every tracked file under the three source paths. Use `git mv` to move the paths into `do_not_use/`; add `do_not_use/README.md` describing their preservation-only status; update only the two source comments.

- [ ] **Step 4: Verify archive integrity and run focused tests**

  Compare the saved source checksums with the files now under `do_not_use/`. Confirm each original has a matching `R`/rename in Git status/diff and no file contents changed.

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: archive/runtime checks and existing locale/SEO checks PASS.

- [ ] **Step 5: Run the full suite and commit**

  Run: `python3 -m unittest discover -s tests -v`

  Expected: all tests PASS.

  Commit the archive moves, comment updates, and tests as `chore: archive non-runtime source files`.

### Task 2: Add Dokploy-ready Docker Compose deployment

**Files:**
- Create: `Dockerfile`
- Create: `compose.yaml`
- Create: `compose.local.yaml`
- Create: `.dockerignore`
- Create: `nginx/default.conf`
- Modify: `README.md`
- Modify: `tests/test_discoverability.py`

**Interfaces:**
- Production service name: `web`.
- Internal HTTP port: `80`.
- Image reference: `realbkk-web:${IMAGE_TAG:-latest}`.
- Local port mapping: `127.0.0.1:${WEB_PORT:-8080}:80`, only in `compose.local.yaml`.
- Dokploy uses `compose.yaml` only and its Domains UI targets the `web` service on container port 80.
- Nginx redirects `Host: realbkk.com` to `https://www.realbkk.com$request_uri`; other hosts serve static files from `/usr/share/nginx/html`.

- [ ] **Step 1: Add failing Docker packaging tests**

  Extend `tests/test_discoverability.py` with:
  - `test_production_compose_builds_and_tags_web_image`: assert production Compose has one `web` service, builds `Dockerfile`, uses the specified image interpolation, and exposes port 80 without `ports`.
  - `test_local_compose_binds_only_loopback`: assert the local override maps `127.0.0.1:${WEB_PORT:-8080}:80`.
  - `test_dockerfile_copies_required_runtime_paths_only`: assert all locale pages, CSS, JS, images, logo, GIFs, robots, and sitemap are copied; archived/development paths are excluded from `.dockerignore`.
  - `test_nginx_routes_directories_and_unknown_paths`: assert Nginx has the specified document root, index, apex redirect, and `try_files $uri $uri/ =404`.

- [ ] **Step 2: Run focused tests to verify they fail**

  Run: `python3 -m unittest discover -s tests -p 'test_discoverability.py' -v`

  Expected: FAIL because Docker packaging and Nginx config files are absent.

- [ ] **Step 3: Add the production Docker image and Compose service**

  Create an Nginx Alpine Dockerfile that copies only the site’s explicit runtime paths into `/usr/share/nginx/html` and installs `nginx/default.conf`. Add production Compose with the `web` build, the exact interpolated image tag, internal `expose: ["80"]`, restart policy, and a homepage health check.

- [ ] **Step 4: Add the local override and Docker context exclusions**

  Add `compose.local.yaml` with only the loopback host mapping and default port 8080. Add `.dockerignore` exclusions for `do_not_use/`, Git data, tests, docs, `.superpowers/`, `.playwright-mcp/`, and other development-only files. Do not ignore runtime assets or the Docker/Nginx files needed for the build.

- [ ] **Step 5: Add Nginx static and canonical-host routing**

  Add the apex-to-www redirect and static `www`/default server using root `/usr/share/nginx/html`, `index index.html`, and `try_files $uri $uri/ =404`. Keep TLS outside the container.

- [ ] **Step 6: Update README local and Dokploy instructions**

  Document Docker/Compose prerequisites, local start (`docker compose -f compose.yaml -f compose.local.yaml up --build -d`), `http://localhost:8080`, shutdown, optional `WEB_PORT`/`IMAGE_TAG`, and Dokploy Git Compose setup. State to select `compose.yaml`, standard Docker Compose mode, `web` container port 80, attach apex and `www` domains, enable TLS, and redeploy after domain changes. Explain that `IMAGE_TAG` tags the locally built image and does not publish to a registry.

- [ ] **Step 7: Verify Compose configuration and image build**

  Run:

  ```sh
  docker compose -f compose.yaml config
  IMAGE_TAG=review docker compose -f compose.yaml config
  docker compose -f compose.yaml -f compose.local.yaml config
  docker compose -f compose.yaml -f compose.local.yaml build
  ```

  Expected: all configs validate; the default tag is `latest`, the alternate config uses `review`, the production config has no host port, the local config binds loopback, and the image builds successfully.

- [ ] **Step 8: Smoke-test the running image and all existing tests**

  Start with `docker compose -f compose.yaml -f compose.local.yaml up -d`. Verify:
  - The `web` service becomes healthy.
  - Each of the 12 locale/page URLs, `/robots.txt`, `/sitemap.xml`, `/1587.gif`, `/1885.gif`, and representative assets returns HTTP 200.
  - An unknown path returns 404.
  - Sending `Host: realbkk.com` returns a redirect to `https://www.realbkk.com/...`.
  - Existing configurator and simulator work.

  Run: `python3 -m unittest discover -s tests -v`

  Expected: all tests PASS. Stop the local Compose services after verification.

- [ ] **Step 9: Commit the deployment setup**

  Commit the Dockerfile, Compose files, Docker ignore rules, Nginx config, README, and tests as `feat: add Dokploy Docker Compose deployment`.

## Final acceptance

- All files from the three archive candidates remain in Git under `do_not_use/`; no file is deleted.
- Production Dokploy deployment builds directly from Git and has no published host port, runtime mount, external registry, or secret.
- Local Compose serves the app only on loopback by default.
- Docker image is tagged `realbkk-web:latest` unless `IMAGE_TAG` overrides it.
- Nginx serves the current site and redirects the apex host to canonical `www`; Dokploy handles public TLS.
- SEO metadata, locale routing, interactive tools, sitemap, and robots behavior continue to pass checks.
