# Dokploy and Docker Compose deployment design

## Goal

Make the existing static REAL Bangkok site straightforward to run locally and deploy from Git through Dokploy, while preserving all current files. Archive only files that are not needed by the running site in a root `do_not_use/` directory, and exclude that archive from production image builds.

## Current state

- The site is static HTML, CSS, JavaScript, and media; it has no build system, package manifest, backend, or database.
- English pages live at the root; Thai and Japanese pages live under `/th/` and `/ja/`.
- The website is currently served from repository root paths. Runtime references include root-level `1587.gif`, `1885.gif`, optimized files under `images/`, `css/`, `js/`, and `logo/`.
- There are 78 original/source media files under `Behind The Production 2025/`; the site gallery loads the same number of optimized image files from `images/gallery/`.
- `REF/` is referenced only in stylesheet comments, and `IMG_7567.png` has no runtime references.
- There is no Dockerfile, Docker Compose file, or Nginx deployment configuration in the repository.

## Deployment approach

Use the standard Dokploy Docker Compose deployment flow from Git. Dokploy builds the site's Dockerfile directly from the checked-out repository; the image contains the website files and Nginx config, with no runtime bind mounts.

The production `compose.yaml` defines one web service:

- Build from the repository root using `Dockerfile`.
- Assign the local Compose image name `realbkk-web:${IMAGE_TAG:-latest}`. `IMAGE_TAG` is a Compose interpolation variable with a safe `latest` default; Dokploy can set it to a release name or commit identifier.
- Expose container port 80 to the Docker network only, without publishing a host port.
- Include a health check that requests the local homepage.
- Bake the site and Nginx configuration into the image.

`compose.local.yaml` is an opt-in local override that publishes Nginx only on `127.0.0.1:${WEB_PORT:-8080}`. Local run instructions use both Compose files; Dokploy must use production `compose.yaml` only.

The image tag is local to the Compose build. This design does not add GitHub Actions, publish to GHCR, require registry credentials, or claim that a registry tag is created. Deployment from Git and redeployment on pushes are configured in Dokploy.

Dokploy's Domains UI handles routing and TLS. Configure the `web` service's container port as 80 and attach both `www.realbkk.com` and `realbkk.com` with HTTPS enabled. The Nginx config redirects apex requests to `https://www.realbkk.com$request_uri`; Dokploy terminates public TLS before forwarding HTTP to Nginx. Do not put certificate files or TLS secrets in the image. Use standard Docker Compose mode, not Docker Stack/Swarm mode.

## Nginx behavior

Use a small repository-owned Nginx server config with a redirect from `realbkk.com` to `https://www.realbkk.com$request_uri` and a static server with document root `/usr/share/nginx/html`, `index.html` as the directory index, and `try_files $uri $uri/ =404`. This serves `/`, locale directory indexes, and the site's explicit `.html` paths without inventing SPA routes. Dokploy terminates public HTTPS; Nginx listens on HTTP port 80 inside the container.

## Repository organization and preservation

Create root `do_not_use/` and move, without deleting or altering file contents:

- `Behind The Production 2025/` to `do_not_use/Behind The Production 2025/`.
- `REF/` to `do_not_use/REF/`.
- `IMG_7567.png` to `do_not_use/IMG_7567.png`.

Add a short `do_not_use/README.md` explaining that these source/reference files are preserved but not loaded by the current website. Keep active runtime files in place, especially `1587.gif`, `1885.gif`, all optimized gallery assets, logos, CSS, JS, and all 12 HTML locale pages. Do not move `.playwright-mcp/`, `.superpowers/`, or any other untracked/tool-generated files.

Update source comments that name `REF/` or `Behind The Production 2025/` so they point to the archived locations.

Add `.dockerignore` rules for Git data, `do_not_use/`, tests, docs, agent/browser artifacts, and other development-only files. The Dockerfile should copy only the explicit runtime files and directories needed by the site.

## Documentation and operation

Update `README.md` with:

- Requirements for Docker Engine and the Compose plugin.
- A local command that builds/runs the local override and opens `http://localhost:8080`.
- How to set `IMAGE_TAG` and `WEB_PORT` without requiring either variable.
- The Dokploy setup flow: deploy the Git repository in Compose mode using `compose.yaml`, configure the `web` container port as 80, attach `www.realbkk.com` and the apex domain, enable TLS, and optionally set `IMAGE_TAG`.
- A clear distinction between the locally tagged Compose image and publishing an image to a registry, which is not part of this design.

## Security and operational boundaries

- No application secrets, certificate files, or host-published production ports.
- No extra services, database, external registry, build workflow, or runtime mounts.
- Do not delete files; use tracked moves into `do_not_use/`.
- Preserve canonical URLs, sitemap/robots files, the three locale routes, and existing configurator/simulator behavior.
- Keep Dokploy's generated routing labels/configuration in Dokploy unless manual routing is specifically needed; do not check in environment-specific hostnames or generated labels by default.

## Validation and acceptance criteria

1. `docker compose -f compose.yaml config` succeeds with defaults and with an alternate `IMAGE_TAG`.
2. The local Compose overlay maps to loopback only; production Compose exposes internal port 80 without publishing it to the host.
3. The Docker image builds, reports healthy, and serves the English, Thai, and Japanese homepage and tool routes.
4. The 12 existing locale/SEO discoverability tests still pass; sitemap, robots, canonical metadata, and internal assets remain available in the image.
5. Unknown paths return 404 rather than the homepage.
6. Every archived file exists under `do_not_use/` after the move and retains its content; active files used by the app remain in their current paths, and source comments identify the new archive paths.
7. The README gives working local and Dokploy instructions, clearly explaining that Dokploy provides TLS and that `IMAGE_TAG` is not a registry-publish workflow.

## Primary deployment references

- [Dokploy Docker Compose domains](https://docs.dokploy.com/docs/core/docker-compose/domains) — Compose Domains UI, internal container port, TLS, and the recommendation to use `expose` rather than host port publication.
- [Dokploy Docker Compose example](https://docs.dokploy.com/docs/core/docker-compose/example) — deploying a Git-backed Compose project that builds a Dockerfile.
- [Dokploy Docker Compose overview](https://docs.dokploy.com/docs/core/docker-compose) — standard Compose versus Stack mode and Compose environment interpolation behavior.
- [Docker Compose variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/) — `${IMAGE_TAG:-latest}` defaults.
